"""
bass.server
-----
Simple web server for development and test purposes.
"""

from os import chdir, walk
from os.path import join, getmtime
from datetime import datetime
from .site import rebuild_site
from . import setting
from .common import logger

try:
    from webob import Request, Response
    from webob.static import DirectoryApp

    class Monitor():
        """class for generating WSGI middleware handler"""
        def __init__(self, app, checklist, callback):
            self.wrapped = app
            self.timestamp = datetime.now()
            self.checklist = checklist
            self.callback = callback

        def changed(self):
            """return True if any file in one of the directories in self.checklist has changed
               since self.timestamp, otherwise False"""
            for checkdir in self.checklist:
                for (dirpath, _, filenames) in walk(checkdir):
                    for f in filenames:
                        path = join(dirpath, f)
                        if datetime.fromtimestamp(getmtime(path)) > self.timestamp:
                            logger.debug('%s has changed', path)
                            return True
            return False

        def __call__(self, environ, start_response):
            """this __call__ method turns an instance into a WSGI middleware handler"""
            request = Request(environ)
            # check for modifications every time a page (not an asset) is requested
            if request.path.endswith('.html') and self.changed():
                logger.debug('Rebuilding site')
                self.timestamp = datetime.now()
                self.callback()
            response = request.get_response(self.wrapped)
            dt = datetime.strftime(datetime.now(), "%d/%b/%Y %H:%M:%S")
            logger.info('{} - - [{}] "{} {}" {} {}'.\
                        format(request.server_name, dt, request.method, request.path_info,
                               response.status, response.content_length))
            return response(environ, start_response)

    try:
        from waitress import serve
    except ImportError:
        from wsgiref.simple_server import make_server
        def serve(app, host, port):
            """serve: WSGI server with same interface as waitress.serve"""
            server = make_server(host, port, app)
            server.serve_forever()

    def http_server(host, port):
        """http_server: WSGI-based web server with same interface as in standard library"""
        static = DirectoryApp(setting.output, index_page=None)
        wrapped = Monitor(static, checklist=[setting.input, setting.layout], callback=rebuild_site)
        logger.debug('Starting HTTP server on port %d', port)
        serve(wrapped, host=host, port=port)

except ImportError:
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    def http_server(host, port):
        """http_server: basic web server based on standard library"""
        chdir(setting.output)
        httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
        logger.debug('Starting HTTP server on port %d', port)
        httpd.serve_forever()
