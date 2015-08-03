# -*- coding: utf-8 -*-
"""
bass.common
-----
Objects and functions shared by other modules.
"""

import yaml

def read_file(filename):
    with open(filename, 'rU') as f:
        text = ''.join(f.readlines())
    return text

def write_file(text, filename):
    with open(filename, 'w') as f:
        f.write(text)

def read_yaml_file(path):
    with open(path, 'r') as f:
        result = yaml.load(f, Loader=yaml.CLoader)
    return result

def read_yaml_string(string):
    result = yaml.load(string, Loader=yaml.CLoader)
    return result

def partition(lst, size):
    return [lst[offset:offset+size] for offset in range(0, len(lst), size)]

def add_toc(page, nodelist, skin, sep='_', size=10):
    """add_toc: add a table of contents of a list of nodes to the specified page,
    and apply pagination if necessary.
    - page: node to which table of contents is added
    - nodelist: nodes to include in table of contents
    - skin: string or callable
      - string: name of template to render one node in nodelist
      - callable: callable to render one node in nodelist."""
    # one HTML fragment per node, then partitioned in chunks of 'size'
    parts = partition([skin.render(this=node) for node in nodelist], size)
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
        # last subpage
        previous.next = None
