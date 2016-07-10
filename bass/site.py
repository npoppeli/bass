"""
bass.site
-----
Objects and functions related to site structure and site generation.
"""

import shutil, sys, yaml
from . import setting
from .common import write_file
from .config import config_default, read_config
from .event import event_handler
from .layout import read_templates
from .common import logger
from .tree import Folder, Page, Asset
from fnmatch import fnmatch
from importlib import import_module
from os import listdir, mkdir, unlink, walk
# TODO: Python >=3.5 offers scandir as replacement for listdir
from os.path import isdir, isfile, islink, join, relpath, splitext, split

def create_project():
    """create new project directory, with default configuration"""
    logger.info('Creating project')
    if len(listdir()) == 0:
        write_file(yaml.dump(config_default, default_flow_style=False), 'config')
        mkdir(config_default['input'])
        mkdir(config_default['output'])
        mkdir(config_default['layout'])
    else:
        logger.warning('Current directory not empty')
        sys.exit()

def build_site():
    """build site in project directory"""
    read_config()
    verify_project()
    read_extension()
    logger.info('Building site tree')
    root = generate_tree()
    prepare_output()
    read_templates()
    logger.info('Rendering site tree')
    root.render()

def rebuild_site():
    """rebuild site in project directory"""
    logger.info('Building modified site tree')
    root = generate_tree()
    prepare_output()
    read_templates()
    logger.info('Rendering modified site tree')
    root.render()

def verify_project():
    """verify existence of directories specified in configuration"""
    if not (isdir(setting.input) and isdir(setting.output) and isdir(setting.layout)):
        logger.critical("Directories missing in project")
        sys.exit(1)

def read_extension():
    """read extension(s) from package specified in configuration file"""
    if setting.extension and isdir(join(setting.project, setting.extension)):
        try:
            logger.debug("Adding project directory {} to Python path".format(setting.project))
            sys.path.insert(0, setting.project)
            logger.debug("Importing package {}".format(setting.extension))
            module = import_module(setting.extension)
        except ImportError:
            logger.debug("Extension directory {} is not a Python package".format(setting.extension))

def prepare_output():
    """clean output directory before rendering site tree"""
    logger.debug('Clean output directory %s', setting.output)
    for name in [n for n in listdir(setting.output) if n[0] != '.']:
        path = join(setting.output, name)
        if isfile(path):
            unlink(path)
        else:
            shutil.rmtree(path)

def ignore_entry(name_rel, dirname):
    """True if 'name_rel' matches one of the ignore patterns or
    if 'name_rel' refers to a symbolic link"""
    return any([fnmatch(name_rel, pattern) for pattern in setting.ignore]) or \
           (not setting.follow_links and islink(join(dirname, name_rel)))

def generate_tree():
    """generate site tree from files and directories in input directory"""
    logger.info('Ignore files/directories: %s', ' '.join(setting.ignore))
    logger.info('Follow symbolic links: %s', ('no','yes')[setting.follow_links])
    prefix = 'generate:post:page:extension:'
    pagetypes = [key.replace(prefix, '') for key in event_handler.keys() if key.startswith(prefix)]
    logger.info('Page types: %s', ' '.join(pagetypes))
    folder_queue = {}
    for dirpath, dirnames, filenames in walk(setting.input, topdown=False, followlinks=setting.follow_links):
        dirpath_rel = relpath(dirpath, setting.input)
        folder_name = split(dirpath_rel)[1]
        if dirpath_rel == '.':
            dirpath_rel, folder_name = '', ''
        if ignore_entry(dirpath_rel, setting.input):
            logger.debug("Ignore directory %s", dirpath_rel)
            continue
        folder = Folder(folder_name, dirpath_rel, None)
        for name in set(dirnames) & set(folder_queue.keys()):
            folder.add(folder_queue[name])
        for name in filenames: # pages and assets; become children of this folder
            filename_rel = name if dirpath_rel == '.' else join(dirpath_rel, name)
            if ignore_entry(filename_rel, setting.input):
                logger.debug("Ignore file %s", filename_rel)
                continue
            suffix = splitext(name)[1][1:]
            this = (Page if suffix in pagetypes else Asset)(name, filename_rel, None)
            folder.add(this)
            this.ready()
        folder.ready()
        folder_queue[folder_name] = folder
    # by definition: folder with name = '' is the root of the site tree
    return folder_queue['']
