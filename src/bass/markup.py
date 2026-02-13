"""
bass.markup
-----
Objects and functions related to markup of text pages.

On module initialization, the dictionary 'converter' is populated with available markup
converters, depending on which external packages are available.
"""

import re
from collections.abc import Callable
from .common import logger

# available page converters
converter = {}

# Pygments
try:
    import pygments
    have_pygments = True
except:
    have_pygments = False

# Markdown
try:
    import markdown
    extensions = ['markdown.extensions.tables', 'markdown.extensions.def_list', 'markdown.extensions.fenced_code']
    if have_pygments:
        extensions.append('markdown.extensions.codehilite')
    def convert_mkd(text):
        return markdown.markdown(text, extensions=extensions)
    converter['.mkd'] = convert_mkd
    have_markdown = True
except ImportError:
    have_markdown = False

# Markdown 2
if not have_markdown:
    try:
        import markdown2
        extensions = ['tables']
        if have_pygments:
            extensions.append('fenced-code-blocks')
        def convert_md2(text):
            return markdown2.markdown(text, extras=extensions)
        converter['.mkd'] = convert_md2
        have_markdown  = True
    except ImportError:
        have_markdown  = False

# RestructuredText
try:
    import docutils.core
    from docutils.writers.html4css1 import Writer
    def convert_rst(text):
        return docutils.core.publish_parts(text, writer=Writer())['body']
    converter['.rst'] = convert_rst
    have_rest = True
except ImportError:
    have_rest = False

# Textile
try:
    import textile
    def convert_txi(text):
        return textile.textile(text)
    converter['.txi'] = convert_txi
    have_textile = True
except ImportError:
    have_textile = False

# HTML
def convert_html(text):
    return text
converter['.html'] = convert_html

# plain text
def convert_txt(text):
    return '<p>' + re.sub(r'\n{2,}', '</p><p>', text) + '</p>'
converter['.txt'] = convert_txt

# user-defined converters
def add_converter(extension: str, conv: Callable) -> None:
    """Add converter for `extension`.

    Arguments:
        extension (str): extension of filetype
        conv (Callable): callable for this filetype
    """
    if callable(conv):
        if extension in converter:
            logger.debug(f'Converter for {extension} already exists')
        else:
            logger.debug(f'New converter for {extension}')
            converter[extension] = conv
    else:
        logger.debug(f'Converter for {extension} is not a callable')
