# -*- coding: utf-8 -*-
"""
bass.common
-----
Objects and functions shared by other modules.
"""

import yaml

def read_file(filename):
    """read entire file, return content as one string"""
    with open(filename, 'rU') as f:
        text = ''.join(f.readlines())
    return text

def write_file(text, filename):
    """write text to file"""
    with open(filename, 'w') as f:
        f.write(text)

def read_yaml_file(path):
    """read file, return YAML content as dictionary"""
    with open(path, 'r') as f:
        result = yaml.load(f, Loader=yaml.CLoader)
    return result

def read_yaml_string(string):
    """read string, return YAML content as dictionary"""
    result = yaml.load(string, Loader=yaml.CLoader)
    return result
