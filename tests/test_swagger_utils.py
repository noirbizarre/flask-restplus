# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus.swagger import extract_path, extract_path_params, parse_docstring

from . import TestCase


class ExtractPathTestCase(TestCase):
    def test_extract_static_path(self):
        path = '/test'
        self.assertEqual(extract_path(path), '/test')

    def test_extract_path_with_a_single_simple_parameter(self):
        path = '/test/<parameter>'
        self.assertEqual(extract_path(path), '/test/{parameter}')

    def test_extract_path_with_a_single_typed_parameter(self):
        path = '/test/<string:parameter>'
        self.assertEqual(extract_path(path), '/test/{parameter}')

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<string:other>/'
        self.assertEqual(extract_path(path), '/test/{parameter}/{other}/')


class ExtractPathParamsTestCase(TestCase):
    def test_extract_static_path(self):
        path = '/test'
        self.assertEqual(extract_path_params(path), {})

    def test_extract_single_simple_parameter(self):
        path = '/test/<parameter>'
        self.assertEqual(extract_path_params(path), {
            'parameter': {
                'name': 'parameter',
                'type': 'string',
                'in': 'path',
                'required': True
            }
        })

    def test_single_int_parameter(self):
        path = '/test/<int:parameter>'
        self.assertEqual(extract_path_params(path), {
            'parameter': {
                'name': 'parameter',
                'type': 'integer',
                'in': 'path',
                'required': True
            }
        })

    def test_single_float_parameter(self):
        path = '/test/<float:parameter>'
        self.assertEqual(extract_path_params(path), {
            'parameter': {
                'name': 'parameter',
                'type': 'number',
                'in': 'path',
                'required': True
            }
        })

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<int:other>/'
        self.assertEqual(extract_path_params(path), {
            'parameter': {
                'name': 'parameter',
                'type': 'string',
                'in': 'path',
                'required': True
            },
            'other': {
                'name': 'other',
                'type': 'integer',
                'in': 'path',
                'required': True
            }
        })

    # def test_extract_registered_converters(self):
    #     class ListConverter(BaseConverter):
    #         def to_python(self, value):
    #             return value.split(',')

    #         def to_url(self, values):
    #             return ','.join(super(ListConverter, self).to_url(value) for value in values)

    #     self.app.url_map.converters['list'] = ListConverter

    #     path = '/test/<list:parameters>'
    #     with self.context():
    #         self.assertEqual(extract_path_params(path), [{
    #             'name': 'parameters',
    #             'type': 'number',
    #             'in': 'path',
    #             'required': True
    #         }])


class ParseDocstringTest(TestCase):
    def test_empty(self):
        def without_doc():
            pass

        parsed = parse_docstring(without_doc)

        self.assertIsNone(parsed['raw'])
        self.assertIsNone(parsed['summary'])
        self.assertIsNone(parsed['details'])
        self.assertIsNone(parsed['returns'])
        self.assertEqual(parsed['raises'], {})
        self.assertEqual(parsed['params'], [])

    def test_single_line(self):
        def func():
            '''Some summary'''
            pass

        parsed = parse_docstring(func)

        self.assertEqual(parsed['raw'], 'Some summary')
        self.assertEqual(parsed['summary'], 'Some summary')
        self.assertIsNone(parsed['details'])
        self.assertIsNone(parsed['returns'])
        self.assertEqual(parsed['raises'], {})
        self.assertEqual(parsed['params'], [])

    def test_multi_line(self):
        def func():
            '''
            Some summary
            Some details
            '''
            pass

        parsed = parse_docstring(func)

        self.assertEqual(parsed['raw'], 'Some summary\nSome details')
        self.assertEqual(parsed['summary'], 'Some summary')
        self.assertEqual(parsed['details'], 'Some details')
        self.assertIsNone(parsed['returns'])
        self.assertEqual(parsed['raises'], {})
        self.assertEqual(parsed['params'], [])

    def test_multi_line_and_dot(self):
        def func():
            '''
            Some summary. bla bla
            Some details
            '''
            pass

        parsed = parse_docstring(func)

        self.assertEqual(parsed['raw'], 'Some summary. bla bla\nSome details')
        self.assertEqual(parsed['summary'], 'Some summary')
        self.assertEqual(parsed['details'], 'bla bla\nSome details')
        self.assertIsNone(parsed['returns'])
        self.assertEqual(parsed['raises'], {})
        self.assertEqual(parsed['params'], [])

    def test_raises(self):
        def func():
            '''
            Some summary.
            :raises SomeException: in case of something
            '''
            pass

        parsed = parse_docstring(func)

        self.assertEqual(parsed['raw'], 'Some summary.\n:raises SomeException: in case of something')
        self.assertEqual(parsed['summary'], 'Some summary')
        self.assertIsNone(parsed['details'])
        self.assertIsNone(parsed['returns'])
        self.assertEqual(parsed['params'], [])
        self.assertEqual(parsed['raises'], {
            'SomeException': 'in case of something'
        })
