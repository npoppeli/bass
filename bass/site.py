# -*- coding: utf-8 -*-
"""
bass.site
-----
Objects and functions related to site structure.
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
    """create_project: create new project directory, with default configuration"""
    logging.info('creating project')
    if len(listdir()) == 0:
        write_file(yaml.dump(config_default, default_flow_style=False), 'config')
        mkdir('input'); mkdir('output'); mkdir('template')
    else:
        logging.warn('current directory not empty')
        sys.exit()

def build_site():
    read_config()
    verify_project()
    read_templates()
    read_hooks()
    logging.info('building site tree')
    root = build_tree()
    prepare_output()
    logging.info('rendering site tree')
    root.render()

def check_hooks(hooks):
    # TODO: remove entries with value not a callable; remove entry '#' (would match all nodes without explicit id attribute)
    return hooks
    
def read_hooks():
    if isdir(setting.hooks):
        (fileobj, path, details) = imp.find_module('__init__', [setting.hooks])
        module = imp.load_module('hooks', fileobj, path, details)
        setting.pre_hook  = check_hooks(getattr(module, 'pre', {}))
        setting.post_hook = check_hooks(getattr(module, 'post', {}))
    else:
        setting.pre_hook  = {}
        setting.post_hook = {}

def verify_project():
    """verify_project: # verify existence of directories specified in configuration"""
    if not ( isdir(setting.input) and isdir(setting.output) and isdir(setting.templates) ):
        logging.critical("Directories missing in project.")
        sys.exit(1)

def prepare_output():
    """prepare_output: clean output directory before rendering site tree"""
    for name in listdir(setting.output):
        if name[0] == ".":
            continue
        path = join(setting.output, name)
        if isfile(path):
            unlink(path)
        else:
            shutil.rmtree(path)

def build_tree():
    root = None
    if '//' in setting.pre_hook: setting.pre_hook['//'](root)
    logging.info('ignoring files/directories: %s', ' '.join(setting.ignore))
    pagetypes = list(setting.converter.keys())
    logging.info('valid page extensions: %s', ' '.join(pagetypes))
    root = create_folder('', '', None)
    if '//' in setting.post_hook: setting.post_hook['//'](root)
    return root

def ignore_entry(name):
    """ignore_entry: True if symbolic link or if filename matches one of the ignore patterns"""
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
            logging.debug('ignore %s', rel_path)
        elif isfile(path):
            extension = splitext(name)[1]
            if extension in pagetypes:
                this = Page(name, rel_path, folder)
            else:
                this = Asset(name, rel_path, folder)
            folder.add(this)
        elif isdir(path):
            this = create_folder(name, rel_path, folder)
            folder.add(this)
        else:
            logging.debug('ignore %s', rel_path)
    return folder
