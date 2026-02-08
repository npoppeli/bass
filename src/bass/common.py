"""
bass.common
-----
Basic objects and functions shared by other modules.

Logging
-------
Logging levels are DEBUG, INFO, WARNING, ERROR, CRITICAL.
Bass uses logging level INFO by default, and DEBUG if called with --debug.

Basic (no webob, no waitress):
Create new logger object 'bass'.

Webob available:
Create new logger object 'bass'.

Webob and Waitress available:
Use the logger object of Waitress, called 'waitress'.
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

def read_file(path: str) -> str:
    """Read entire file, return content as one string.
    
    Arguments:
        path (str): path to file to read

    Returns:
        text (str): content of file
    """
    with open(path, 'r') as f:
        try:
            text = ''.join(f.readlines())
        except UnicodeError:
            text = ''
            logger.debug(f'Unicode error in file {path}')
    return text

def write_file(text: str, path: str) -> None:
    """Write text to file.
    
    Arguments:
        text (str): content of file to be written
        path (str): path to file to write
    """
    with open(path, 'w') as f:
        f.write(text)

def read_yaml_file(path: str) -> dict:
    """Read file, return YAML content as dictionary.
    
        Arguments:
        path (str): path to file to read

    Returns:
        text (dict): content of file
    """
    with open(path, 'r') as f:
        result = load(f, Loader=Loader)
    return result

def read_yaml_string(string: str) -> dict: 
    """Read string, return YAML content as dictionary.

    Arguments:
        string (str): string in YAML format

    Returns:
        text (dict): content of string
    """
    result = load(string, Loader=Loader)
    return result
