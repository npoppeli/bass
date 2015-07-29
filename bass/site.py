# -*- coding: utf-8 -*-
"""
bass.site
-----
Objects and functions related to site structure.
"""

import fnmatch, logging, os, shutil,sys, yaml
from . import setting
from .common import write_file
from .config import config_default, read_config
from .convert import converter
from .render import read_templates
from .tree import Folder, Page, Asset
from os.path import isdir

def create_project():
    """create_project: create new project directory, with default configuration"""
    logging.info('creating project')
    if len(os.listdir()) == 0:
        write_file(yaml.dump(config_default, default_flow_style=False), 'config')
        os.mkdir('input'); os.mkdir('output'); os.mkdir('template')
    else:
        logging.warn('current directory not empty')
        sys.exit()

def build_site():
    read_config()
    verify_project()
    read_templates()
    logging.info('building site')
    root = build_tree()
    # root.transform()
    prepare_output()
    root.render()
    setting.root = root

def verify_project():
    """verify_project: # verify existence of directories specified in configuration"""
    if not ( isdir(setting.input) and isdir(setting.output) and isdir(setting.templates) ):
        logging.critical("Directories missing in project. Exit, stage left.")
        sys.exit(1)

def prepare_output():
    """prepare_output: clean output directory before rendering site tree"""
    for name in os.listdir(setting.output):
        if name[0] == ".":
            continue
        path = os.path.join(setting.output, name)
        if os.path.isfile(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)

def build_tree():
    logging.info('ignoring files/directories: %s', ' '.join(setting.ignore))
    logging.info('valid page extensions: %s', ' '.join(setting.pagetypes))
    return create_folder('', '', None)

def ignore_entry(name):
    """ignore_entry: True if symbolic link or if filename matches one of the ignore patterns"""
    return any([fnmatch.fnmatch(name, pattern) for pattern in setting.ignore]) or os.path.islink(name)

def create_folder(name, path, parent):
    folder = Folder(name, path, parent)
    if parent is None:
        folder_path = setting.input
    else:
        folder_path = os.path.join(setting.input, path)
    for name in os.listdir(folder_path):
        path = os.path.join(folder_path, name)
        rel_path = os.path.relpath(path, setting.input)
        if ignore_entry(path):
            logging.debug('ignore %s', rel_path)
        elif os.path.isfile(path):
            extension = os.path.splitext(name)[1]
            if extension in setting.pagetypes:
                # logging.debug('create page %s path=%s', name, rel_path)
                this = Page(name, rel_path, folder)
            else:
                # logging.debug('create asset %s path=%s', name, rel_path)
                this = Asset(name, rel_path, folder)
            folder.add(this)
        elif os.path.isdir(path):
            # logging.debug('create folder %s path=%s', name, rel_path)
            this = create_folder(name, rel_path, folder)
            folder.add(this)
        else:
            logging.debug('ignore %s', rel_path)
    return folder
