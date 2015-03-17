# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from contextlib import contextmanager

from flask import Flask


class TestCase(unittest.TestCase):
    '''An helper mixin for common operations'''
    def setUp(self):
        '''Initialize an Flask application'''
        self.app = Flask(__name__)

    @contextmanager
    def context(self):
        with self.app.test_request_context('/'):
            yield

    def get_specs(self, prefix='/api', app=None, status=200):
        '''Get a Swagger specification for a RestPlus API'''
        with self.app.test_client() as client:
            response = client.get('{0}/swagger.json'.format(prefix))
            self.assertEquals(response.status_code, status)
            self.assertEquals(response.content_type, 'application/json')
            return json.loads(response.data.decode('utf8'))

    def get_declaration(self, namespace='default', prefix='/api', status=200, app=None):
        '''Get an API declaration for a given namespace'''
        with self.app.test_client() as client:
            response = client.get('{0}/swagger.json'.format(prefix, namespace))
            self.assertEquals(response.status_code, status)
            self.assertEquals(response.content_type, 'application/json')
            return json.loads(response.data.decode('utf8'))

    def get_json(self, url, status=200):
        with self.app.test_client() as client:
            response = client.get(url)

        self.assertEquals(response.status_code, status)
        self.assertEquals(response.content_type, 'application/json')
        return json.loads(response.data.decode('utf8'))
