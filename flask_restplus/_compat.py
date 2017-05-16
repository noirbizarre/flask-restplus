# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import sys

# Use optimized OrderedDict when available on Python < 3.5
# Starting Python 3.5 OrderedDict has been rewitten in C
if sys.version_info[0:2] < (3, 5):
    try:
        from cyordereddict import OrderedDict  # noqa
    except ImportError:
        from collections import OrderedDict  # noqa
else:
    from collections import OrderedDict  # noqa
