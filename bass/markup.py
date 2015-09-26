"""
bass.markup
-----
Objects and functions related to markup of text pages.
"""

import re
from . import setting

converter = {}

# Pygments
try:
    import pygments
    setting.pygments = True
except:
    setting.pygments = False

# Markdown
try:
    import markdown2
    def convert_md2(text):
        extensions = ['tables']
        if setting.pygments:
            extensions.append('fenced-code-blocks')
        return markdown2.markdown(text, extras=extensions)
    converter['mkd'] = convert_md2
    setting.markdown  = True
except ImportError:
    setting.markdown  = False

if not setting.markdown:
    try:
        import markdown
        def convert_mkd(text):
            extras = ['markdown.extensions.tables']
            if setting.pygments:
                extras.extend(['markdown.extensions.codehilite',
                               'markdown.extensions.fenced_code'])
            return markdown.markdown(text, extensions=extras)
        converter['mkd'] = convert_mkd
        setting.markdown = True
    except ImportError:
        setting.markdown = False

# RestructuredText
try:
    import docutils.core
    from docutils.writers.html4css1 import Writer
    def convert_rst(text):
        return docutils.core.publish_parts(text, writer=Writer())['body']
    converter['rst'] = convert_rst
    setting.rest = True
except ImportError:
    setting.rest = False

# Textile
try:
    import textile
    def convert_txi(text):
        return textile.textile(text)
    converter['txi'] = convert_txi
    setting.textile = True
except ImportError:
    setting.textile = False

# HTML
def convert_html(text):
    return text
converter['html'] = convert_html

# plain text
def convert_txt(text):
    return '<p>' + re.sub(r'\n{2,}', '</p><p>', text) + '</p>'
converter['txt'] = convert_txt
