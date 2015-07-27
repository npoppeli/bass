# -*- coding: utf-8 -*-
"""
bass.render
-----
Objects and functions related to rendering the site tree.
Chameleon is the primary template toolkit.
"""

from .common import keep, read_file
from glob import glob
from chameleon import PageTemplate
import logging

def read_templates():
    template = {}
    for filename in glob(keep.config['templates']+'/*.xml'):
        name = os.path.basename(filename).replace('.xml', '')
        try:
            template[name] = PageTemplate(read_file(filename))
        except Exception as e:
            logging.debug('error in template for {0} in file {1}'.format(name, filename))
            logging.debug(str(e))
    keep.template = template
