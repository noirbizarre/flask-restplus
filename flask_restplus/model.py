# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy

from collections import MutableMapping


class ApiModel(dict, MutableMapping):
    '''A thin wrapper on dict to store API doc metadata'''
    def __init__(self, *args, **kwargs):
        self.__apidoc__ = {}
        self.__parent__ = None
        super(ApiModel, self).__init__(*args, **kwargs)


def resolve_fields(fields):
    if not getattr(fields, '__parent__', None):
        return fields

    resolved = copy.deepcopy(fields)
    resolved.update(resolve_fields(fields.__parent__))
    return resolved
