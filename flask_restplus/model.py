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
    '''
    Resolve real fields before submitting them to upstream restful marshal
    '''
    # Duplicate fields
    resolved = copy.deepcopy(fields)

    # Recursively copy parent fields if necessary
    if getattr(fields, '__parent__'):
        resolved.update(resolve_fields(fields.__parent__))

    # Handle discriminator
    candidates = [f for f in resolved.values() if getattr(f, 'discriminator', None)]
    # Ensure the is only one discriminator
    if len(candidates) > 1:
        raise ValueError('There can only be one discriminator by schema')
    # Ensure discriminator always output the model name
    elif len(candidates) == 1:
        candidates[0].default = fields.__apidoc__['name']

    return resolved
