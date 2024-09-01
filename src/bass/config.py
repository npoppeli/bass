"""
bass.config
-----
Objects and functions related to configuration.
"""

import argparse, sys
from os import getcwd
from os.path import exists, isfile, join
from . import setting
from .common import read_yaml_file, logger

config_default = dict(follow_links=False, hard_links=False, ignore='.?*',
                      host='localhost', port=8080, root_url='/',
                      input='input', output='output', layout='layout')

def read_config():
    """Read configuration file, define global settings.
    Assumption: the current working directory is the project directory.
    """
    setting.project = getcwd()
    config_file = 'config'
    config = config_default.copy()
    if exists(config_file):
        if isfile(config_file):
            config.update(read_yaml_file(config_file))
        else:
            logger.critical("'config' is not a file")
            sys.exit(1)
    else:
        logger.critical("Current directory does not contain a 'config' file")
        sys.exit(1)
    setting.follow_links = config['follow_links']
    setting.hard_links   = config['hard_links']
    setting.ignore       = config['ignore'].split()
    setting.host         = config['host']
    setting.port         = config['port']
    setting.root_url     = config['root_url']
    if config_default['ignore'] not in setting.ignore:
        setting.ignore.append(config_default['ignore'])
    setting.input   = join(setting.project, config['input'])
    setting.layout  = join(setting.project, config['layout'])
    setting.output  = join(setting.project, config['output'])
    if 'extension' in config:
        setting.extension = config['extension']

def parse_cmdline():
    """Parse command line, and return parsed argument list.

    Returns:
        namespace: parsed argument list
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--build',   help='build',   action='store_true', default=False)
    parser.add_argument('-v', '--version', help='version', action='store_true', default=False)
    parser.add_argument('-c', '--create',  help='create',  action='store_true', default=False)
    parser.add_argument('-d', '--debug',   help='debug',   action='store_true', default=False)
    parser.add_argument('-s', '--server',  help='server',  action='store_true')
    return parser.parse_args()
