# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus.swagger import extract_path, extract_path_params, parse_docstring


class ExtractPathTest(object):
    def test_extract_static_path(self):
        path = '/test'
        assert extract_path(path) == '/test'

    def test_extract_path_with_a_single_simple_parameter(self):
        path = '/test/<parameter>'
        assert extract_path(path) == '/test/{parameter}'

    def test_extract_path_with_a_single_typed_parameter(self):
        path = '/test/<string:parameter>'
        assert extract_path(path) == '/test/{parameter}'

    def test_extract_path_with_a_single_typed_parameter_with_arguments(self):
        path = '/test/<string(length=2):parameter>'
        assert extract_path(path) == '/test/{parameter}'

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<string:other>/'
        assert extract_path(path) == '/test/{parameter}/{other}/'


class ExtractPathParamsTestCase(object):
    def test_extract_static_path(self):
        path = '/test'
        assert extract_path_params(path) == {}

    def test_extract_single_simple_parameter(self):
        path = '/test/<parameter>'
        assert extract_path_params(path) == {
            'parameter': {
                'name': 'parameter',
                'type': 'string',
                'in': 'path',
                'required': True
            }
        }

    def test_single_int_parameter(self):
        path = '/test/<int:parameter>'
        assert extract_path_params(path) == {
            'parameter': {
                'name': 'parameter',
                'type': 'integer',
                'in': 'path',
                'required': True
            }
        }

    def test_single_float_parameter(self):
        path = '/test/<float:parameter>'
        assert extract_path_params(path) == {
            'parameter': {
                'name': 'parameter',
                'type': 'number',
                'in': 'path',
                'required': True
            }
        }

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<int:other>/'
        assert extract_path_params(path) == {
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
        }

    def test_extract_parameter_with_arguments(self):
        path = '/test/<string(length=2):parameter>'
        assert extract_path_params(path) == {
            'parameter': {
                'name': 'parameter',
                'type': 'string',
                'in': 'path',
                'required': True
            }
        }

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


class ParseDocstringTest(object):
    def test_empty(self):
        def without_doc():
            pass

        parsed = parse_docstring(without_doc)

        assert parsed['raw'] is None
        assert parsed['summary'] is None
        assert parsed['details'] is None
        assert parsed['raises'] == {}

    def test_single_line(self):
        def func():
            '''Some summary'''
            pass

        parsed = parse_docstring(func)

        assert parsed['raw'] == 'Some summary'
        assert parsed['summary'] == 'Some summary'
        assert parsed['details'] is None
        assert parsed['raises'] == {}

    def test_multi_line(self):
        def func():
            '''
            Some summary
            Some more summary
            '''
            pass

        parsed = parse_docstring(func)

        assert parsed['raw'] == 'Some summary\nSome more summary'
        assert parsed['summary'] == 'Some summary\nSome more summary'
        assert parsed['details'] is None
        assert parsed['raises'] == {}

    def test_multi_paragraph(self):
        def func():
            '''
            Some summary. Some more summary

            Some details. Some more details

            Even more details
            '''
            pass

        parsed = parse_docstring(func)

        assert parsed['raw'] == 'Some summary. Some more summary\n\nSome details. Some more details\n\n' \
            'Even more details'
        assert parsed['summary'] == 'Some summary. Some more summary'
        assert parsed['details'] == 'Some details. Some more details\n\nEven more details'
        assert parsed['raises'] == {}

    def test_raises(self):
        def func():
            '''
            Some summary

            :raises SomeException: in case of something
            '''
            pass

        parsed = parse_docstring(func)

        assert parsed['raw'] == 'Some summary\n\n:raises SomeException: in case of something'
        assert parsed['summary'] == 'Some summary'
        assert parsed['details'] is None
        assert parsed['raises'] == {'SomeException': 'in case of something'}

    def test_sphinx(self):
        def func():
            '''
            Some summary

            :param id: The ID
            :type id: int
            :returns: Nothing
            :rtype: None
            '''
            pass

        parsed = parse_docstring(func)

        assert parsed['raw'] == 'Some summary\n\n:param id: The ID\n:type id: int\n:returns: Nothing\n:rtype: None'
        assert parsed['summary'] == 'Some summary'
        assert parsed['details'] is None
        assert parsed['raises'] == {}
