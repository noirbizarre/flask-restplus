# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from flask import Flask

from flask.ext.restplus import fields, reqparse, Api
from flask.ext.restplus.swagger import utils

from . import TestCase


class ExtractPathTestCase(unittest.TestCase):
    def test_extract_static_path(self):
        path = '/test'
        self.assertEqual(utils.extract_path(path), '/test')

    def test_extract_path_with_a_single_simple_parameter(self):
        path = '/test/<parameter>'
        self.assertEqual(utils.extract_path(path), '/test/{parameter}')

    def test_extract_path_with_a_single_typed_parameter(self):
        path = '/test/<string:parameter>'
        self.assertEqual(utils.extract_path(path), '/test/{parameter}')

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<string:other>/'
        self.assertEqual(utils.extract_path(path), '/test/{parameter}/{other}/')


class ExtractPathParamsTestCase(TestCase):
    def test_extract_static_path(self):
        path = '/test'
        self.assertEqual(utils.extract_path_params(path), [])

    def test_extract_single_simple_parameter(self):
        path = '/test/<parameter>'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'string',
            'paramType': 'path',
            'required': True
        }])

    def test_single_int_parameter(self):
        path = '/test/<int:parameter>'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'integer',
            'paramType': 'path',
            'required': True
        }])

    def test_single_float_parameter(self):
        path = '/test/<float:parameter>'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'number',
            'paramType': 'path',
            'required': True
        }])

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<int:other>/'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'string',
            'paramType': 'path',
            'required': True
        }, {
            'name': 'other',
            'type': 'integer',
            'paramType': 'path',
            'required': True
        }])

    # def test_extract_registered_converters(self):
    #     class ListConverter(BaseConverter):
    #         def to_python(self, value):
    #             return value.split(',')

    #         def to_url(self, values):
    #             return ','.join(super(ListConverter, self).to_url(value) for value in values)

    #     self.app.url_map.converters['list'] = ListConverter

    #     path = '/test/<list:parameters>'
    #     with self.context():
    #         self.assertEqual(utils.extract_path_params(path), [{
    #             'name': 'parameters',
    #             'type': 'number',
    #             'paramType': 'path',
    #             'required': True
    #         }])


