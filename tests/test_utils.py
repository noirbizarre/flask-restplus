# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from flask.ext.restplus import utils


class MergeTestCase(unittest.TestCase):
    def test_merge_simple_dicts_without_precedence(self):
        a = {'a': 'value'}
        b = {'b': 'other value'}
        self.assertEqual(utils.merge(a, b), {'a': 'value', 'b': 'other value'})

    def test_merge_simple_dicts_with_precedence(self):
        a = {'a': 'value', 'ab': 'overwritten'}
        b = {'b': 'other value', 'ab': 'keep'}
        self.assertEqual(utils.merge(a, b), {'a': 'value', 'b': 'other value', 'ab': 'keep'})

    def test_recursions(self):
        a = {
            'a': 'value',
            'ab': 'overwritten',
            'nested_a': {
                'a': 'nested'
            },
            'nested_a_b': {
                'a': 'a only',
                'ab': 'overwritten'
            }
        }
        b = {
            'b': 'other value',
            'ab': 'keep',
            'nested_b': {
                'b': 'nested'
            },
            'nested_a_b': {
                'b': 'b only',
                'ab': 'keep'
            }
        }
        self.assertEqual(utils.merge(a, b), {
            'a': 'value',
            'b': 'other value',
            'ab': 'keep',
            'nested_a': {
                'a': 'nested'
            },
            'nested_b': {
                'b': 'nested'
            },
            'nested_a_b': {
                'a': 'a only',
                'b': 'b only',
                'ab': 'keep'
            }
        })

    def test_recursions_with_empty(self):
        a = {}
        b = {
            'b': 'other value',
            'ab': 'keep',
            'nested_b': {
                'b': 'nested'
            },
            'nested_a_b': {
                'b': 'b only',
                'ab': 'keep'
            }
        }
        self.assertEqual(utils.merge(a, b), b)


class CamelToDashTestCase(unittest.TestCase):
    def test_no_transform(self):
        self.assertEqual(utils.camel_to_dash('test'), 'test')

    def test_transform(self):
        tests = {
            'aValue': 'a_value',
            'aLongValue': 'a_long_value',
            'Upper': 'upper',
            'UpperCase': 'upper_case',
        }
        for value, expected in tests.items():
            self.assertEqual(utils.camel_to_dash(value), expected)
