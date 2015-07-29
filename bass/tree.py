# -*- coding: utf-8 -*-
"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import logging, os, shutil
from datetime import datetime, date
from . import setting
from .common import read_file, read_yaml_string, write_file

# node classes
class Node:
    def __init__(self, name, path, parent=None):
        self.key = ''
        self.path = path
        self.name = name
        self.parent = parent
        self.child = []
    def transform(self):
        pass
    def render(self):
        pass
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
        if self.name == '': # root directory should already exist
            pass
        else: # create sub-directory 'name' in directory 'parent'
            dir_path = os.path.join(setting.output, self.path)
            os.mkdir(dir_path)
        for node in self.child:
            node.render()

class Page(Node):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        logging.debug('Page.init: name=%s path=%s', self.name, self.path)
        self.key = 'Page'
        pagetype = os.path.splitext(path)[1]
        full_path = os.path.join(setting.input, parent.path, name)
        (meta, preview, content) = read_page(full_path)
        convert = setting.converter[pagetype]
        self.preview = convert(preview) if preview else ''
        self.content = convert(content)
        self.meta = complete_meta(meta, full_path)
        # add metadata as node attributes
        for key, value in self.meta.items():
            setattr(self, key, value)
        logging.debug('Page.init: meta=%s', str(self.meta))
        logging.debug('Page.init: name=%s path=%s', self.name, self.path)
    def render(self):
        logging.debug('Page.render: name=%s path=%s', self.name, self.path)
        html_file = os.path.splitext(self.path)[0] + '.html'
        logging.debug('html file before join %s', html_file)
        template = setting.template[self.type]
        logging.debug('create %s', os.path.join(setting.output, html_file))
        write_file(template.render(this=self), os.path.join(setting.output, html_file))

class Asset(Node):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        self.key = 'Asset'
    def render(self):
        shutil.copy(os.path.join(setting.input, self.path), os.path.join(setting.output, self.path))

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
        meta['title'] = os.path.splitext(os.path.basename(meta['path']))[0]
    # author: cannot be derived from anything else
    # tags
    if 'tags' in meta:
        if isinstance(meta['tags'], list):
            pass # OK
        elif isinstance(meta['tags'], str):
            meta['tags'] = [tag.strip() for tag in meta['tags'].split(',')]
    else:
        meta['tags'] = []
    # type
    if 'type' not in meta:
        meta['type'] = 'default'
    # date, time, datetime
    fix_date_time(meta, path)
    return meta

def fix_date_time(meta, path):
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
        meta['datetime'] = datetime.fromtimestamp(os.path.getctime(path))
