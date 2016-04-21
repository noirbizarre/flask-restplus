# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import warnings

try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from mock import Mock, patch
except:
    # python3
    from unittest.mock import Mock, patch  # noqa

from contextlib import contextmanager

from flask import Flask


from nose.tools import assert_equal, assert_raises  # noqa
try:
    from nose.tools import assert_equal, assert_raises, assert_in, assert_not_in, assert_is_none  # noqa
except:
    # Extract unittest2.TestCase methods using the same method than nose (only for Python 2.6)
    class Dummy(unittest.TestCase):
        def nop():
            pass
    dummy = Dummy('nop')

    assertions = {
        'assert_equal': 'assertEqual',
        'assert_raises': 'assertRaises',
        'assert_in': 'assertIn',
        'assert_not_in': 'assertNotIn',
        'assert_is_none': 'assertIsNone',
    }

    for local_name, unittest_name in assertions.items():
        vars()[local_name] = getattr(dummy, unittest_name)

    del Dummy
    del dummy


def assert_data_equal(tested, expected):
    '''Compare data without caring about order and type (dict vs. OrderedDict)'''
    tested = json.loads(json.dumps(tested))
    expected = json.loads(json.dumps(expected))
    assert_equal(tested, expected)


class TestCase(unittest.TestCase):
    '''An helper mixin for common operations'''
    def setUp(self):
        '''Initialize an Flask application'''
        self.app = Flask(__name__)

    @contextmanager
    def context(self, **kwargs):
        with self.app.test_request_context('/', **kwargs):
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

    @contextmanager
    def assert_warning(self, category=Warning):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            # Cause all warnings to always be triggered.
            yield
            self.assertGreaterEqual(len(w), 1, 'It should raise a warning')
            warning = w[0]
            self.assertEqual(warning.category, category, 'It should raise {0}'.format(category.__name__))

    def get(self, url, **kwargs):
        with self.app.test_client() as client:
            return client.get(url, **kwargs)

    def post(self, url, **kwargs):
        with self.app.test_client() as client:
            return client.post(url, **kwargs)

    def get_json(self, url, status=200, **kwargs):
        response = self.get(url, **kwargs)
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.content_type, 'application/json')
        return json.loads(response.data.decode('utf8'))

    def get_specs(self, prefix='', status=200, **kwargs):
        '''Get a Swagger specification for a RestPlus API'''
        return self.get_json('{0}/swagger.json'.format(prefix), status=status, **kwargs)

    def assertDataEqual(self, tested, expected):
        '''Compare data without caring about order and type (dict vs. OrderedDict)'''
        assert_data_equal(tested, expected)
