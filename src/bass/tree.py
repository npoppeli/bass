"""
bass.tree
-----
Objects and functions related to the site tree.
"""

import shutil, sys
from typing import Callable
from copy import copy as shallow_copy
from datetime import datetime, date, time
from os.path import getctime, basename
from os import makedirs
from os.path import join, splitext
from xmlrpc.client import DateTime

from . import setting
from . import event as event_mod
from .common import read_file, read_yaml_string, write_file, logger

# available assets transformers
"""
copy: shutil.copy(src, dst)
hard link: os.link(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True)

More complicated examples:
- browserify vue/dist/vue.runtime.common.js > bundle.js
- browserify axios/index.js > bundle.js
- coffee -t -p index.coffee|cs > index.js
"""
transformer = {
    '*': shutil.copy
}

def add_transformer(extension: str, transform: Callable, overwrite: bool=False):
    """Add/set transformer for asset type (extension)."""
    if callable(transform):
        if extension in transformer:
            if overwrite:
                logger.debug(f'New transformer for {extension}')
                transformer[extension] = transform
            else:
                logger.debug(f'Attempt to redefine transformer for {extension}')
        else:
            logger.debug(f'New transformer for {extension}')
            transformer[extension] = transform
    else:
        logger.debug(f'Transformer for {extension} is not a callable')

"""Node classes are defined below, starting with the base class 'Node'."""
class Node:
    """Node is the base class for Folder, Page and Asset
       Instance variables:
           - kind:     type of node
           - id:       identifier of node (usually unique within the tree)
           - name:     name of node (last part of path)
           - path:     path of node
           - parent:   parent node
           - children: list of child nodes

       Instance methods:
           - render: abstract method
           - root: find root of tree
    """
    def __init__(self, name: str, path: str, parent=None):
        """Construct Node with given name, path and parent.

        Arguments:
            name (str):    name of node
            path (str):    filesystem path of node contents
            parent (Node): parent node (can be empty, i.e. None)
        """
        self.kind = 'Node'
        self.id = ''
        self.name = name
        self.path = path
        self.parent = parent
        self.children = []
        self.tags = []

    def __str__(self):
        return f"{self.kind} '{self.path}'"

    def ready(self):
        """abstract `ready` method"""
        pass

    def event(self, descr: str) -> None:
        """Call handler for event `descr`.

        Arguments:
            descr (str): description of event
        """
        if descr in event_mod.event_handler:
            try:
                event_mod.event_handler[descr](self)
            except Exception as e:
                logger.error(f'Error handling event {descr} on {self}:\n{e}')

    def render(self):
        """abstract `render` method"""
        pass

    def add(self, node):
        """add child node"""
        node.parent = self
        self.children.append(node)

    def root(self): # follow parent chain until you get 'None'
        """Find root of tree of which this node is a member.

        Returns:
            root node
        """
        this = self
        while this.parent is not None:
            this = this.parent
        return this

