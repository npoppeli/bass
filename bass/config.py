# -*- coding: utf-8 -*-
"""
bass.config
-----
Objects and functions related to configuration.
"""

import argparse, os
from . import setting
from .common import read_yaml_file

config_default = {
    'input':     'input',
    'output':    'output',
    'templates': 'templates',
    'ignore':    '.?*'
}

def read_config():
    config_file = 'config' # assumption: cwd == project directory
    config = config_default.copy()
    if os.path.exists(config_file) and os.path.isfile(config_file):
         config.update(read_yaml_file(config_file))
    setting.ignore = config['ignore'].split()
    if config_default['ignore'] not in setting.ignore:
        setting.ignore.append(config_default['ignore'])
    setting.project   = os.getcwd()
    setting.input     = os.path.join(setting.project, config['input'])
    setting.output    = os.path.join(setting.project, config['output'])
    setting.templates = os.path.join(setting.project, config['templates'])

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--build',  help='build',  action='store_true', default=False)
    parser.add_argument('-c', '--create', help='create', action='store_true', default=False)
    parser.add_argument('-d', '--debug',  help='debug', action='store_true', default=False)
    parser.add_argument('-s', '--server', help='server', action='store_true')
    return parser.parse_args()