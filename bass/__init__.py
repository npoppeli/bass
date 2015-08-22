# -*- coding: utf-8 -*-
"""
Bass
-----
Bass is a tool for building static web sites.
Wok, Wintersmith, Pelican and StrangeCase served as sources of inspiration.
Markdown, RestructuredText and Textile are used for light-weight page markup.
Chameleon is used for templating, but other template engines can be added.

Functions:
    - parse_cmdline: parse command line, return parsed argument list
    - build_site: build new site from content and layout directories
    - create_project: create new project with default configuration
    - converter: dictionary of known page converters (for customization by user)
    - http_server: simple HTTP server, for development and testing
"""

from .config import parse_cmdline
from .event  import add_toc, add_handler, copy_handler, remove_handler
from .layout import add_template_type, copy_template_type
from .server import http_server
from .site   import build_site, create_project
