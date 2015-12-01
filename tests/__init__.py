# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from mock import Mock
except:
    # python3
    from unittest.mock import Mock

from contextlib import contextmanager

from flask import Flask


skipIf = unittest.skipIf


class TestCase(unittest.TestCase):
    '''An helper mixin for common operations'''
    def setUp(self):
        '''Initialize an Flask application'''
        self.app = Flask(__name__)

    @contextmanager
    def context(self):
        with self.app.test_request_context('/'):
            yield

    @contextmanager
    def settings(self, **settings):
        '''
        A context manager to alter app settings during a test and restore it after..
        '''
        original = {}

        # backup
        for key, value in settings.items():
            original[key] = self.app.config.get(key)
            self.app.config[key] = value

        yield

        # restore
        for key, value in original.items():
            self.app.config[key] = value

    def get_json(self, url, status=200, headers=None):
        with self.app.test_client() as client:
            response = client.get(url, headers=headers or {})

        self.assertEquals(response.status_code, status)
        self.assertEquals(response.content_type, 'application/json')
        return json.loads(response.data.decode('utf8'))

    def get_specs(self, prefix='', status=200):
        '''Get a Swagger specification for a RestPlus API'''
        return self.get_json('{0}/swagger.json'.format(prefix), status=status)
