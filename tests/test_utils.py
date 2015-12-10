# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus import utils

from . import TestCase


class MergeTestCase(TestCase):
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


class CamelToDashTestCase(TestCase):
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


class UnpackTest(TestCase):
    def test_single_value(self):
        data, code, headers = utils.unpack('test')
        self.assertEqual(data, 'test')
        self.assertEqual(code, 200)
        self.assertEqual(headers, {})

    def test_single_value_with_default_code(self):
        data, code, headers = utils.unpack('test', 500)
        self.assertEqual(data, 'test')
        self.assertEqual(code, 500)
        self.assertEqual(headers, {})

    def test_value_code(self):
        data, code, headers = utils.unpack(('test', 201))
        self.assertEqual(data, 'test')
        self.assertEqual(code, 201)
        self.assertEqual(headers, {})

    def test_value_code_headers(self):
        data, code, headers = utils.unpack(('test', 201, {'Header': 'value'}))
        self.assertEqual(data, 'test')
        self.assertEqual(code, 201)
        self.assertEqual(headers, {'Header': 'value'})

    def test_value_headers_default_code(self):
        data, code, headers = utils.unpack(('test', None, {'Header': 'value'}))
        self.assertEqual(data, 'test')
        self.assertEqual(code, 200)
        self.assertEqual(headers, {'Header': 'value'})

    def test_too_many_values(self):
        with self.assertRaises(ValueError):
            utils.unpack((None, None, None, None))
