# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import unicode_literals

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse
