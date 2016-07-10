from bass import add_handler, resolve_idref, logger

logger.info('Define function table_class as extension')
def table_class(this):
    logger.debug('render:pre:page:tag:table called for page %s', this.name)
    this.content = this.content.replace('<table>', '<table class="table">')\
                               .replace('class="docutils"', 'class="table"')\
                               .replace('border="1"', '')

logger.info('Add handler table_class as extension')
add_handler('render:pre:page:tag:table', table_class)
logger.info('Add handler resolve_idref as extension')
add_handler('render:pre:page:any',       resolve_idref)
