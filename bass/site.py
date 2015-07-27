# -*- coding: utf-8 -*-
"""
bass.site
-----
Objects and functions related to site structure.
"""

import fnmatch, logging, os, sys
from .common import keep, read_file, write_file
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
    return any([fnmatch.fnmatch(name, pattern) for pattern in keep.ignore]) or os.path.islink(name)

def build_site():
    logging.info('building site')
    read_config()
    keep.project = os.getcwd()
    keep.input = os.path.join(keep.project, keep.config['input'])
    keep.output = os.path.join(keep.project, keep.config['output'])
    read_templates()
    root = build_tree()
    root.transform()
    root.render()
    keep.root = root

def build_tree():
    logging.info('ignoring files/directories: %s', ' '.join(keep.ignore))
    logging.info('valid page extensions: %s', ' '.join(keep.pagetypes))
    return create_folder('', None)

def create_folder(path, parent):
    folder = Folder(path, parent)
    if parent is None:
        folder_path = keep.input
    else:
        folder_path = os.path.join(keep.input, path)
    for name in os.listdir(folder_path):
        path = os.path.join(folder_path, name)
        if ignore_entry(path):
            logging.debug('ignore %s', path)
        elif os.path.isfile(path):
            extension = os.path.splitext(name)[1]
            if extension in keep.pagetypes:
                logging.debug('create page %s path=%s', name, path)
                this = Page(path, folder)
            else:
                logging.debug('create asset %s path=%s', name, path)
                this = Asset(path, folder)
            folder.add(this)
        elif os.path.isdir(path):
            logging.debug('create folder %s path=%s', name, path)
            this = create_folder(path, folder)
            folder.add(this)
        else:
            logging.debug('ignore %s', path)
    return folder
