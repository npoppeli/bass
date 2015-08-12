# -*- coding: utf-8 -*-
"""
bass.convert
-----
Objects and functions related to conversion of text pages.
"""

import re
from . import setting

# available converters
converter = {}

# Markdown
try:
    import markdown2
    markdown_found = True
    def convert_mkd2(text):
        return markdown2.markdown(text, extras=['def_list', 'footnotes', 'tables'])
    converter['.md']  = convert_mkd2
    converter['.mkd'] = convert_mkd2
    setting.markdown = True
except ImportError:
    setting.markdown = False

if not setting.markdown:
    try:
        import markdown
        def convert_mkd(text):
            return markdown.markdown(text, extras=['markdown.extensions.def_list',
                                                   'markdown.extensions.footnotes',
                                                   'markdown.extensionstables'])
        converter['.md']  = convert_mkd
        converter['.mkd'] = convert_mkd
        setting.markdown = True
    except ImportError:
        setting.markdown = False

# RestructuredText
try:
    import docutils.core
    from docutils.writers.html4css1 import Writer as rst_writer
    def convert_rst(text):
        return docutils.core.publish_parts(text, writer=rst_writer())['body']
    converter['.rst'] = convert_rst
    setting.restructuredtext = True
except ImportError:
    setting.restructuredtext = False

# Textile
try:
    import textile
    def convert_txi(text):
        return textile.textile(text)
    converter['.txi'] = convert_txi
    setting.textile = True
except ImportError:
    setting.textile = False

# HTML
converter['.html'] = lambda text: text

# plain text
def convert_txt(text):
    return '<p>' + re.sub(r'\n{2,}', '</p><p>', text) + '</p>'
converter['.txt'] = convert_txt

setting.converter = converter
