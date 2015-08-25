# -*- coding: utf-8 -*-
"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import logging, shutil, sys
from copy import copy
from os import mkdir
from os.path import join, splitext
from . import setting
from .common import read_file, read_yaml_string, write_file
from .event import event

# node classes
class Node:
    """Node is the base class for Folder, Page and Asset
       Instance variables:
           - key: type of node
           - id: identifier of node (usually unique within tree)
           - name: name of node (last part of path)
           - path: path of node
           - parent: parent node
           - child: list of child nodes

       Instance methods:
           - render: abstract method
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
        """abstract render method"""
        pass

    def add(self, node):
        """add child node"""
        self.child.append(node)

    def root(self): # follow parent chain until you get None
        """find root of tree in which this node lives"""
        this = self
        while this.parent is not None:
            this = this.parent
        return this


class Folder(Node):
    def __init__(self, name, path, parent):
        """create new Folder node"""
        super().__init__(name, path, parent)
        self.key = 'Folder'
        if name != '':
            event('generate:post:folder:path:'+path, self)

    def asset(self, name):
        """return asset node with given name in this folder"""
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Asset']
        return matches[0] if matches else None

    def assets(self):
        """return all asset nodes in this folder"""
        return [child.name for child in self.child if child.key == 'Asset']

    def folder(self, name):
        """return folder node with given name in this folder"""
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Folder']
        return matches[0] if matches else None

    def folders(self):
        """return all folder nodes in this folder"""
        return [child for child in self.child if child.key == 'Folder']

    def page(self, name):
        """return page node with given name in this folder"""
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Page']
        return matches[0] if matches else None

    def pages(self, tag=None, key='name'):
        """return page nodes with given tag in this folder"""
        if tag:
            result = [child for child in self.child if child.key == 'Page' and tag in child.tags]
        else:
            result = [child for child in self.child if child.key == 'Page']
        return sorted(result, key=lambda page: getattr(page, key))

    def render(self):
        """render folder"""
        event('render:pre:root' if self.name == '' else 'render:pre:folder:path:'+self.path, self)
        if self.name != '': # root -> output directory, which already exists
            # render = create sub-directory 'self.path' in output directory
            mkdir(join(setting.output, self.path))
        for node in self.child:
            node.render()
        event('render:post:root' if self.name == '' else 'render:post:folder:path:'+self.path, self)


class Page(Node):
    def __init__(self, name, path, parent):
        """create new Page node"""
        super().__init__(name, path, parent)
        self.key = 'Page'
        full_path = join(setting.input, parent.path, name)
        self.meta, self.preview, self.content = read_page(full_path)
        pagetype = splitext(path)[1][1:]
        event('generate:post:page:path:'+path, self)
        event('generate:post:page:extension:'+pagetype, self)

    def copy(self, sep='_'):
        """create copy of page node, with its own name, path and URL, and empty children list"""
        newpage = copy(self)
        newpage.child = []
        (pagename, pagetype) = splitext(newpage.path)
        newpage.name += sep
        newpage.path = pagename + sep + pagetype
        newpage.url = '/' + pagename + sep + '.html'
        return newpage

    def render(self):
        """render Page node"""
        event('render:pre:page:path:'+self.path, self)
        if self.id: event('render:pre:page:id:'+self.id, self)
        for tag in self.tags: event('render:pre:page:tag:'+tag, self)
        if self.skin in setting.template:
            template = setting.template[self.skin]
        else:
            logging.critical("Template '%s' for page %s not available.", self.skin, self.path)
            sys.exit(1)
        write_file(template.render(this=self, root=self.root()), join(setting.output, self.url[1:]))
        for node in self.child: # (dynamically created) sub-pages
            node.render()
        event('render:post:page:path:'+self.path, self)
        if self.id: event('render:post:page:id:'+self.id, self)
        for tag in self.tags: event('render:post:page:tag:'+tag, self)


class Asset(Node):
    def __init__(self, name, path, parent):
        """create new Asset node"""
        super().__init__(name, path, parent)
        self.key = 'Asset'
        self.url = '/' + self.path
        event('generate:post:asset:path:'+path, self)
    def render(self):
        """render Asset node"""
        event('render:pre:asset:path:'+self.path, self)
        shutil.copy(join(setting.input, self.path), join(setting.output, self.path))
        event('render:post:asset:path:'+self.path, self)

def read_page(path):
    """read page from file and return triple (meta, preview, content)"""
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
