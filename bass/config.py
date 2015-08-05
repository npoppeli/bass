# -*- coding: utf-8 -*-
"""
bass.config
-----
Objects and functions related to configuration.
"""

import argparse
from os import getcwd
from os.path import exists, isfile, join
from . import setting
from .common import read_yaml_file

config_default = {
    'input':  'input',
    'output': 'output',
    'hooks':  'hooks',
    'layout': 'layout',
    'ignore': '.?*'
}

def read_config():
    """read configuration file, define global settings"""
    config_file = 'config' # assumption: cwd == project directory
    config = config_default.copy()
    if exists(config_file) and isfile(config_file):
        config.update(read_yaml_file(config_file))
    setting.ignore = config['ignore'].split()
    if config_default['ignore'] not in setting.ignore:
        setting.ignore.append(config_default['ignore'])
    setting.project = getcwd()
    setting.input   = join(setting.project, config['input'])
    setting.output  = join(setting.project, config['output'])
    setting.hooks   = join(setting.project, config['hooks'])
    setting.layout  = join(setting.project, config['layout'])

def parse_cmdline():
    """parse command line, return parsed argument list"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--build',  help='build',  action='store_true', default=False)
    parser.add_argument('-c', '--create', help='create', action='store_true', default=False)
    parser.add_argument('-d', '--debug',  help='debug', action='store_true', default=False)
    parser.add_argument('-s', '--server', help='server', action='store_true')
    return parser.parse_args()
