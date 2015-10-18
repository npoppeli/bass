"""
bass.common
-----
Basic objects and functions shared by other modules.

Logging
-------
Logging levels are DEBUG, INFO, WARNING, ERROR, CRITICAL.
Bass uses logging level INFO by default, and DEBUG if called with --debug.

Basic (no webob, no waitress):

Webob available:

Webob and Waitress available:
Waitress uses a logger object named 'waitress', and sets the logging level to WARNING.
"""

import logging
# configure logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
try:
    import waitress
    logger = logging.getLogger('waitress')
except ImportError:
    logger = logging.getLogger('bass')

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
