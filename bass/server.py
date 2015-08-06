# -*- coding: utf-8 -*-
"""
bass.server
-----
Simple web server for development and test purposes.
"""

import logging, waitress
# TODO: change to Python library: SimpleHTTPServer
from webob.static import DirectoryApp
from . import setting

def http_server(**kwarg):
    logging.debug('Starting HTTP server')
    app = DirectoryApp(setting.output, index_page=None)
    waitress.serve(app, **kwarg)
