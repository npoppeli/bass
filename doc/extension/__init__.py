from bass import add_handler, resolve_idref
import logging

def table_class(this):
    logging.debug('render:pre:page:tag:table called for page %s', this.name)
    this.content = this.content.replace('<table>', '<table class="table">')\
                               .replace('class="docutils"', 'class="table"')\
                               .replace('border="1"', '')

add_handler('render:pre:page:tag:table', table_class)
add_handler('render:pre:page:any',       resolve_idref)
