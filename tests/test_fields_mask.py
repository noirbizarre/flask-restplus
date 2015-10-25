# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask.ext.restplus import mask

from . import TestCase


class ParseMaskMixin(object):
    def test_empty_mask(self):
        self.assertEqual(mask.parse(''), [])

    def test_one_field(self):
        self.assertEqual(mask.parse('field_name'), ['field_name'])

    def test_multiple_field(self):
        parsed = mask.parse('field1, field2,field3')
        self.assertEqual(parsed, ['field1', 'field2', 'field3'])

    def test_nested_fields(self):
        parsed = mask.parse('nested{field1,field2}')
        expected = [mask.Nested('nested', ['field1', 'field2'])]
        self.assertEqual(parsed, expected)

    def test_complex(self):
        parsed = mask.parse('field1, nested{field, sub{subfield}}, field2')
        expected = [
            'field1',
            mask.Nested('nested', [
                'field',
                mask.Nested('sub', ['subfield'])
            ]),
            'field2'
        ]
        self.assertEqual(parsed, expected)

    def test_missing_closing_bracket(self):
        with self.assertRaises(mask.ParseError):
            mask.parse('nested{')

    def test_consecutive_coma(self):
        with self.assertRaises(mask.ParseError):
            mask.parse('field,,')

    def test_coma_before_bracket(self):
        with self.assertRaises(mask.ParseError):
            mask.parse('field,{}')

    def test_coma_after_bracket(self):
        with self.assertRaises(mask.ParseError):
            mask.parse('nested{,}')

    def test_unexpected_opening_bracket(self):
        with self.assertRaises(mask.ParseError):
            mask.parse('{{field}}')

    def test_unexpected_closing_bracket(self):
        with self.assertRaises(mask.ParseError):
            mask.parse('{field}}')


class ParseMaskUnwrapped(ParseMaskMixin, TestCase):
    def parse(self, value):
        return mask.parse(value)


class ParseMaskWrapped(ParseMaskMixin, TestCase):
    def parse(self, value):
        return mask.parse('{' + value + '}')


class DObject(object):
    '''A dead simple object built from a dictionnary (no recursion)'''
    def __init__(self, data):
        self.__dict__.update(data)


class ApplyMaskTest(TestCase):
    def test_empty(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '{}')
        self.assertEqual(result, {})

    def test_single_field(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '{integer}')
        self.assertEqual(result, {'integer': 42})

    def test_multiple_fields(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '{integer, string}')
        self.assertEqual(result, {'integer': 42, 'string': 'a string'})

    def test_with_objects(self):
        data = DObject({
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        })
        result = mask.apply(data, '{integer, string}')
        self.assertEqual(result, {'integer': 42, 'string': 'a string'})

    def test_nested_field(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
            'nested': {
                'integer': 42,
                'string': 'a string',
                'boolean': True,
            }
        }
        result = mask.apply(data, '{nested}')
        self.assertEqual(result, {'nested': {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }})

    def test_nested_fields(self):
        data = {
            'nested': {
                'integer': 42,
                'string': 'a string',
                'boolean': True,
            }
        }
        result = mask.apply(data, '{nested{integer}}')
        self.assertEqual(result, {'nested': {'integer': 42}})

    def test_nested_fields_when_none(self):
        data = {'nested': None}
        result = mask.apply(data, '{nested{integer}}')
        self.assertEqual(result, {'nested': None})

    def test_list(self):
        data = [{
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }, {
            'integer': 404,
            'string': 'another string',
            'boolean': False,
        }]
        result = mask.apply(data, '{integer, string}')
        self.assertEqual(result, [
            {'integer': 42, 'string': 'a string'},
            {'integer': 404, 'string': 'another string'}
        ])

    def test_nested_list(self):
        data = {
            'integer': 42,
            'list': [{
                'integer': 42,
                'string': 'a string',
            }, {
                'integer': 404,
                'string': 'another string',
            }]
        }
        result = mask.apply(data, '{list}')
        self.assertEqual(result, {'list': [{
            'integer': 42,
            'string': 'a string',
        }, {
            'integer': 404,
            'string': 'another string',
        }]})

    def test_nested_list_fields(self):
        data = {
            'list': [{
                'integer': 42,
                'string': 'a string',
            }, {
                'integer': 404,
                'string': 'another string',
            }]
        }
        result = mask.apply(data, '{list{integer}}')
        self.assertEqual(result, {'list': [{'integer': 42}, {'integer': 404}]})
