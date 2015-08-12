# -*- coding: utf-8 -*-
"""
bass.server
-----
Simple web server for development and test purposes.
"""

import logging, os
from datetime import datetime
from .site import rebuild_site
from . import setting

try:
    from webob import Request, Response
    from webob.static import DirectoryApp

    class Monitor():
        def __init__(self, app, checklist, callback):
            self.wrapped = app
            self.timestamp = datetime.now()
            self.checklist = checklist
            self.callback = callback

        def changed(self, path):
            """return True if any file has changed since self.timestamp, otherwise False"""
            for checkdir in self.checklist:
                for (root, _, filelist) in os.walk(checkdir):
                    for f in filelist:
                        path = os.path.join(root, f)
                        if datetime.fromtimestamp(os.path.getmtime(path)) > self.timestamp:
                            logging.debug('%s has changed', path)
                            return True
            return False

        def __call__(self, environ, start_response):
            request = Request(environ)
            # check for modifications every time a page (not an asset) is requested
            if request.path.endswith('.html') and self.changed(request.path):
                logging.debug('Rebuilding site')
                self.timestamp = datetime.now()
                self.callback()
            response = request.get_response(self.wrapped)
            return response(environ, start_response)

    try:
        from waitress import serve
    except ImportError:
        from wsgiref.simple_server import make_server
        def serve(app, host, port):
            server = make_server(host, port, app)
            server.serve_forever()

    def http_server(host, port):
        static = DirectoryApp(setting.output, index_page=None)
        wrapped = Monitor(static, checklist=[setting.input, setting.layout], callback=rebuild_site)
        logging.debug('Starting HTTP server on port %d', port)
        serve(wrapped, host=host, port=port)

except ImportError:
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    def http_server(host, port):
        os.chdir(setting.output)
        httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
        logging.debug('Starting HTTP server on port %d', port)
        httpd.serve_forever()
