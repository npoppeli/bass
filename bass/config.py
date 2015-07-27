# -*- coding: utf-8 -*-
"""
bass.config
-----
Objects and functions related to configuration.
"""

import argparse, logging, os
from .common import keep, read_yaml_file

config_default = {
    'input':     'input',
    'output':    'output',
    'templates': 'templates',
    'ignore':    '.?*'
}

def read_config():
    config_file = 'config'
    config = config_default.copy()
    if os.path.exists(config_file) and os.path.isfile(config_file):
         config.update(read_yaml_file(config_file))
    keep.ignore = config['ignore'].split()
    if config_default['ignore'] not in keep.ignore:
        keep.ignore.append(config_default['ignore'])
    keep.config = config

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--build',  help='build',  action='store_true', default=False)
    parser.add_argument('-c', '--create', help='create', action='store_true', default=False)
    parser.add_argument('-d', '--debug',  help='debug', action='store_true', default=False)
    parser.add_argument('-s', '--server', help='server', action='store_true')
    return parser.parse_args()
