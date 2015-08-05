# -*- coding: utf-8 -*-
"""
bass.site
-----
Objects and functions related to site structure and site generation.
"""

import fnmatch, imp, logging, os, shutil,sys, yaml
from . import setting
from .common import write_file
from .config import config_default, read_config
from .convert import converter
from .render import read_templates
from .tree import Folder, Page, Asset
from os import listdir, mkdir, unlink
from os.path import isdir, isfile, islink, join, relpath, splitext

def create_project():
    """create new project directory, with default configuration"""
    logging.info('Creating project')
    if len(listdir()) == 0:
        write_file(yaml.dump(config_default, default_flow_style=False), 'config')
        mkdir('input'); mkdir('output'); mkdir('template')
    else:
        logging.warn('Current directory not empty.')
        sys.exit()

def build_site():
    """build site in current project directory"""
    read_config()
    verify_project()
    read_templates()
    read_hooks()
    logging.info('Building site tree')
    root = build_tree()
    prepare_output()
    logging.info('Rendering site tree')
    root.render()

def check_hooks(hooks):
    """select all hooks that are callable"""
    return {key:value for key, value in hooks.items() if callable(value)}

def read_hooks():
    """read hooks from directory specified in configuration file"""
    if isdir(setting.hooks):
        (fileobj, path, details) = imp.find_module('__init__', [setting.hooks])
        module = imp.load_module('hooks', fileobj, path, details)
        setting.pre_hook  = check_hooks(getattr(module, 'pre', {}))
        setting.post_hook = check_hooks(getattr(module, 'post', {}))
    else:
        setting.pre_hook  = {}
        setting.post_hook = {}

def verify_project():
    """verify existence of directories specified in configuration"""
    if not ( isdir(setting.input) and isdir(setting.output) and isdir(setting.layout) ):
        logging.critical("Directories missing in project.")
        sys.exit(1)

def prepare_output():
    """clean output directory before rendering site tree"""
    for name in [n for n in listdir(setting.output) if n[0] != '.']:
        path = join(setting.output, name)
        if isfile(path):
            unlink(path)
        else:
            shutil.rmtree(path)

def build_tree():
    """generate site tree from files and directories in input directory"""
    root = None
    if '//' in setting.pre_hook:
        setting.pre_hook['//'](root)
    logging.info('Ignoring files/directories: %s', ' '.join(setting.ignore))
    logging.info('Valid page extensions: %s', ' '.join(setting.converter.keys()))
    root = create_folder('', '', None)
    if '//' in setting.post_hook:
        setting.post_hook['//'](root)
    return root

def ignore_entry(name):
    """True if 'name' is symbolic link or if 'name' matches one of the ignore patterns"""
    return any([fnmatch.fnmatch(name, pattern) for pattern in setting.ignore]) or islink(name)

def create_folder(name, path, parent):
    folder = Folder(name, path, parent)
    pagetypes = list(setting.converter.keys())
    if parent is None:
        folder_path = setting.input
    else:
        folder_path = join(setting.input, path)
    for name in os.listdir(folder_path):
        path = join(folder_path, name)
        rel_path = relpath(path, setting.input)
        if ignore_entry(path):
            logging.debug('Ignore %s', rel_path)
        elif isfile(path):
            extension = splitext(name)[1]
            this = (Page if extension in pagetypes else Asset)(name, rel_path, folder)
            folder.add(this)
        elif isdir(path):
            this = create_folder(name, rel_path, folder)
            folder.add(this)
        else:
            logging.debug('Ignore %s', rel_path)
    return folder