"""Folder node class"""
class Folder(Node):
    def __init__(self, name: str, path: str, parent: Node):
        """Create new Folder node with name `name` and filesystem path `path`."""
        super().__init__(name, path, parent)
        self.kind = 'Folder'

    def asset(self, name: str) -> Node | None:
        """Return asset node with given name in this folder.

        Arguments:
           name (str): name of asset

        Returns:
           Asset node with name `name`, or None
    """
        matches = [child for child in self.children
                   if child.name == name and child.kind == 'Asset']
        return matches[0] if matches else None

    def assets(self) -> list[Node]:
        """Return all asset nodes in this folder.

        Returns:
            list of Asset nodes
        """
        return [child.name for child in self.children if child.kind == 'Asset']

    def folder(self, name) -> Node | None:
        """Return folder node with name `name` within present folder.

        Returns:
           Folder node with name `name`, or None
        """
        matches = [child for child in self.children
                   if child.name == name and child.kind == 'Folder']
        return matches[0] if matches else None

    def folders(self) -> list[Node]:
        """Return all folder nodes within present folder.

        Returns:
            list of Folder nodes
        """
        return [child for child in self.children if child.kind == 'Folder']

    def page(self, name: str) -> Node | None:
        """Return page node with given name in this folder.

        Arguments:
            name (str): name of page

        Returns:
            Page node with name `name`, or None
        """
        matches = [child for child in self.children
                   if child.name == name and child.kind == 'Page']
        return matches[0] if matches else None

    def _pages(self, deep=False):
        result = [node for node in self.children if node.kind == 'Page']
        if deep:
            for f in self.folders():
                result.extend(f._pages(deep=True))
        return result

    def pages(self, tag=None, idref=None, deep=False, key='name') -> list[Node]:
        """Return page nodes with tag `tag` within present folder.

        Arguments:
            tag (str):   tag name
            idref (str): identifier of another node
            deep (bool): perform deep search
            key (str):   sort key (must be name of an attribute of Page nodes)

        Returns:
            list of Page nodes
        """
        result = self._pages(deep=deep)
        if tag:
            result = [node for node in result if tag in node.tags]
        elif idref:
            result = [node for node in result if idref == node.id]
        return sorted(result, key=lambda page: getattr(page, key))

    def ready(self):
        """Folder node is ready: send event(s)."""
        self.event('generate:post:root' if self.name == '' else
                   'generate:post:folder:path:' + self.path)

    def render(self):
        """Render folder node."""
        self.event('render:pre:root' if self.name == '' else
                   'render:pre:folder:path:' + self.path)
        if self.name != '': # root -> output directory, which already exists
            # rendering a folder means: create sub-directory 'self.path' in output directory
            dirpath = join(setting.output, setting.root_url[1:], self.path)
            logger.debug(f"Creating directory {dirpath}")
            makedirs(dirpath)
        for node in self.children:
            node.render()
        self.event('render:post:root' if self.name == '' else
                   'render:post:folder:path:'+self.path)


"""Page node class, and auxiliary functions."""
def read_page(path: str) -> tuple[dict, str, str]:
    """Read page from file and return triple (meta, preview, content).

    Arguments:
        path: filesystem path of Page node

    Returns:
        metadata dictionary, page preview, page content
    """
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

def complete_metadata(meta: dict, path: str) -> dict:
    """Complete the metadata dictionary for the node with given path.

        Arguments:
        meta (dict): dictionary of metadata
        path (str):  filesystem path for node in tree

        Returns:
            Dictionary of metadata, with added default values
    """
    # title: if this is missing, create one from path
    if 'title' not in meta:
        title = splitext(basename(path))[0]
        meta['title'] = title.replace('-', ' ').replace('_', ' ').capitalize()
    # author: cannot be derived from anything else
    # tags: can be an explicit list or a string that can be split as a whitespace-separated list
    if 'tags' in meta:
        if isinstance(meta['tags'], list):
            pass # OK
        elif isinstance(meta['tags'], str):
            meta['tags'] = [tag.strip() for tag in meta['tags'].split()]
    else:
        meta['tags'] = []
    # skin: template for this page
    if 'skin' not in meta:
        meta['skin'] = 'default'
    # id: identifier for this page
    if 'id' not in meta:
        meta['id'] = ''
    # date, time, datetime
    adjust_date_time(meta, datetime.fromtimestamp(getctime(path)))
    return meta

def adjust_date_time(meta: dict, ctime: datetime):
    """Adjust metadata fields `date`, `time` and `datetime`.
    If present in the YAML file, the metadata fields `date`, `time` and `datetime` should have the
    right data type.

    Arguments:
        meta: metadata dictionary
        ctime: ctime of a node
    """
    date_value, time_value, datetime_value = None, None, None
    if 'date' in meta:
        if isinstance(meta['date'], datetime):
            date_value = meta['date']
        else:
            logger.debug(f"Bad date value {date_value}, type {type(date_value)}")
    if 'time' in meta:
        if isinstance(meta['time'], time):
            time_value = meta['time']
        else:
            logger.debug(f"Bad time value {time_value}, type {type(time_value)}")
    if 'datetime' in meta:
        if isinstance(meta['datetime'], datetime):
            datetime_value = meta['datetime']
        else:
            logger.debug(f"Bad datetime value {datetime_value}, type {type(datetime_value)}")
    # We now distinguish 3 cases:
    # 1. if we have a valid datetime, we can set date and time based on datetime, if necessary
    # 2. we do not have a valid datetime, but we have a valid date or date+time
    # 3. we have neither a valid datetime nor a valid date
    if datetime_value: # case 1
        if date_value is None:
            date_value = datetime_value.date()
            meta['date'] = date_value
        if time_value is None:
            time_value = datetime_value.time()
            meta['time'] = time_value
    elif date_value: # case 2
        if time_value:
            meta['datetime'] = datetime(date_value.year, date_value.month,
                date_value.day, time_value.hour, time_value.minute,
                time_value.second, time_value.microsecond, time_value.tzinfo)
        else:
            meta['datetime'] = datetime(date_value.year, date_value.month, date_value.day)
    else: # case 3
        meta['datetime'] = ctime
        meta['date']     = ctime.date()
        meta['time']     = ctime.time()

