# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from flask import Flask
from werkzeug.datastructures import FileStorage

from flask_restplus import fields, reqparse, Api, SpecsError
from flask_restplus.swagger import extract_path, extract_path_params, parser_to_params

from . import TestCase


class ExtractPathTestCase(unittest.TestCase):
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




class ParserToParamsTestCase(unittest.TestCase):
    def test_empty_parser(self):
        parser = reqparse.RequestParser()
        self.assertEqual(parser_to_params(parser), {})

    def test_primitive_types(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, help='Some integer')
        parser.add_argument('str', type=str, help='Some string')
        self.assertEqual(parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'in': 'query',
                'description': 'Some integer',
            },
            'str': {
                'type': 'string',
                'in': 'query',
                'description': 'Some string',
            }
        })

    def test_unknown_type(self):
        parser = reqparse.RequestParser()
        unknown = lambda v: v
        parser.add_argument('unknown', type=unknown)
        self.assertEqual(parser_to_params(parser), {
            'unknown': {
                'type': 'string',
                'in': 'query',
            }
        })

    def test_required(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, required=True)
        self.assertEqual(parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'in': 'query',
                'required': True,
            }
        })

    def test_default(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, default=5)
        self.assertEqual(parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'in': 'query',
                'default': 5,
            }
        })

    def test_choices(self):
        parser = reqparse.RequestParser()
        parser.add_argument('string', type=str, choices=['a', 'b'])
        self.assertEqual(parser_to_params(parser), {
            'string': {
                'type': 'string',
                'in': 'query',
                'enum': ['a', 'b'],
                'collectionFormat': 'multi',
            }
        })

    def test_location(self):
        parser = reqparse.RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_values', type=int, location='values')
        parser.add_argument('in_query', type=int, location='args')
        parser.add_argument('in_headers', type=int, location='headers')
        parser.add_argument('in_cookie', type=int, location='cookie')
        self.assertEqual(parser_to_params(parser), {
            'default': {
                'type': 'integer',
                'in': 'query',
            },
            'in_values': {
                'type': 'integer',
                'in': 'query',
            },
            'in_query': {
                'type': 'integer',
                'in': 'query',
            },
            'in_headers': {
                'type': 'integer',
                'in': 'header',
            },
        })

    def test_location_json(self):
        parser = reqparse.RequestParser()
        parser.add_argument('in_json', type=str, location='json')
        self.assertEqual(parser_to_params(parser), {
            'in_json': {
                'type': 'string',
                'in': 'body',
            },
        })

    def test_location_form(self):
        parser = reqparse.RequestParser()
        parser.add_argument('in_form', type=int, location='form')
        self.assertEqual(parser_to_params(parser), {
            'in_form': {
                'type': 'integer',
                'in': 'formData',
            },
        })

    def test_location_files(self):
        parser = reqparse.RequestParser()
        parser.add_argument('in_files', type=FileStorage, location='files')
        self.assertEqual(parser_to_params(parser), {
            'in_files': {
                'type': 'file',
                'in': 'formData',
            },
        })

    def test_form_and_body_location(self):
        parser = reqparse.RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_form', type=int, location='form')
        parser.add_argument('in_json', type=str, location='json')
        with self.assertRaises(SpecsError) as cm:
            parser_to_params(parser)

        self.assertEqual(cm.exception.msg, "Can't use formData and body at the same time")

    def test_files_and_body_location(self):
        parser = reqparse.RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_files', type=FileStorage, location='files')
        parser.add_argument('in_json', type=str, location='json')
        with self.assertRaises(SpecsError) as cm:
            parser_to_params(parser)

        self.assertEqual(cm.exception.msg, "Can't use formData and body at the same time")

    def test_models(self):
        app = Flask(__name__)
        api = Api(app)
        todo_fields = api.model('Todo', {
            'task': fields.String(required=True, description='The task details')
        })
        parser = reqparse.RequestParser()
        parser.add_argument('todo', type=todo_fields)
        self.assertEqual(parser_to_params(parser), {
            'todo': {
                'type': 'Todo',
                'in': 'body',
            },
        })

    def test_lists(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, action='append')
        self.assertEqual(parser_to_params(parser), {
            'int': {
                'in': 'query',
                'items': True,
                'type': 'array',
                'items': {'type': 'integer'}
            }
        })