class FieldToPropertyTestCase(TestCase):
    def test_unknown_field(self):
        prop = utils.field_to_property(None)
        self.assertEqual(prop, {'type': 'string'})

    def test_simple_raw_field(self):
        prop = utils.field_to_property(fields.Raw)
        self.assertEqual(prop, {'type': 'string'})

    def test_raw_field_with_description(self):
        prop = utils.field_to_property(fields.Raw(description='A description'))
        self.assertEqual(prop, {'type': 'string', 'description': 'A description'})

    def test_raw_field_with_required(self):
        prop = utils.field_to_property(fields.Raw(required=True))
        self.assertEqual(prop, {'type': 'string', 'required': True})

    def test_raw_field_with_default(self):
        prop = utils.field_to_property(fields.Raw(default='aaa'))
        self.assertEqual(prop, {'type': 'string', 'defaultValue': 'aaa'})

    def test_simple_string_field(self):
        prop = utils.field_to_property(fields.String)
        self.assertEqual(prop, {'type': 'string'})

    def test_string_field_with_description(self):
        prop = utils.field_to_property(fields.String(description='A description'))
        self.assertEqual(prop, {'type': 'string', 'description': 'A description'})

    def test_string_field_with_required(self):
        prop = utils.field_to_property(fields.String(required=True))
        self.assertEqual(prop, {'type': 'string', 'required': True})

    def test_string_field_with_enum(self):
        prop = utils.field_to_property(fields.String(enum=['A', 'B', 'C']))
        self.assertEqual(prop, {'type': 'string', 'enum': ['A', 'B', 'C']})

    def test_string_field_with_default(self):
        prop = utils.field_to_property(fields.String(default='aaa'))
        self.assertEqual(prop, {'type': 'string', 'defaultValue': 'aaa'})

    def test_simple_integer_field(self):
        prop = utils.field_to_property(fields.Integer)
        self.assertEqual(prop, {'type': 'integer'})

    def test_integer_field_with_description(self):
        prop = utils.field_to_property(fields.Integer(description='A description'))
        self.assertEqual(prop, {'type': 'integer', 'description': 'A description'})

    def test_integer_field_with_required(self):
        prop = utils.field_to_property(fields.Integer(required=True))
        self.assertEqual(prop, {'type': 'integer', 'required': True})

    def test_integer_field_with_min_max(self):
        prop = utils.field_to_property(fields.Integer(min=0, max=5))
        self.assertEqual(prop, {'type': 'integer', 'minimum': 0, 'maximum': 5})

    def test_integer_field_with_default(self):
        prop = utils.field_to_property(fields.Integer(default=42))
        self.assertEqual(prop, {'type': 'integer', 'defaultValue': 42})

    def test_simple_boolean_field(self):
        prop = utils.field_to_property(fields.Boolean)
        self.assertEqual(prop, {'type': 'boolean'})

    def test_boolean_field_with_description(self):
        prop = utils.field_to_property(fields.Boolean(description='A description'))
        self.assertEqual(prop, {'type': 'boolean', 'description': 'A description'})

    def test_boolean_field_with_required(self):
        prop = utils.field_to_property(fields.Boolean(required=True))
        self.assertEqual(prop, {'type': 'boolean', 'required': True})

    def test_boolean_field_with_default(self):
        prop = utils.field_to_property(fields.Boolean(default=True))
        self.assertEqual(prop, {'type': 'boolean', 'defaultValue': True})

    def test_simple_float_field(self):
        prop = utils.field_to_property(fields.Float)
        self.assertEqual(prop, {'type': 'number'})

    def test_float_field_with_description(self):
        prop = utils.field_to_property(fields.Float(description='A description'))
        self.assertEqual(prop, {'type': 'number', 'description': 'A description'})

    def test_float_field_with_required(self):
        prop = utils.field_to_property(fields.Float(required=True))
        self.assertEqual(prop, {'type': 'number', 'required': True})

    def test_float_field_with_min_max(self):
        prop = utils.field_to_property(fields.Float(min=0, max=5))
        self.assertEqual(prop, {'type': 'number', 'minimum': 0, 'maximum': 5})

    def test_float_field_with_default(self):
        prop = utils.field_to_property(fields.Float(default=0.5))
        self.assertEqual(prop, {'type': 'number', 'defaultValue': 0.5})

    def test_simple_fixed_field(self):
        prop = utils.field_to_property(fields.Fixed)
        self.assertEqual(prop, {'type': 'number'})

    def test_fixed_field_with_description(self):
        prop = utils.field_to_property(fields.Fixed(description='A description'))
        self.assertEqual(prop, {'type': 'number', 'description': 'A description'})

    def test_fixed_field_with_required(self):
        prop = utils.field_to_property(fields.Fixed(required=True))
        self.assertEqual(prop, {'type': 'number', 'required': True})

    def test_fixed_field_with_min_max(self):
        prop = utils.field_to_property(fields.Fixed(min=0, max=5))
        self.assertEqual(prop, {'type': 'number', 'minimum': 0, 'maximum': 5})

    def test_fixed_field_with_default(self):
        prop = utils.field_to_property(fields.Fixed(default=0.5))
        self.assertEqual(prop, {'type': 'number', 'defaultValue': 0.5})

    def test_simple_arbitrary_field(self):
        prop = utils.field_to_property(fields.Arbitrary)
        self.assertEqual(prop, {'type': 'number'})

    def test_arbitrary_field_with_description(self):
        prop = utils.field_to_property(fields.Arbitrary(description='A description'))
        self.assertEqual(prop, {'type': 'number', 'description': 'A description'})

    def test_arbitrary_field_with_required(self):
        prop = utils.field_to_property(fields.Arbitrary(required=True))
        self.assertEqual(prop, {'type': 'number', 'required': True})

    def test_arbitrary_field_with_min_max(self):
        prop = utils.field_to_property(fields.Arbitrary(min=0, max=5))
        self.assertEqual(prop, {'type': 'number', 'minimum': 0, 'maximum': 5})

    def test_arbitrary_field_with_default(self):
        prop = utils.field_to_property(fields.Arbitrary(default=0.5))
        self.assertEqual(prop, {'type': 'number', 'defaultValue': 0.5})

    def test_simple_datetime_field(self):
        prop = utils.field_to_property(fields.DateTime)
        self.assertEqual(prop, {'type': 'string', 'format': 'date-time'})

    def test_datetime_field_with_required(self):
        prop = utils.field_to_property(fields.DateTime(required=True))
        self.assertEqual(prop, {'type': 'string', 'format': 'date-time', 'required': True})

    def test_datetime_field_with_description(self):
        prop = utils.field_to_property(fields.DateTime(description='A description'))
        self.assertEqual(prop, {'type': 'string', 'format': 'date-time', 'description': 'A description'})

    def test_datetime_field_with_default(self):
        prop = utils.field_to_property(fields.DateTime(default='2014-08-25'))
        self.assertEqual(prop, {'type': 'string', 'format': 'date-time', 'defaultValue': '2014-08-25'})

    def test_list_field(self):
        prop = utils.field_to_property(fields.List(fields.String))
        self.assertEqual(prop, {'type': 'array', 'items': {'type': 'string'}})

    def test_nested_field(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        prop = utils.field_to_property(fields.Nested(nested_fields))
        self.assertEqual(prop, {'$ref': 'NestedModel', 'required': True})

    def test_nested_field_with_description(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        prop = utils.field_to_property(fields.Nested(nested_fields, description='A description'))
        self.assertEqual(prop, {'$ref': 'NestedModel', 'required': True, 'description': 'A description'})

    def test_nullable_nested_field(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        prop = utils.field_to_property(fields.Nested(nested_fields, allow_null=True))
        self.assertEqual(prop, {'$ref': 'NestedModel'})

    def test_nested_field_as_list(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        prop = utils.field_to_property(api.as_list(fields.Nested(nested_fields)))
        self.assertEqual(prop, {'type': 'array', 'items': {'$ref': 'NestedModel'}})

    def test_nested_field_as_list_is_reusable(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})

        prop = utils.field_to_property(api.as_list(fields.Nested(nested_fields)))
        self.assertEqual(prop, {'type': 'array', 'items': {'$ref': 'NestedModel'}})

        prop = utils.field_to_property(fields.Nested(nested_fields))
        self.assertEqual(prop, {'$ref': 'NestedModel', 'required': True})

    def test_simple_formatted_string_field(self):
        prop = utils.field_to_property(fields.FormattedString('Hello {name}'))
        self.assertEqual(prop, {'type': 'string'})

    def test_formatted_string_field_with_description(self):
        prop = utils.field_to_property(fields.FormattedString('Hello {name}', description='A description'))
        self.assertEqual(prop, {'type': 'string', 'description': 'A description'})

    def test_formatted_string_field_with_required(self):
        prop = utils.field_to_property(fields.FormattedString('Hello {name}', required=True))
        self.assertEqual(prop, {'type': 'string', 'required': True})

    def test_simple_url_field(self):
        prop = utils.field_to_property(fields.Url('endpoint'))
        self.assertEqual(prop, {'type': 'string'})

    def test_url_field_with_description(self):
        prop = utils.field_to_property(fields.Url('endpoint', description='A description'))
        self.assertEqual(prop, {'type': 'string', 'description': 'A description'})

    def test_url_field_with_required(self):
        prop = utils.field_to_property(fields.Url('endpoint', required=True))
        self.assertEqual(prop, {'type': 'string', 'required': True})

    def test_custom_field(self):
        class Custom(fields.Raw):
            pass
        prop = utils.field_to_property(Custom)
        self.assertEqual(prop, {'type': 'string'})

    def test_custom_field_with_description(self):
        class Custom(fields.Raw):
            pass
        prop = utils.field_to_property(Custom(description='A description'))
        self.assertEqual(prop, {'type': 'string', 'description': 'A description'})


class ParserToParamsTestCase(unittest.TestCase):
    def test_empty_parser(self):
        parser = reqparse.RequestParser()
        self.assertEqual(utils.parser_to_params(parser), {})

    def test_primitive_types(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, help='Some integer')
        parser.add_argument('str', type=str, help='Some string')
        self.assertEqual(utils.parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'paramType': 'query',
                'description': 'Some integer',
            },
            'str':  {
                'type': 'string',
                'paramType': 'query',
                'description': 'Some string',
            }
        })

    def test_unknown_type(self):
        parser = reqparse.RequestParser()
        unknown = lambda v: v
        parser.add_argument('unknown', type=unknown)
        self.assertEqual(utils.parser_to_params(parser), {
            'unknown':  {
                'type': 'string',
                'paramType': 'query',
            }
        })

    def test_required(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, required=True)
        self.assertEqual(utils.parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'paramType': 'query',
                'required': True,
            }
        })

    def test_default(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, default=5)
        self.assertEqual(utils.parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'paramType': 'query',
                'defaultValue': 5,
            }
        })

    def test_location(self):
        parser = reqparse.RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_form', type=int, location='form')
        parser.add_argument('in_json', type=str, location='json')
        parser.add_argument('in_values', type=int, location='values')
        parser.add_argument('in_query', type=int, location='args')
        parser.add_argument('in_headers', type=int, location='headers')
        parser.add_argument('in_cookie', type=int, location='cookie')
        self.assertEqual(utils.parser_to_params(parser), {
            'default': {
                'type': 'integer',
                'paramType': 'query',
            },
            'in_form': {
                'type': 'integer',
                'paramType': 'form',
            },
            'in_json': {
                'type': 'string',
                'paramType': 'body',
            },
            'in_values': {
                'type': 'integer',
                'paramType': 'query',
            },
            'in_query': {
                'type': 'integer',
                'paramType': 'query',
            },
            'in_headers': {
                'type': 'integer',
                'paramType': 'header',
            },
        })

    def test_models(self):
        app = Flask(__name__)
        api = Api(app)
        todo_fields = api.model('Todo', {
            'task': fields.String(required=True, description='The task details')
        })
        parser = reqparse.RequestParser()
        parser.add_argument('todo', type=todo_fields)
        self.assertEqual(utils.parser_to_params(parser), {
            'todo': {
                'type': 'Todo',
                'paramType': 'body',
            },
        })

    def test_lists(self):
        parser = reqparse.RequestParser()
        parser.add_argument('int', type=int, action='append')
        self.assertEqual(utils.parser_to_params(parser), {
            'int': {
                'type': 'integer',
                'paramType': 'query',
                'allowMultiple': True,
            }
        })
