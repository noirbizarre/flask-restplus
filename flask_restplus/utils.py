# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from copy import deepcopy
from six import iteritems

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


def merge(first, second):
    '''
    Recursively merges two dictionnaries.

    Second dictionnary values will take precedance over those from the first one.
    Nested dictionnaries are merged too.
    '''
    if not isinstance(second, dict):
        return second
    result = deepcopy(first)
    for key, value in iteritems(second):
        if key in result and isinstance(result[key], dict):
                result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def camel_to_dash(value):
    '''Transform a CamelCase string into a low_dashed one'''
    first_cap = FIRST_CAP_RE.sub(r'\1_\2', value)
    return ALL_CAP_RE.sub(r'\1_\2', first_cap).lower()


def default_id(resource, method):
    '''Default operation ID generator'''
    return '{0}_{1}'.format(method, camel_to_dash(resource))


def not_none(data):
    '''Remove all keys where value is None'''
    return dict((k, v) for k, v in iteritems(data) if v is not None)


def not_none_sorted(data):
    '''Remove all keys where value is None'''
    ordered_items = OrderedDict(sorted(iteritems(data)))
    return OrderedDict((k, v) for k, v in iteritems(ordered_items) if v is not None)
