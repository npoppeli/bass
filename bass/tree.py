# -*- coding: utf-8 -*-
"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import logging, shutil
from datetime import datetime, date
from os import mkdir
from os.path import join, splitext, getctime, basename
from . import setting
from .common import read_file, read_yaml_string, write_file

# node classes
class Node:
    def __init__(self, name, path, parent=None):
        self.key = ''
        self.id = ''
        self.path = path
        self.name = name
        self.parent = parent
        self.child = []
    def transform(self):
        pass
    def render(self):
        pass
    def apply(self, hooks):
        if self.path in hooks:
            hooks[self.path](self)
        elif '#'+self.id in hooks:
            hooks['#'+self.id](self)
    def root(self): # follow parent chain until you get None
        this = self
        while this.parent is not None:
            this = this.parent
        return this

class Folder(Node):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        self.key = 'Folder'
    def add(self, node):
        self.child.append(node)
    def folder(self, name):
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Folder']
        return matches[0] if matches else None
    def folders(self):
        return [child for child in self.child if child.key == 'Folder']
    def pages(self):
        return [child for child in self.child if child.key == 'Page']
    def assets(self):
        return [child.name for child in self.child if child.key == 'Asset']
    def page(self, name):
        matches = [child for child in self.child
                   if child.name == name and child.key == 'Page']
        return matches[0] if matches else None
    def render(self):
        logging.debug('Folder.render: name=%s path=%s', self.name, self.path)
        self.apply(setting.pre_hook)
        if self.name == '': # root directory should already exist
            pass
        else: # create sub-directory 'self.path' in output directory
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
        pagetype = splitext(path)[1]
        convert = setting.converter[pagetype]
        self.preview = convert(preview) if preview else ''
        self.content = convert(content)
        self.meta = complete_meta(meta, full_path)
        # add metadata as node attributes
        for key, value in self.meta.items():
            setattr(self, key, value)
        self.url = '/' + splitext(self.path)[0] + '.html'
    def render(self):
        logging.debug('Page.render: name=%s path=%s', self.name, self.path)
        self.apply(setting.pre_hook)
        template = setting.template[self.skin]
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
        logging.debug('Asset.render: name=%s path=%s', self.name, self.path)
        self.apply(setting.pre_hook)
        shutil.copy(join(setting.input, self.path), join(setting.output, self.path))
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
        meta['title'] = splitext(basename(meta['path']))[0]
    # author: cannot be derived from anything else
    # tags
    if 'tags' in meta:
        if isinstance(meta['tags'], list):
            pass # OK
        elif isinstance(meta['tags'], str):
            meta['tags'] = [tag.strip() for tag in meta['tags'].split(',')]
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
    date_part = meta['date'] if 'date' in meta else None
    time_part = meta['time'] if 'time' in meta else None
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
    if date_part is not None and time_part is not None:
        meta['datetime'] = datetime(date_part.year, date_part.month,
                date_part.day, time_part.hour, time_part.minute,
                time_part.second, time_part.microsecond, time_part.tzinfo)
    elif date_part is not None:
        meta['datetime'] = datetime(date_part.year, date_part.month, date_part.day)
    else:
        meta['datetime'] = ctime
