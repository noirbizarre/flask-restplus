# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import MutableMapping


class ApiModel(dict, MutableMapping):
    '''A thin wrapper on dict to store API doc metadata'''
    def __init__(self, *args, **kwargs):
        self.__apidoc__ = {}
        super(ApiModel, self).__init__(*args, **kwargs)

    def __call__(self, raw=None, **kwargs):
        print 'call', raw, kwargs
