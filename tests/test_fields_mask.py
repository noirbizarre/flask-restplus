# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from flask.ext.restplus import mask, Api, Resource, fields

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


person_fields = {
    'name': fields.String,
    'age': fields.Integer
}

family_fields = {
    'father': fields.Nested(person_fields),
    'mother': fields.Nested(person_fields),
    'children': fields.List(fields.Nested(person_fields))
}


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

    def test_with_ordered_dict(self):
        data = OrderedDict({
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

    def test_nested_api_fields(self):
        result = mask.apply(family_fields, 'father{name},children{age}')
        self.assertEqual(set(result.keys()), set(['father', 'children']))
        self.assertIsInstance(result['father'], fields.Nested)
        self.assertEqual(set(result['father'].nested.keys()), set(['name']))
        self.assertIsInstance(result['children'], fields.List)
        self.assertIsInstance(result['children'].container, fields.Nested)
        self.assertEqual(set(result['children'].container.nested.keys()), set(['age']))

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


class MaskAPI(TestCase):
    def test_marshal_with_honour_field_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        data = self.get_json('/test/', headers={
            'X-Fields': '{name,age}'
        })
        self.assertEqual(data, {
            'name': 'John Doe',
            'age': 42,
        })

    def test_marshal_with_honour_field_mask_list(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return [{
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }, {
                    'name': 'Jane Doe',
                    'age': 33,
                    'boolean': False
                }]

        data = self.get_json('/test/', headers={
            'X-Fields': '{name,age}'
        })
        self.assertEqual(data, [{
            'name': 'John Doe',
            'age': 42,
        }, {
            'name': 'Jane Doe',
            'age': 33,
        }])

    def test_marshal_honour_field_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            def get(self):
                return api.marshal({
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }, model)

        data = self.get_json('/test/', headers={
            'X-Fields': '{name,age}'
        })
        self.assertEqual(data, {
            'name': 'John Doe',
            'age': 42,
        })

    def test_marshal_with_honour_custom_field_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        with self.settings(RESTPLUS_MASK_HEADER='X-Mask'):
            data = self.get_json('/test/', headers={
                'X-Mask': '{name,age}'
            })

        self.assertEqual(data, {
            'name': 'John Doe',
            'age': 42,
        })

    def test_marshal_honour_custom_field_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            def get(self):
                return api.marshal({
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }, model)

        with self.settings(RESTPLUS_MASK_HEADER='X-Mask'):
            data = self.get_json('/test/', headers={
                'X-Mask': '{name,age}'
            })

        self.assertEqual(data, {
            'name': 'John Doe',
            'age': 42,
        })

    def test_marshal_does_not_hit_unrequired_attributes(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        class Person(object):
            def __init__(self, name, age):
                self.name = name
                self.age = age

            @property
            def boolean(self):
                raise Exception()

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return Person('John Doe', 42)

        data = self.get_json('/test/', headers={
            'X-Fields': '{name,age}'
        })
        self.assertEqual(data, {
            'name': 'John Doe',
            'age': 42,
        })


class SwaggerMaskHeaderTest(TestCase):
    def test_marshal_with_expose_mask_header(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        specs = self.get_specs()
        op = specs['paths']['/test/']['get']

        self.assertIn('parameters', op)
        self.assertEqual(len(op['parameters']), 1)

        param = op['parameters'][0]

        self.assertEqual(param['name'], 'X-Fields')
        self.assertEqual(param['type'], 'string')
        self.assertEqual(param['format'], 'mask')
        self.assertEqual(param['in'], 'header')
        self.assertNotIn('required', param)

    def test_marshal_with_expose_custom_mask_header(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        with self.settings(RESTPLUS_MASK_HEADER='X-Mask'):
            specs = self.get_specs()

        op = specs['paths']['/test/']['get']
        self.assertIn('parameters', op)
        self.assertEqual(len(op['parameters']), 1)

        param = op['parameters'][0]
        self.assertEqual(param['name'], 'X-Mask')

    def test_marshal_with_disabling_mask_header(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        with self.settings(RESTPLUS_MASK_SWAGGER=False):
            specs = self.get_specs()

        op = specs['paths']['/test/']['get']

        self.assertNotIn('parameters', op)

    def test_is_only_exposed_on_marshal_with(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            def get(self):
                return api.marshal({
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }, model)

        specs = self.get_specs()
        op = specs['paths']['/test/']['get']

        self.assertNotIn('parameters', op)
