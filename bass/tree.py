# -*- coding: utf-8 -*-
"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import logging, shutil, sys
from datetime import datetime, date
from copy import copy
from os import mkdir
from os.path import join, splitext, getctime, basename
from . import setting
from .common import read_file, read_yaml_string, write_file

# node classes
class Node:
    """Node is the base class for Folder, Page and Asset
       Instance variables:
           - key: type of node
           - id: identifier of node (preferably unique within tree)
           - name: name of node (last part of path)
           - path: path of node
           - parent: parent node
           - child: list of child nodes

       Instance methods:
           - render: abstract method
           - apply: apply hook to node
           - root: find root of tree
    """
    def __init__(self, name, path, parent=None):
        """construct Node with given name, path and parent"""
        self.key = ''
        self.id = ''
        self.name = name
        self.path = path
        self.parent = parent
        self.child = []
        self.tags = []
    def render(self):
        pass
    def add(self, node):
        self.child.append(node)
    def apply(self, hooks):
        if self.path in hooks:
            hooks[self.path](self)
        elif self.id and '#'+self.id in hooks:
            hooks['#'+self.id](self)
        else:
            for tag in [tag for tag in self.tags and '$'+tag in hooks]:
                hooks['$'+tag](self)
    def root(self): # follow parent chain until you get None
        this = self
        while this.parent is not None:
            this = this.parent
        return this

class Folder(Node):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        self.key = 'Folder'
    def asset(self, name):
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Asset']
        return matches[0] if matches else None
    def assets(self):
        return [child.name for child in self.child if child.key == 'Asset']
    def folder(self, name):
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Folder']
        return matches[0] if matches else None
    def folders(self):
        return [child for child in self.child if child.key == 'Folder']
    def page(self, name):
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Page']
        return matches[0] if matches else None
    def pages(self):
        return [child for child in self.child if child.key == 'Page']
    def render(self):
        # logging.debug('Folder.render: name=%s path=%s', self.name, self.path)
        self.apply(setting.pre_hook)
        if self.name != '': # root directory should already exist
            # create sub-directory 'self.path' in output directory
            mkdir(join(setting.output, self.path))
        for node in self.child:
            node.render()
        self.apply(setting.post_hook)

class Page(Node):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        self.key = 'Page'
        full_path = join(setting.input, parent.path, name)
        (meta, preview, content) = read_page(full_path)
        (pagename, pagetype) = splitext(path)
        convert = setting.converter[pagetype]
        self.preview = convert(preview) if preview else ''
        self.content = convert(content)
        self.meta = complete_meta(meta, full_path)
        # add metadata as node attributes
        for key, value in self.meta.items():
            setattr(self, key, value)
        self.url = '/' + pagename + '.html'
    def copy(self, sep='_'):
        """create of copy of page node, but with its own name, path and URL, and empty children list"""
        newpage = copy(self)
        newpage.child = []
        (pagename, pagetype) = splitext(newpage.path)
        newpage.name += sep
        newpage.path = pagename + sep + pagetype
        newpage.url = '/' + pagename + sep + '.html'
        return newpage

    def render(self):
        # logging.debug('Page.render: name=%s path=%s', self.name, self.path)
        self.apply(setting.pre_hook)
        if self.skin in setting.template:
            template = setting.template[self.skin]
        else:
            logging.critical("Template '%s' for page %s not available.", self.skin, self.path)
            sys.exit()
        write_file(template.render(this=self), join(setting.output, self.url[1:]))
        for node in self.child: # sub-pages (dynamically created)
            node.render()
        self.apply(setting.post_hook)

class Asset(Node):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        self.key = 'Asset'
        self.url = '/' + self.path
    def render(self):
        # logging.debug('Asset.render: name=%s path=%s', self.name, self.path)
        self.apply(setting.pre_hook)
        shutil.copy(join(setting.input, self.path), join(setting.output, self.path))
        # if an Asset node has children, what is the meaning?
        # for node in self.child: node.render()
        self.apply(setting.post_hook)

# read page, return triple (meta, preview, content)
def read_page(path):
    text = read_file(path)
    parts = text.split('\n---\n')
    if len(parts) == 1: # no metadata, just content
        return {}, '', parts[0]
    elif len(parts) == 2: # metadata, content
        meta = read_yaml_string(parts[0])
        return meta, '', parts[1]
    else: # len(parts) > 2 -> metadata, preview, content
        meta = read_yaml_string(parts[0])
        return meta, parts[1], '\n'.join(parts[1:])

def complete_meta(meta, path):
    # title: if missing, create one from path
    if 'title' not in meta:
        title = splitext(basename(path))[0]
        meta['title'] = title.replace('-', ' ').replace('_', ' ').capitalize()
    # author: cannot be derived from anything else
    # tags
    if 'tags' in meta:
        if isinstance(meta['tags'], list):
            pass # OK
        elif isinstance(meta['tags'], str):
            meta['tags'] = [tag.strip() for tag in meta['tags'].split()]
    else:
        meta['tags'] = []
    # skin
    if 'skin' not in meta:
        meta['skin'] = 'default'
    # id
    if 'id' not in meta:
        meta['id'] = ''
    # date, time, datetime
    fix_date_time(meta, datetime.fromtimestamp(getctime(path)))
    return meta

def fix_date_time(meta, ctime):
    date_part = meta.get('date')
    time_part = meta.get('time')
    if 'datetime' in meta:
        if date_part is None:
            if isinstance(meta['datetime'], datetime):
                date_part = meta['datetime'].date()
            elif isinstance(meta['datetime'], date):
                date_part = meta['datetime']
        if time_part is None and isinstance(meta['datetime'], datetime):
            time_part = meta['datetime'].time()
    meta['date'] = date_part
    meta['time'] = time_part
    # date & time from datetime override date & time from metadata
    if date_part is not None and time_part is not None:
        meta['datetime'] = datetime(date_part.year, date_part.month,
                date_part.day, time_part.hour, time_part.minute,
                time_part.second, time_part.microsecond, time_part.tzinfo)
    elif date_part is not None:
        meta['datetime'] = datetime(date_part.year, date_part.month, date_part.day)
    else:
        meta['datetime'] = ctime
        meta['date']     = ctime.date()
        meta['time']     = ctime.time()

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
    logging.debug('TOC main page name=%s path=%s', page.name, page.path)
    logging.debug('TOC has %d parts', len(parts))
    if len(parts) > 0:
        page.toc = '\n'.join(parts[0])
    else:
        page.toc = ''
    if len(parts) > 1:
        for p, part in enumerate(parts[1:]):
            current = page.copy(sep+str(p+1))
            logging.debug('subpage name=%s path=%s', current.name, current.path)
            current.toc = '\n'.join(part)
            page.add(current)
            previous.next = current
            current.prev = previous
            previous = current
        previous.next = None # last subpage
