# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from flask_restplus import mask, Api, Resource, fields, marshal

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

    def test_star(self):
        parsed = mask.parse('nested{field1,field2},*')
        expected = [mask.Nested('nested', ['field1', 'field2']), '*']
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


def ordered_to_dict(o):
    return json.loads(json.dumps(o))


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

    def test_star_only(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '*')
        self.assertEqual(result, data)

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

    def test_nested_with_start(self):
        data = {
            'nested': {
                'integer': 42,
                'string': 'a string',
                'boolean': True,
            },
            'other': 'value',
        }
        result = mask.apply(data, '{nested{integer},*}')
        self.assertEqual(result, {'nested': {'integer': 42}, 'other': 'value'})

    def test_nested_fields_when_none(self):
        data = {'nested': None}
        result = mask.apply(data, '{nested{integer}}')
        self.assertEqual(result, {'nested': None})

    def test_raw_api_fields(self):
        family_fields = {
            'father': fields.Raw,
            'mother': fields.Raw,
        }

        result = mask.apply(family_fields, 'father{name},mother{age}')

        data = {
            'father': {'name': 'John', 'age': 42},
            'mother': {'name': 'Jane', 'age': 42},
        }
        expected = {'father': {'name': 'John'}, 'mother': {'age': 42}}

        self.assertEqual(ordered_to_dict(marshal(data, result)), expected)
        # Should leave th original mask untouched
        self.assertEqual(ordered_to_dict(marshal(data, family_fields)), data)

    def test_nested_api_fields(self):
        family_fields = {
            'father': fields.Nested(person_fields),
            'mother': fields.Nested(person_fields),
        }

        result = mask.apply(family_fields, 'father{name},mother{age}')
        self.assertEqual(set(result.keys()), set(['father', 'mother']))
        self.assertIsInstance(result['father'], fields.Nested)
        self.assertEqual(set(result['father'].nested.keys()), set(['name']))
        self.assertIsInstance(result['mother'], fields.Nested)
        self.assertEqual(set(result['mother'].nested.keys()), set(['age']))

        data = {
            'father': {'name': 'John', 'age': 42},
            'mother': {'name': 'Jane', 'age': 42},
        }
        expected = {'father': {'name': 'John'}, 'mother': {'age': 42}}

        self.assertEqual(ordered_to_dict(marshal(data, result)), expected)
        # Should leave th original mask untouched
        self.assertEqual(ordered_to_dict(marshal(data, family_fields)), data)

    def test_multiple_nested_api_fields(self):
        level_2 = {'nested_2': fields.Nested(person_fields)}
        level_1 = {'nested_1': fields.Nested(level_2)}
        root = {'nested': fields.Nested(level_1)}

        result = mask.apply(root, 'nested{nested_1{nested_2{name}}}')
        self.assertEqual(set(result.keys()), set(['nested']))
        self.assertIsInstance(result['nested'], fields.Nested)
        self.assertEqual(set(result['nested'].nested.keys()), set(['nested_1']))

        data = {
            'nested': {
                'nested_1': {
                    'nested_2': {'name': 'John', 'age': 42}
                }
            }
        }
        expected = {
            'nested': {
                'nested_1': {
                    'nested_2': {'name': 'John'}
                }
            }
        }

        self.assertEqual(ordered_to_dict(marshal(data, result)), expected)
        # Should leave th original mask untouched
        self.assertEqual(ordered_to_dict(marshal(data, root)), data)

    def test_list_fields_with_simple_field(self):
        family_fields = {
            'name': fields.String,
            'members': fields.List(fields.String)
        }

        result = mask.apply(family_fields, 'members')
        self.assertEqual(set(result.keys()), set(['members']))
        self.assertIsInstance(result['members'], fields.List)
        self.assertIsInstance(result['members'].container, fields.String)

        data = {'name': 'Doe', 'members': ['John', 'Jane']}
        expected = {'members': ['John', 'Jane']}

        self.assertEqual(ordered_to_dict(marshal(data, result)), expected)
        # Should leave th original mask untouched
        self.assertEqual(ordered_to_dict(marshal(data, family_fields)), data)

    def test_list_fields_with_nested(self):
        family_fields = {
            'members': fields.List(fields.Nested(person_fields))
        }

        result = mask.apply(family_fields, 'members{name}')
        self.assertEqual(set(result.keys()), set(['members']))
        self.assertIsInstance(result['members'], fields.List)
        self.assertIsInstance(result['members'].container, fields.Nested)
        self.assertEqual(set(result['members'].container.nested.keys()), set(['name']))

        data = {'members': [
            {'name': 'John', 'age': 42},
            {'name': 'Jane', 'age': 42},
        ]}
        expected = {'members': [{'name': 'John'}, {'name': 'Jane'}]}

        self.assertEqual(ordered_to_dict(marshal(data, result)), expected)
        # Should leave th original mask untouched
        self.assertEqual(ordered_to_dict(marshal(data, family_fields)), data)

    def test_list_fields_with_raw(self):
        family_fields = {
            'members': fields.List(fields.Raw)
        }

        result = mask.apply(family_fields, 'members{name}')

        data = {'members': [
            {'name': 'John', 'age': 42},
            {'name': 'Jane', 'age': 42},
        ]}
        expected = {'members': [{'name': 'John'}, {'name': 'Jane'}]}

        self.assertEqual(ordered_to_dict(marshal(data, result)), expected)
        # Should leave th original mask untouched
        self.assertEqual(ordered_to_dict(marshal(data, family_fields)), data)

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

    def test_missing_field_none_by_default(self):
        result = mask.apply({}, '{integer}')
        self.assertEqual(result, {'integer': None})

    def test_missing_field_skipped(self):
        result = mask.apply({}, '{integer}', skip=True)
        self.assertEqual(result, {})

    def test_missing_nested_field_skipped(self):
        result = mask.apply({}, 'nested{integer}', skip=True)
        self.assertEqual(result, {})


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

    def test_marshal_with_honour_default_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model, mask='{name,age}')
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        data = self.get_json('/test/')
        self.assertEqual(data, {
            'name': 'John Doe',
            'age': 42,
        })

    def test_marshal_with_honour_header_field_mask_with_default_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model, mask='{name,age}')
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        data = self.get_json('/test/', headers={
            'X-Fields': '{name}'
        })
        self.assertEqual(data, {
            'name': 'John Doe',
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

    def test_marshal_with_skip_missing_fields(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                }

        data = self.get_json('/test/', headers={
            'X-Fields': '{name,missing}'
        })
        self.assertEqual(data, {
            'name': 'John Doe',
        })

    def test_raise_400_on_invalid_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                pass

        with self.app.test_client() as client:
            response = client.get('/test/', headers={'X-Fields': 'name{,missing}'})
            self.assertEqual(response.status_code, 400)
            self.assertEquals(response.content_type, 'application/json')


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
        self.assertNotIn('default', param)

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

    def test_marshal_with_expose_default_mask_header(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model, mask='{name,age}')
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
        self.assertEqual(param['default'], '{name,age}')
        self.assertEqual(param['in'], 'header')
        self.assertNotIn('required', param)
