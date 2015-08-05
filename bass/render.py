# -*- coding: utf-8 -*-
"""
bass.render
-----
Objects and functions related to rendering the site tree.
Chameleon is the primary template engine. Other engines can be added.
"""

from .common import read_file
from . import setting
from os import listdir
from os.path import join, splitext
import logging, sys

# By default, there is one template factory: chameleon.PageTemplate. This is connected
# to the file extensions '.xml' and '.pt'. Other template factories can be defined, provided
# they follow this protocol.
# extension -> template factory: template_factory[extension] gives a class T
# template string s -> template t: T(string) -> template object t
# t.render(this=node) creates HTML content (preferably: complete page) for specified node

setting.template_factory = {}

try:
    from chameleon import PageTemplate
    setting.template_factory['.xml'] = PageTemplate
    setting.template_factory['.pt'] = setting.template_factory['.xml']
except ImportError:
    logging.critical('Chameleon template engine not available.')
    sys.exit()

def read_templates():
    """read templates from layout directory"""
    template = {}
    template_types = list(setting.template_factory.keys())
    logging.debug('Scanning for templates in {0}'.format(setting.layout))
    for filename in listdir(setting.layout):
        (name, extension) = splitext(filename)
        if extension in template_types: # other extensions are ignored
            try:
                logging.debug('Template for {0} in file {1}'.format(name, filename))
                template[name] = setting.template_factory[extension](
                    read_file(join(setting.layout, filename)))
            except Exception as e:
                logging.debug('Error in template for {0} in file {1}'.format(name, filename))
                logging.debug(str(e))
    setting.template = template
