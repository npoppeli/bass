# -*- coding: utf-8 -*-
"""
bass.common
-----
Objects and functions shared by other modules.
"""

import yaml
from bunch import Bunch
keep = Bunch()

def read_file(filename):
    with open(filename, 'rU') as f:
        text = ''.join(f.readlines())
    return text

def write_file(text, filename):
     with open(filename, 'w') as f:
         f.write(text)

def read_yaml_file(path):
    with open(path, 'r') as file:
        result = yaml.load(file, Loader=yaml.CLoader)
    return result

def read_yaml_string(string):
    result = yaml.load(string, Loader=yaml.CLoader)
    return result
