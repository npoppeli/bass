# -*- coding: utf-8 -*-
"""
bass.site
-----
Objects and functions related to site structure.
"""

import fnmatch, logging, os, sys, yaml
from . import setting
from .common import write_file
from .config import config_default, read_config
from .convert import converter
from .render import read_templates
from .tree import Folder, Page, Asset

def create_project():
    logging.info('creating project')
    if len(os.listdir()) == 0:
        write_file(yaml.dump(config_default, default_flow_style=False), 'config')
        os.mkdir('input'); os.mkdir('output'); os.mkdir('template')
    else:
        logging.warn('current directory not empty')
        sys.exit()

def ignore_entry(name):
    return any([fnmatch.fnmatch(name, pattern) for pattern in setting.ignore]) or os.path.islink(name)

def build_site():
    logging.info('building site')
    read_config()
    read_templates()
    root = build_tree()
    # root.transform()
    # root.render()
    setting.root = root

def build_tree():
    logging.info('ignoring files/directories: %s', ' '.join(setting.ignore))
    logging.info('valid page extensions: %s', ' '.join(setting.pagetypes))
    return create_folder('', '', None)

def create_folder(name, path, parent):
    folder = Folder(name, path, parent)
    if parent is None:
        folder_path = setting.input
    else:
        folder_path = path # os.path.join(setting.input, path)
    for name in os.listdir(folder_path):
        path = os.path.join(folder_path, name)
        if ignore_entry(path):
            logging.debug('ignore %s', path)
        elif os.path.isfile(path):
            extension = os.path.splitext(name)[1]
            if extension in setting.pagetypes:
                logging.debug('create page %s path=%s', name, path)
                this = Page(name, path, folder)
            else:
                logging.debug('create asset %s path=%s', name, path)
                this = Asset(name, path, folder)
            folder.add(this)
        elif os.path.isdir(path):
            logging.debug('create folder %s path=%s', name, path)
            this = create_folder(name, path, folder)
            folder.add(this)
        else:
            logging.debug('ignore %s', path)
    return folder
