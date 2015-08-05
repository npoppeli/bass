# -*- coding: utf-8 -*-
"""
bass.common
-----
Objects and functions shared by other modules.
"""

import logging, yaml, sys
from . import setting

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

def partition(lst, size):
    """divide list in list of sub-lists of length <= size"""
    return [lst[offset:offset+size] for offset in range(0, len(lst), size)]

def add_toc(page, nodelist, skin, sep='_', size=10):
    """add a table of contents to the specified node, apply pagination if necessary.

    Parameters:
        - page (Node): node to which table of contents is added
        - nodelist ([Node]): nodes to include in table of contents
        - skin (str|callable):
            - string: name of template to render one node in nodelist
            - callable: callable to render one node in nodelist
    Return value: None
    """
    # determine method for converting node to HTML fragment
    if callable(skin):
        func = skin
    elif isinstance(skin, str):
        func = setting.template[skin].render
    else:
        logging.critical("Bad parameter 'skin' in function 'add_toc'")
        sys.exit(1)
    # one HTML fragment per node, then partitioned in chunks of 'size'
    parts = partition([func(this=node) for node in nodelist], size)
    page.prev, page.next = None, None
    previous = page
    if len(parts) > 0:
        page.toc = '\n'.join(parts[0])
    else:
        page.toc = ''
    if len(parts) > 1:
        for p, part in enumerate(parts[1:]):
            current = page.copy()
            current.name += sep + str(p+1)
            current.toc = '\n'.join(part)
            page.child.append(current)
            previous.next = current
            current.prev = previous
            previous = current
        previous.next = None # last subpage
