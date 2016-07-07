"""
Bass
-----
Bass is a tool for building static web sites.
Wok, Wintersmith, Pelican and StrangeCase served as sources of inspiration.
Markdown, RestructuredText and Textile are used for lightweight page markup.
Chameleon is used for templating, but other template engines can be added.

Functions:
    - parse_cmdline: parse command line, return parsed argument list
    - build_site: build new site from content and layout directories
    - create_project: create new project with default configuration
    - http_server: simple HTTP server, for development and testing
    - add_handler: add event handler
    - copy_handler: copy event handler
    - remove_handler: remove event handler
    - add_template_type: add template type (template factory + extension)
    - copy_template_type: copy template type (existing template factory + new extension)
    - logger: logging object
    - resolve_idref: event handler for resolving idref notation
    - add_toc: helper function for creating event handler
"""

from .common  import logger
from .config  import parse_cmdline
from .event   import add_toc, add_handler, copy_handler, remove_handler, resolve_idref
from .layout  import add_template_type, copy_template_type
from .server  import http_server
from .site    import build_site, create_project
