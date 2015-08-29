# -*- coding: utf-8 -*-
"""
bass.site
-----
Objects and functions related to site structure and site generation.
"""

import imp, logging, shutil,sys, yaml
from . import setting
from .common import write_file
from .config import config_default, read_config
from .event import event, event_handler
from .layout import read_templates
from .tree import Folder, Page, Asset
from fnmatch import fnmatch
from os import listdir, mkdir, unlink
from os.path import isdir, isfile, islink, join, relpath, splitext

def create_project():
    """create new project directory, with default configuration"""
    logging.info('Creating project')
    if len(listdir()) == 0:
        write_file(yaml.dump(config_default, default_flow_style=False), 'config')
        for k, v in config_default.items():
            if k != 'ignore': mkdir(v)
    else:
        logging.warn('Current directory not empty')
        sys.exit()

def build_site():
    """build site in current project directory"""
    read_config()
    verify_project()
    read_handlers()
    logging.info('Building site tree')
    root = build_tree()
    prepare_output()
    read_templates()
    logging.info('Rendering site tree')
    root.render()

def rebuild_site():
    """rebuild site in current project directory"""
    logging.info('Building modified site tree')
    root = build_tree()
    prepare_output()
    read_templates()
    logging.info('Rendering modified site tree')
    root.render()

def verify_project():
    """verify existence of directories specified in configuration"""
    if not ( isdir(setting.input) and isdir(setting.output) and isdir(setting.layout) ):
        logging.critical("Directories missing in project")
        sys.exit(1)

def read_handlers():
    """read handlers from directory specified in configuration file"""
    if isdir(setting.handlers):
        (fileobj, path, details) = imp.find_module('__init__', [setting.handlers])
        module = imp.load_module('handlers', fileobj, path, details)

def prepare_output():
    """clean output directory before rendering site tree"""
    logging.debug('Clean output directory %s', setting.output)
    for name in [n for n in listdir(setting.output) if n[0] != '.']:
        path = join(setting.output, name)
        if isfile(path):
            unlink(path)
        else:
            shutil.rmtree(path)

def build_tree():
    """generate site tree from files and directories in input directory"""
    logging.info('Ignoring files/directories: %s', ' '.join(setting.ignore))
    prefix = 'generate:post:page:extension:'
    setting.pagetypes =  [key.replace(prefix, '') for key in event_handler.keys() if key.startswith(prefix)]
    logging.info('Valid page extensions: %s', ' '.join(setting.pagetypes))
    root = create_folder('', '', None)
    event('generate:post:root', root)
    return root

def ignore_entry(name):
    """True if 'name' is symbolic link or if 'name' matches one of the ignore patterns"""
    return any([fnmatch(name, pattern) for pattern in setting.ignore]) or islink(name)

def create_folder(name, path, parent):
    """create folder node in site tree"""
    folder = Folder(name, path, parent)
    if parent is None:
        folder_path = setting.input
    else:
        folder_path = join(setting.input, path)
    for name in listdir(folder_path):
        path = join(folder_path, name)
        rel_path = relpath(path, setting.input)
        if ignore_entry(path):
            logging.debug('Ignore %s', rel_path)
        elif isfile(path):
            suffix = splitext(name)[1][1:]
            this = (Page if suffix in setting.pagetypes else Asset)(name, rel_path, folder)
            folder.add(this)
        elif isdir(path):
            this = create_folder(name, rel_path, folder)
            folder.add(this)
        else:
            logging.debug('Ignore %s', rel_path)
    return folder
