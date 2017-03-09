# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from flask_restplus import utils


class MergeTestCase(object):
    def test_merge_simple_dicts_without_precedence(self):
        a = {'a': 'value'}
        b = {'b': 'other value'}
        assert utils.merge(a, b) == {'a': 'value', 'b': 'other value'}

    def test_merge_simple_dicts_with_precedence(self):
        a = {'a': 'value', 'ab': 'overwritten'}
        b = {'b': 'other value', 'ab': 'keep'}
        assert utils.merge(a, b) == {'a': 'value', 'b': 'other value', 'ab': 'keep'}

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
        assert utils.merge(a, b) == {
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
        }

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
        assert utils.merge(a, b) == b


class CamelToDashTestCase(object):
    def test_no_transform(self):
        assert utils.camel_to_dash('test') == 'test'

    @pytest.mark.parametrize('value,expected', [
        ('aValue', 'a_value'),
        ('aLongValue', 'a_long_value'),
        ('Upper', 'upper'),
        ('UpperCase', 'upper_case'),
    ])
    def test_transform(self, value, expected):
        assert utils.camel_to_dash(value) == expected


class UnpackTest(object):
    def test_single_value(self):
        data, code, headers = utils.unpack('test')
        assert data == 'test'
        assert code == 200
        assert headers == {}

    def test_single_value_with_default_code(self):
        data, code, headers = utils.unpack('test', 500)
        assert data == 'test'
        assert code == 500
        assert headers == {}

    def test_value_code(self):
        data, code, headers = utils.unpack(('test', 201))
        assert data == 'test'
        assert code == 201
        assert headers == {}

    def test_value_code_headers(self):
        data, code, headers = utils.unpack(('test', 201, {'Header': 'value'}))
        assert data == 'test'
        assert code == 201
        assert headers == {'Header': 'value'}

    def test_value_headers_default_code(self):
        data, code, headers = utils.unpack(('test', None, {'Header': 'value'}))
        assert data == 'test'
        assert code == 200
        assert headers == {'Header': 'value'}

    def test_too_many_values(self):
        with pytest.raises(ValueError):
            utils.unpack((None, None, None, None))
