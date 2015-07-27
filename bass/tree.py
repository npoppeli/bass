# -*- coding: utf-8 -*-
"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import logging, os, yaml
from datetime import datetime, date, time
from .common import keep, read_file, read_yaml_string
from .convert import converter

# node classes
class Node:
    def __init__(self, parent=None):
        self.key = ''
        self.parent = parent
        self.child = []
    def transform(self):
        pass
    def render(self):
        pass
    def add(self, node):
        self.child.append(node)
    def root(self): # follow parent chain until you get None
        this = self
        while this.parent is not None:
            this = this.parent
        return this

class Folder(Node):
    def __init__(self, path, parent):
        super().__init__(parent)
        self.key = 'Folder'
        self.path = path

class Page(Node):
    def __init__(self, path, parent):
        super().__init__(parent)
        self.key = 'Page'
        self.path = path
        logging.debug('create page from %s', path)
        pagetype = os.path.splitext(path)[1]
        logging.debug('convert as %s', pagetype)
        (meta, preview, content) = read_page(path)
        convert = keep.converter[pagetype]
        self.preview = convert(preview) if preview else ''
        self.content = convert(content)
        self.meta = complete_meta(meta)

class Asset(Node):
    def __init__(self, path, parent):
        super().__init__(parent)
        self.key = 'Asset'
        self.path = path

# read page, return triple (meta, preview, content)
def read_page(path):
    text = read_file(path)
    parts = text.split('\n---\n')
    if len(parts) == 1: # no metadata, just content
        return {'path':path}, '', parts[0]
    elif len(parts) == 2: # metadata, content
        meta = read_yaml_string(parts[0])
        meta['path'] = path
        return meta, '', parts[1]
    else: # len(parts) > 2 -> metadata, preview, content
        meta = read_yaml_string(parts[0])
        meta['path'] = path
        return meta, parts[1], '\n'.join(parts[1:])

def complete_meta(meta):
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
    fix_date_time(meta)
    return meta

def fix_date_time(meta):
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
        meta['datetime'] = datetime.fromtimestamp(os.path.getctime(meta['path']))
