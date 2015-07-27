# -*- coding: utf-8 -*-
"""
bass.convert
-----
Objects and functions related to conversion of text pages.
"""

import logging, re
from .common import keep

# available converters
converter = {}

# Markdown
try:
    import markdown2
    markdown_found = True
    def convert_mkd(text):
        return markdown2.markdown(text, extras=['def_list', 'footnotes', 'tables'])
    converter['.md']  = convert_mkd
    converter['.mkd'] = convert_mkd
    keep.markdown = True
except ImportError:
    keep.markdown = False

if not markdown_found:
    try:
        import markdown
        def convert_mkd(text):
            return markdown.markdown(text, extras=['def_list', 'footnotes'])
        converter['.md']  = convert_mkd
        converter['.mkd'] = convert_mkd
    except ImportError:
        keep.markdown = False

# RestructuredText
try:
    import docutils.core
    from docutils.writers.html4css1 import Writer as rst_writer
    def convert_rst(text):
        return docutils.core.publish_parts(text, writer=rst_writer())['body']
    converter['.rst'] = convert_rst
    keep.restructuredtext = True
except ImportError:
    keep.restructuredtext = False

# Textile
try:
    import textile
    def convert_txi(text):
        return textitle.textile(text)
    converter['.txi'] = convert_txi
    keep.textile = True
except ImportError:
    keep.textile = False

# HTML
converter['.html'] = lambda text: text

# plain text
def convert_txt(text):
    return '<p>' + re.sub(r'\n{2,}', '</p><p>', text) + '</p>'
converter['.txt'] = convert_txt

keep.converter = converter
keep.pagetypes = list(converter.keys())
