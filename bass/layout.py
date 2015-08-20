# -*- coding: utf-8 -*-
"""
bass.layout
-----
Objects and functions related to the layout of the site tree.
Chameleon is the primary template engine. Other engines can be added.
"""

from . import setting
from os import listdir
from os.path import join, splitext
import logging, sys

# By default, there is one template factory: chameleon.PageTemplate. This is connected
# to the file extensions '.xml' and '.pt'. Other template factories can be defined, provided
# they implement the following protocol:
#   - extension -> template factory: T = template_factory[extension]
#   - filename -> template: t = T(filename)
#   - node -> string: t.render(this=node) is HTML page for node 'this'

template_factory = {}

try:
    from chameleon import PageTemplateFile
    template_factory['.xml'] = PageTemplateFile
    template_factory['.pt'] = template_factory['.xml']
except ImportError:
    logging.critical('Chameleon template engine not available')
    sys.exit()

setting.template_factory = template_factory

def read_templates():
    """read templates from layout directory"""
    template = {}
    template_types = list(template_factory.keys())
    logging.debug('Scanning for templates in {0}'.format(setting.layout))
    logging.debug('Template types: {0}'.format(' '.join(template_types)))
    for filename in listdir(setting.layout):
        (name, extension) = splitext(filename)
        if extension in template_types: # other extensions are ignored
            try:
                template[name] = template_factory[extension](join(setting.layout, filename))
            except Exception as e:
                logging.debug('Error in template for {0} in file {1}'.format(name, filename))
                logging.debug(str(e))
    if 'default' in template:
        setting.template = template
    else:
        logging.critical('There is no default template')
        sys.exit()
