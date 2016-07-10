"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import shutil, sys
from copy import copy
from os import makedirs
from os.path import join, splitext
from . import setting
from .common import read_file, read_yaml_string, write_file, logger
from .event import event

# node classes
class Node:
    """Node is the base class for Folder, Page and Asset
       Instance variables:
           - kind: type of node
           - id: identifier of node (usually unique within the tree)
           - name: name of node (last part of path)
           - path: path of node
           - parent: parent node
           - children: list of child nodes

       Instance methods:
           - render: abstract method
           - root: find root of tree
    """
    def __init__(self, name, path, parent=None):
        """construct Node with given name, path and parent"""
        self.kind = 'Node'
        self.id = ''
        self.name = name
        self.path = path
        self.parent = parent
        self.children = []
        self.tags = []

    def ready(self):
        """abstract ready method"""
        pass

    def render(self):
        """abstract render method"""
        pass

    def add(self, node):
        """add child node"""
        node.parent = self
        self.children.append(node)

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
        self.kind = 'Folder'

    def asset(self, name):
        """return asset node with given name in this folder"""
        matches = [child for child in self.children
                   if child.name == name and child.kind == 'Asset']
        return matches[0] if matches else None

    def assets(self):
        """return all asset nodes in this folder"""
        return [child.name for child in self.children if child.kind == 'Asset']

    def folder(self, name):
        """return folder node with given name in this folder"""
        matches = [child for child in self.children
                   if child.name == name and child.kind == 'Folder']
        return matches[0] if matches else None

    def folders(self):
        """return all folder nodes in this folder"""
        return [child for child in self.children if child.kind == 'Folder']

    def page(self, name):
        """return page node with given name in this folder"""
        matches = [child for child in self.children
                   if child.name == name and child.kind == 'Page']
        return matches[0] if matches else None

    def _pages(self, deep=False):
        result = [node for node in self.children if node.kind == 'Page']
        if deep:
            for f in self.folders():
                result.extend(f._pages(deep=True))
        return result

    def pages(self, tag=None, idref=None, deep=False, key='name'):
        """return page nodes with given tag in this folder"""
        result = self._pages(deep=deep)
        if tag:
            result = [node for node in result if tag in node.tags]
        elif idref:
            result = [node for node in result if idref == node.id]
        return sorted(result, key=lambda page: getattr(page, key))

    def ready(self):
        """folder is ready: send event(s)"""
        event('generate:post:root' if self.name == '' else 'generate:post:folder:path:'+self.path, self)

    def render(self):
        """render folder"""
        event('render:pre:root' if self.name == '' else 'render:pre:folder:path:'+self.path, self)
        if self.name != '': # root -> output directory, which already exists
            # render = create sub-directory 'self.path' in output directory
            dirpath = join(setting.output, setting.root_url[1:], self.path)
            logger.debug("Creating directory %s", dirpath)
            makedirs(dirpath)
        for node in self.children:
            node.render()
        event('render:post:root' if self.name == '' else 'render:post:folder:path:'+self.path, self)


class Page(Node):
    def __init__(self, name, path, parent):
        """create new Page node; set content, preview and meta attributes"""
        super().__init__(name, path, parent)
        self.kind = 'Page'
        # attributes 'skin' and 'url' are derived from metadata by the page processor
        self.skin = ''
        self.url = ''
        full_path = join(setting.input, path)
        self.meta, self.preview, self.content = read_page(full_path)

    def copy(self, sep='_'):
        """create copy of page node, with its own name, path and URL, and empty children list"""
        newpage = copy(self)
        newpage.children = []
        (page_name, suffix) = splitext(newpage.path)
        newpage.name += sep
        newpage.path = page_name + sep + suffix
        newpage.url = '{0}{1}{2}.html'.format(setting.root_url, page_name, sep)
        return newpage

    def ready(self):
        """page is ready: send event(s)"""
        suffix = splitext(self.path)[1][1:]
        event('generate:post:page:path:'+self.path, self)
        event('generate:post:page:extension:'+suffix, self)

    def render(self):
        """render Page node"""
        event('render:pre:page:any', self)
        event('render:pre:page:path:'+self.path, self)
        if self.id: event('render:pre:page:id:'+self.id, self)
        for tag in self.tags: event('render:pre:page:tag:'+tag, self)
        # 'skin' attribute should be set by page processor
        if self.skin in setting.template:
            template = setting.template[self.skin]
        else:
            logger.critical("Template '%s' for page %s not available.", self.skin, self.path)
            sys.exit(1)
        filepath = join(setting.output, self.url[1:])
        logger.debug("Writing page %s", filepath)
        write_file(template.render(this=self), filepath)
        for node in self.children: # (dynamically created) sub-pages
            node.render()
        event('render:post:page:any', self)
        event('render:post:page:path:'+self.path, self)
        if self.id: event('render:post:page:id:'+self.id, self)
        for tag in self.tags: event('render:post:page:tag:'+tag, self)


class Asset(Node):
    def __init__(self, name, path, parent):
        """create new Asset node"""
        super().__init__(name, path, parent)
        self.kind = 'Asset'
        self.url = setting.root_url + self.path

    def ready(self):
        """asset is ready: send event(s)"""
        suffix = splitext(self.path)[1][1:]
        event('generate:post:asset:path:'+self.path, self)
        event('generate:post:asset:extension:'+suffix, self)

    def render(self):
        """render Asset node"""
        suffix = splitext(self.path)[1][1:]
        event('render:pre:asset:path:'+self.path, self)
        event('render:pre:asset:extension:'+suffix, self)
        filepath = join(setting.output, setting.root_url[1:], self.path)
        logger.debug("Writing asset %s", filepath)
        shutil.copy(join(setting.input, self.path), filepath)
        event('render:post:asset:path:'+self.path, self)
        event('render:post:asset:extension:'+suffix, self)

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
