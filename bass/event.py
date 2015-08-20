# -*- coding: utf-8 -*-
"""
bass.event
-----
Objects and functions related to events and event handlers.
"""

import logging, sys
from datetime import datetime, date
from os.path import join, splitext, getctime, basename
from . import setting
from .convert import converter

event_handler = {}

def handle_event(label, handler):
    if callable(handler):
        if label in event_handler:
            logging.debug('Event handler for %s redefined', label)
        else:
            logging.debug('New event handler for %s', label)
        event_handler[label] = handler
    else:
        logging.debug('Event handler for %s is not a callable', label)

def event(label, node):
    if label in event_handler:
        event_handler[label](node)

class Processor:
    def __init__(self, converter=None):
        """construct page processor for given markup converter"""
        self.convert = converter

    def __call__(self, node):
        """convert node.content, node.preview; use elements of node.meta as attributes of node"""
        if self.convert:
            # convert node.content and node.preview
            node.preview = self.convert(node.preview) if node.preview else ''
            node.content = self.convert(node.content)
        # process metadata
        full_path = join(setting.input, node.path)
        node.meta = complete_meta(node.meta, full_path)
        # add metadata as node attributes
        for key, value in node.meta.items():
            setattr(node, key, value)
        pagename = splitext(node.path)[0]
        node.url = '/' + pagename + '.html'

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

if setting.markdown:
    markdown_processor = Processor(converter['.mkd'])
    handle_event('generate:post:page:extension:md', markdown_processor)
    handle_event('generate:post:page:extension:mkd', markdown_processor)

if setting.rest:
    rest_processor = Processor(converter['.rst'])
    handle_event('generate:post:page:extension:rst', rest_processor)

if setting.textile:
    textile_processor = Processor(converter['.txi'])
    handle_event('generate:post:page:extension:txi', textile_processor)

html_processor = Processor(converter['.html'])
handle_event('generate:post:page:extension:html', html_processor)

text_processor = Processor(converter['.txt'])
handle_event('generate:post:page:extension:txt', text_processor)