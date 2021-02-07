"""
bass.layout
-----
Objects and functions related to the layout of the rendered pages.
Chameleon is the primary template engine. Other template engines can be added.
"""

from . import setting
from .common import logger
from os import listdir
from os.path import join, splitext, isfile
import sys

# By default, there is one template factory: chameleon.PageTemplateFile. This is associated
# with the file extensions '.xml' and '.pt'. Other template factories can be defined,
# provided they implement the following interface:
#   - filename -> template: template = template_factory(filename)
#   - node     -> string: template.render(this=node) returns HTML page for node 'this'
#                 (condition: node.skin should be equal to filename without extension)
# Template factories are stored in a dictionary template_factory, with the extension as key.

template_factory = {}

def add_template_type(extension, factory):
    """
    add template factory for given extension
    :param extension: file extension (.foo)
    :param factory:   template factory (callable object)
    """
    if extension in template_factory:
        logger.debug(f'Cannot redefine template type {extension}')
    else:
        logger.debug(f'Define new template type {extension}')
        template_factory[extension] = factory

def copy_template_type(from_extension, to_extension):
    """copy existing template factory to another extension"""
    if to_extension in template_factory:
        logger.debug(f'Cannot redefine template type {to_extension}')
    elif from_extension in template_factory:
        logger.debug(f'Template type {to_extension} copied from {from_extension}')
        template_factory[to_extension] = template_factory[from_extension]
    else:
        logger.debug(f'No template type {from_extension}')

try:
    from chameleon import PageTemplateFile
    add_template_type('.xml', PageTemplateFile)
    copy_template_type('.xml', '.pt')
except ImportError:
    logger.critical('Chameleon template engine not available')
    sys.exit(1)

def read_templates():
    """Read templates from layout directory. This function should be called
    just before rendering the site tree and after the extensions have been imported."""
    template = {}
    template_types = list(template_factory.keys())
    logger.debug('Scanning for templates in {}'.format(setting.layout))
    logger.debug('Template types: {}'.format(' '.join(template_types)))
    for filename in listdir(setting.layout):
        (name, extension) = splitext(filename)
        file_path = join(setting.layout, filename)
        # all files (not symbolic links) with a recognized extension are possible templates
        if isfile(file_path) and extension in template_types: # other files are ignored
            try:
                template[name] = template_factory[extension](file_path)
            except Exception as e:
                logger.debug(f'Error in template for {name} in file {filename}')
                logger.debug(str(e))
    if 'default' in template:
        setting.template = template
    else:
        logger.critical('There is no default template')
        sys.exit(1)
