"""
bass.event
-----
Objects and functions related to events and event handlers.
"""

import re, sys
from os.path import splitext
from typing import Callable, TypeAlias
from . import setting
from .markup import converter
from .common import logger
from .tree import Node

event_handler = {}

Handler: TypeAlias = Callable[[Node], None]
# as of Python v3.12 we can write this as follows:
# type Handler = Callable[[Node], None]

def combine(h1: Handler, h2: Handler) -> Handler:
    """Combine two handlers.

    Arguments:
        h1, h2 (function): handler functions for nodes

    Returns:
        handler that performs 'h1' and then 'h2'
    """
    def _h12(node):
        h1(node)
        h2(node)
    return _h12

def add_handler(event: str, handler: Handler) -> None:
    """Add handler for event.

    Arguments:
        event (str): description of event
        handler (Handler): handler callable for this event
    """
    if callable(handler):
        if event in event_handler:
            logger.debug(f'Event handler for {event} extended')
            event_handler[event] = combine(event_handler[event], handler)
        else:
            logger.debug(f'New event handler for {event}')
            event_handler[event] = handler
    else:
        logger.debug(f'Event handler for {event} is not a callable')

def copy_handler(from_event: str, to_event: str) -> None:
    """Copy handler for event 'from_event' to event 'to_event'.

    Arguments:
        from_event (str): description of event
        to_event (str): description of event
    """
    if from_event in event_handler:
        logger.debug(f'Event handler for {to_event} copied from {from_event}')
        event_handler[to_event] = event_handler[from_event]
    else:
        logger.debug(f'No event handler for {from_event} - cannot copy')

def remove_handler(event: str) -> None:
    """Remove handler for event 'event'.

    Arguments:
        event (str): description of event
    """
    if event in event_handler:
        logger.debug(f'Event handler for {event} removed')
        del event_handler[event]
    else:
        logger.debug(f'No event handler for {event} - cannot remove')


class Processor:
    """
    Processor instances are page processors for a given type of markup.
    """
    def __init__(self, converter=None):
        """Construct page processor for given markup converter.

        Arguments:
            converter (callable): markup converter
        """
        self.convert = converter

    def __call__(self, node: Node):
        """Convert node.content, node.preview and node.meta, which are set by the
           node constructor, to HTML. Also set node.url.

        Arguments:
            node (Node): node to be processed
        """
        if self.convert:
            # convert node.content and node.preview
            node.preview = self.convert(node.preview) if node.preview else ''
            node.content = self.convert(node.content)
        page_name = splitext(node.path)[0]
        # set node.url to setting.root_url + page_name + HTML extension
        node.url = '{0}{1}.html'.format(setting.root_url, page_name)

# define event handlers for the standard page types, depending on which Python packages are installed
if '.mkd' in converter:
    markdown_processor = Processor(converter['.mkd'])
    add_handler('generate:post:page:extension:mkd', markdown_processor)
    copy_handler('generate:post:page:extension:mkd', 'generate:post:page:extension:md')

if '.rst' in converter:
    rest_processor = Processor(converter['.rst'])
    add_handler('generate:post:page:extension:rst', rest_processor)

if '.txi' in converter:
    textile_processor = Processor(converter['.txi'])
    add_handler('generate:post:page:extension:txi', textile_processor)

html_processor = Processor(converter['.html'])
add_handler('generate:post:page:extension:html', html_processor)

text_processor = Processor(converter['.txt'])
add_handler('generate:post:page:extension:txt', text_processor)

# auxiliary functions for extensions

# partition and add_toc can be used in event handlers to produce index pages (with optional pagination).
def partition(lst: list, size: int) -> list:
    """Divide list `lst` in list of sub-lists of length <= `size`.

    Arguments:
        lst (str): description of event
    """
    return [lst[offset:offset+size] for offset in range(0, len(lst), size)]

def add_toc(page, nodelist, skin, sep='_', size=10):
    """Add a table of contents to the specified node, apply pagination if necessary.

    Arguments:
        page (Node): node to which table of contents is added
        nodelist ([Node]): nodes to include in table of contents
        skin (string|callable):
            - string: name of template to render one node in nodelist
            - callable: callable to render one node in nodelist
    """
    # determine method for converting node to HTML fragment
    if callable(skin):
        logger.debug("add_toc: parameter 'skin' is a callable")
        func = skin
    elif isinstance(skin, str):
        logger.debug("add_toc: parameter 'skin' is a template")
        func = setting.template[skin].render
    else:
        logger.critical("Bad parameter 'skin' in function 'add_toc'")
        sys.exit(1)
    # create one HTML fragment per node, then partition the list of fragments in chunks of `size`
    results = []
    for node in nodelist:
        try:
            result = func(this=node)
            results.append(result)
        except AttributeError:
            logger.debug(f"add_toc: node {node.name} misses an attribute")
    parts = partition(results, size)
    # create 'prev' and 'next' links
    page.prev, page.next = None, None
    previous = page
    logger.debug(f'add_toc: main page name={page.name} path={page.path}, {len(parts)} parts')
    if len(parts) > 0:
        page.toc = '\n'.join(parts[0])
    else:
        page.toc = ''
    if len(parts) > 1:
        for p, part in enumerate(parts[1:]):
            current = page.copy(sep+str(p+1))
            logger.debug(f'add_toc: subpage name={current.name} path={current.path}')
            current.toc = '\n'.join(part)
            page.add(current)
            previous.next = current
            current.prev = previous
            previous = current
        previous.next = None # last subpage

# resolve_idref is an event handler for resolving idref notation in href attributes.
idref_regex = re.compile(r"href=(['\"])idref:\s*(\w+?)\1")

def resolve_idref(node: Node):
    """Replace href='idref:FOO' with href='BAR', where BAR is the URL of the page with id=FOO.

    Arguments:
        node (Node): node in the content tree
    """
    def idref_replace(mo):
        catch = node.root().pages(idref=mo.group(2), deep=True)
        return "href={0}{1}{0}".format(mo.group(1), catch[0].url if catch else '#')

    node.preview = idref_regex.sub(idref_replace, node.preview)
    node.content = idref_regex.sub(idref_replace, node.content)