class Page(Node):
    def __init__(self, name: str, path: str, parent: Node):
        """Create new Page node with name `name` and filesystem path `path`.

        Set node attributes `content`, `preview` and `meta`.
        Set attributes of node to elements of node.meta.

        Arguments:
            name (str): name of node
            path (str): filesystem path of node
            parent (Node): parent node
        """
        super().__init__(name, path, parent)
        # Most attributes are set in this method, but the 'url' is set by the page processor
        self.kind = 'Page'
        self.skin = ''
        self.url = ''
        full_path = join(setting.input, path)
        page_meta, self.preview, self.content = read_page(full_path)
        # process metadata
        self.meta = complete_metadata(page_meta, full_path)
        # add metadata properties as attributes of this node
        for key, value in self.meta.items():
            setattr(self, key, value)

    def copy(self, separator: str='_') -> Node:
        """Create copy of page node, with its own name, path and URL, and empty children list.

        Arguments:
            separator (str): separator for elements of path attributes

        Returns:
            new Page node
        """
        new_page = shallow_copy(self)
        new_page.children = []
        (page_name, suffix) = splitext(new_page.path)
        new_page.name += separator
        new_page.path = page_name + separator + suffix
        new_page.url = f'{setting.root_url}{page_name}{separator}.html'
        return new_page

    def ready(self):
        """Page node is ready: send event(s)."""
        suffix = splitext(self.path)[1][1:]
        self.event('generate:post:page:path:' + self.path)
        self.event('generate:post:page:extension:' + suffix)

    def render(self):
        """Render Page node."""
        self.event('render:pre:page:any')
        self.event('render:pre:page:name:' + self.name)
        if self.id:
            self.event('render:pre:page:id:' + self.id)
        for tag in self.tags:
            self.event('render:pre:page:tag:' + tag)
        # 'skin' attribute should have been set by page processor
        if self.skin == '':
            logger.critical(f"Empty template for page {self.path}")
            sys.exit(1)
        elif self.skin in setting.template:
            template = setting.template[self.skin]
        else:
            logger.critical(f"Undefined template '{self.skin}' for page {self.path}")
            sys.exit(1)
        filepath = join(setting.output, self.url[1:])
        # logger.debug(f"Page {self.path}: self.url={self.url}")
        try:
            write_file(template.render(this=self), filepath)
        except NameError as e:
            logger.error(f"Page {self.path}: error in template expression\n{e}")
        except AttributeError as e:
            logger.error(f"Page {self.path}: missing attribute in \n{e}")
        except IsADirectoryError as e:
            logger.error(f"Page {self.path}: path {filepath} is a directory\n{e}")
        for node in self.children: # (dynamically created) sub-pages
            node.render()
        self.event('render:post:page:any')
        self.event('render:post:page:name:' + self.name)
        if self.id:
            self.event('render:post:page:id:' + self.id)
        for tag in self.tags: self.event('render:post:page:tag:' + tag)


"""Asset node class"""
class Asset(Node):
    def __init__(self, name: str, path: str, parent: Node):
        """Create new Asset node with name `name` and filesystem path `path`."""
        super().__init__(name, path, parent)
        self.kind = 'Asset'
        self.url = setting.root_url + self.path

    def ready(self):
        """Asset node is ready: send event(s)."""
        suffix = splitext(self.path)[1][1:]
        self.event('generate:post:asset:name:' + self.name)
        self.event('generate:post:asset:extension:' + suffix)

    def render(self):
        """Render Asset node."""
        suffix = splitext(self.path)[1][1:]
        self.event('render:pre:asset:name:' + self.name)
        self.event('render:pre:asset:extension:' + suffix)
        output_path = join(setting.output, setting.root_url[1:], self.path)
        transform = transformer[suffix] if suffix in transformer else transformer['*']
        transform(join(setting.input, self.path), output_path)
        self.event('render:post:asset:name:' + self.name)
        self.event('render:post:asset:extension:' + suffix)
