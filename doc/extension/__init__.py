from bass import add_handler, resolve_idref
import logging

print('extension: define function table_class')
def table_class(this):
    logging.debug('render:pre:page:tag:table called for page %s', this.name)
    this.content = this.content.replace('<table>', '<table class="table">')\
                               .replace('class="docutils"', 'class="table"')\
                               .replace('border="1"', '')

print('extension: add handler table_class')
add_handler('render:pre:page:tag:table', table_class)
print('extension: add handler resolve_idref')
add_handler('render:pre:page:any',       resolve_idref)