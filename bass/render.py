# -*- coding: utf-8 -*-
"""
bass.render
-----
Objects and functions related to rendering the site tree.
Chameleon is the primary template engine.
"""

from .common import read_file
from . import setting
from os import listdir
from os.path import join, splitext
import logging, sys

# TODO: make it possible to add other template engines
# map extensions to template factories
# .xml -> chameleon.PageTemplate
# .jpt -> jinja2.SomeClass

setting.template_factory = {}

try:
    from chameleon import PageTemplate
    setting.template_factory['.xml'] = PageTemplate
    setting.template_factory['.pt'] = setting.template_factory['.xml']
except ImportError:
    logging.critical('Chameleon template engine not available.')
    sys.exit()

def read_templates():
    template = {}
    template_types = list(setting.template_factory.keys())
    logging.debug('Scanning for templates in {0}'.format(setting.templates))
    for filename in listdir(setting.templates):
        (name, extension) = splitext(filename)
        if extension in template_types:
            try:
                logging.debug('Template for {0} in file {1}'.format(name, filename))
                template[name] = setting.template_factory[extension](
                    read_file(join(setting.templates, filename)))
            except Exception as e:
                logging.debug('Error in template for {0} in file {1}'.format(name, filename))
                logging.debug(str(e))
        else:
            pass # ignore
    setting.template = template
