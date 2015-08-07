# -*- coding: utf-8 -*-
"""
bass.server
-----
Simple web server for development and test purposes.
"""

import logging, os
from http.server.static import HTTPServer, SimpleHTTPRequestHandler
from . import setting

def http_server(**kwarg):
    logging.debug('Starting HTTP server')
    os.chdir(setting.output)
    httpd = HTTPServer(('', 8080), SimpleHTTPRequestHandler)
    httpd.serve_forever()
