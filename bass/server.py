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
    import waitress
    from webob import Request, Response
    from webob.static import DirectoryApp

    class Monitor():
        def __init__(self, app, monitor, callback):
            self.wrapped = app
            self.timestamp = datetime.now()
            self.monitor = monitor
            self.callback = callback

        def _changed(self, path):
            """return True if any file has changed since self.timestamp, otherwise False"""
            for mondir in self.monitor:
                for (root, dirlist, filelist) in os.walk(mondir):
                    for f in filelist:
                        path = os.path.join(root, f)
                        if datetime.fromtimestamp(os.path.getmtime(path)) > self.timestamp:
                            logging.debug('%s has changed', path)
                            return True
            return False

        def __call__(self, environ, start_response):
            request = Request(environ)
            # check for modifications every time a page (not an asset) is requested
            if request.path.endswith('.html') and self._changed(request.path):
                logging.debug('Rebuilding site')
                self.timestamp = datetime.now()
                self.callback()
            response = request.get_response(self.wrapped)
            return response(environ, start_response)

    def http_server():
        static = DirectoryApp(setting.output, index_page=None)
        wrapped = Monitor(static, monitor=[setting.input, setting.layout], callback=rebuild_site)
        logging.debug('Starting HTTP server on port 8080')
        waitress.serve(wrapped, port=8080)

except ImportError:
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    def http_server():
        os.chdir(setting.output)
        httpd = HTTPServer(('', 8080), SimpleHTTPRequestHandler)
        logging.debug('Starting HTTP server on port 8080')
        httpd.serve_forever()
