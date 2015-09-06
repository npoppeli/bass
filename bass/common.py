"""
bass.common
-----
Basic functions shared by other modules.
"""

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

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
        result = load(f, Loader=Loader)
    return result

def read_yaml_string(string):
    """read string, return YAML content as dictionary"""
    result = load(string, Loader=Loader)
    return result
