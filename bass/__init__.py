# -*- coding: utf-8 -*-
"""
Bass
-----
Bass is a tool for building static web sites.
Wok and StrangeCase served as sources of inspiration.
Chameleon is used for templating.
"""

from .config import parse_cmdline
from .site import build_site, create_project
from .convert import converter
