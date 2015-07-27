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
    read_templates()
    root = build_tree()
    root.transform()
    root.render()
    keep.root = root

def build_tree():
    logging.info('ignoring files/directories: %s', ' '.join(keep.ignore))
    if not keep.markdown: logging.warning('Markdown is not enabled')
    if not keep.restructuredtext: logging.warning('RestructuredText is not enabled')
    if not keep.textile: logging.warning('Textile is not enabled')
    logging.debug('conversion is enabled for the following extensions: %s', ' '.join(converter.keys()))
    keep.project = os.getcwd()
    input_dir = os.path.join(keep.project, keep.config['input'])
    return create_folder(input_dir, None)

def create_folder(folder_path, parent):
    folder = Folder(folder_path, parent)
    for name in os.listdir(folder_path):
        path = os.path.join(folder_path, name)
        if ignore_entry(path):
            logging.debug('ignore %s', path)
        elif os.path.isfile(path):
            extension = os.path.splitext(name)[1]
            if extension in keep.pagetypes:
                logging.debug('page %s', name)
                this = Page(path, folder)
            else:
                logging.debug('asset %s', name)
                this = Asset(path, folder)
            folder.add(this)
        elif os.path.isdir(path):
            logging.debug('folder %s', name)
            this = create_folder(path, folder)
            folder.add(this)
        else:
            logging.debug('ignore %s', path)
    return folder
