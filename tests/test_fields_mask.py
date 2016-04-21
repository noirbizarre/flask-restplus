# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from flask_restplus import mask, Api, Resource, fields, marshal, Mask

from . import TestCase


class MaskMixin(object):
    def test_empty_mask(self):
        self.assertEqual(Mask(''), {})

    def test_one_field(self):
        self.assertEqual(Mask('field_name'), {'field_name': True})

    def test_multiple_field(self):
        mask = Mask('field1, field2, field3')
        self.assertDataEqual(mask, {
            'field1': True,
            'field2': True,
            'field3': True,
        })

    def test_nested_fields(self):
        parsed = Mask('nested{field1,field2}')
        expected = {
            'nested': {
                'field1': True,
                'field2': True,
            }
        }
        self.assertEqual(parsed, expected)

    def test_complex(self):
        parsed = Mask('field1, nested{field, sub{subfield}}, field2')
        expected = {
            'field1': True,
            'nested': {
                'field': True,
                'sub': {
                    'subfield': True,
                }
            },
            'field2': True,
        }
        self.assertDataEqual(parsed, expected)

    def test_star(self):
        parsed = Mask('nested{field1,field2},*')
        expected = {
            'nested': {
                'field1': True,
                'field2': True,
            },
            '*': True,
        }
        self.assertDataEqual(parsed, expected)

    def test_order(self):
        parsed = Mask('f_3, nested{f_1, f_2, f_3}, f_2, f_1')
        expected = OrderedDict([
            ('f_3', True),
            ('nested', OrderedDict([
                ('f_1', True),
                ('f_2', True),
                ('f_3', True),
            ])),
            ('f_2', True),
            ('f_1', True),
        ])
        self.assertEqual(parsed, expected)

    def test_missing_closing_bracket(self):
        with self.assertRaises(mask.ParseError):
            Mask('nested{')

    def test_consecutive_coma(self):
        with self.assertRaises(mask.ParseError):
            Mask('field,,')

    def test_coma_before_bracket(self):
        with self.assertRaises(mask.ParseError):
            Mask('field,{}')

    def test_coma_after_bracket(self):
        with self.assertRaises(mask.ParseError):
            Mask('nested{,}')

    def test_unexpected_opening_bracket(self):
        with self.assertRaises(mask.ParseError):
            Mask('{{field}}')

    def test_unexpected_closing_bracket(self):
        with self.assertRaises(mask.ParseError):
            Mask('{field}}')

    def test_support_colons(self):
        self.assertEqual(Mask('field:name'), {'field:name': True})

    def test_support_dash(self):
        self.assertEqual(Mask('field-name'), {'field-name': True})

    def test_support_underscore(self):
        self.assertEqual(Mask('field_name'), {'field_name': True})


class MaskUnwrapped(MaskMixin, TestCase):
    def parse(self, value):
        return Mask(value)


class MaskWrapped(MaskMixin, TestCase):
    def parse(self, value):
        return Mask('{' + value + '}')


class DObject(object):
    '''A dead simple object built from a dictionnary (no recursion)'''
    def __init__(self, data):
        self.__dict__.update(data)


person_fields = {
    'name': fields.String,
    'age': fields.Integer
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

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, family_fields), data)

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

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, family_fields), data)

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

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, root), data)

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

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, family_fields), data)

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

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, family_fields), data)

    def test_list_fields_with_nested_inherited(self):
        api = Api(self.app)

        person = api.model('Person', {
            'name': fields.String,
            'age': fields.Integer
        })
        child = api.inherit('Child', person, {
            'attr': fields.String
        })

        family = api.model('Family', {
            'children': fields.List(fields.Nested(child))
        })

        result = mask.apply(family.resolved, 'children{name,attr}')

        data = {'children': [
            {'name': 'John', 'age': 5, 'attr': 'value-john'},
            {'name': 'Jane', 'age': 42, 'attr': 'value-jane'},
        ]}
        expected = {'children': [
            {'name': 'John', 'attr': 'value-john'},
            {'name': 'Jane', 'attr': 'value-jane'},
        ]}

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, family), data)

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

        self.assertDataEqual(marshal(data, result), expected)
        # Should leave th original mask untouched
        self.assertDataEqual(marshal(data, family_fields), data)

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

    def test_mask_error_on_simple_fields(self):
        model = {
            'name': fields.String,
        }

        with self.assertRaises(mask.MaskError):
            mask.apply(model, 'name{notpossible}')

    def test_mask_error_on_list_field(self):
        model = {
            'nested': fields.List(fields.String)
        }

        with self.assertRaises(mask.MaskError):
            mask.apply(model, 'nested{notpossible}')


class MaskAPI(TestCase):
    def test_marshal_with_honour_field_mask_header(self):
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

    def test_marshal_with_honour_complex_field_mask_header(self):
        api = Api(self.app)

        person = api.model('Person', person_fields)
        child = api.inherit('Child', person, {
            'attr': fields.String
        })

        family = api.model('Family', {
            'father': fields.Nested(person),
            'mother': fields.Nested(person),
            'children': fields.List(fields.Nested(child)),
            'free': fields.List(fields.Raw),
        })

        house = api.model('House', {
            'family': fields.Nested(family, attribute='people')
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(house)
            def get(self):
                return {'people': {
                    'father': {'name': 'John', 'age': 42},
                    'mother': {'name': 'Jane', 'age': 42},
                    'children': [
                        {'name': 'Jack', 'age': 5, 'attr': 'value-1'},
                        {'name': 'Julie', 'age': 7, 'attr': 'value-2'},
                    ],
                    'free': [
                        {'key-1': '1-1', 'key-2': '1-2'},
                        {'key-1': '2-1', 'key-2': '2-2'},
                    ]
                }}

        data = self.get_json('/test/', headers={
            'X-Fields': 'family{father{name},mother{age},children{name,attr},free{key-2}}'
        })
        expected = {'family': {
            'father': {'name': 'John'},
            'mother': {'age': 42},
            'children': [{'name': 'Jack', 'attr': 'value-1'}, {'name': 'Julie', 'attr': 'value-2'}],
            'free': [{'key-2': '1-2'}, {'key-2': '2-2'}]
        }}
        self.assertEqual(data, expected)

    def test_marshal_honour_field_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        })

        data = {
            'name': 'John Doe',
            'age': 42,
            'boolean': True
        }

        result = api.marshal(data, model, mask='{name,age}')

        self.assertEqual(result, {
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

    def test_marshal_with_honour_default_model_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        }, mask='{name,age}')

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
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

    def test_marshal_with_honour_header_field_mask_with_default_model_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        }, mask='{name,age}')

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
            'X-Fields': '{name}'
        })
        self.assertEqual(data, {
            'name': 'John Doe',
        })

    def test_marshal_with_honour_header_default_mask_with_default_model_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        }, mask='{name,boolean}')

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model, mask='{name}')
            def get(self):
                return {
                    'name': 'John Doe',
                    'age': 42,
                    'boolean': True
                }

        data = self.get_json('/test/')
        self.assertEqual(data, {
            'name': 'John Doe',
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

    def test_marshal_with_honour_header_field_mask_with_default_mask_and_default_model_mask(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        }, mask='{name,boolean}')

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

    def test_marshal_does_not_hit_unrequired_attributes(self):
        api = Api(self.app)

        model = api.model('Person', {
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

    def test_marshal_handle_inheritance(self):
        api = Api(self.app)

        person = api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = api.inherit('Child', person, {
            'extra': fields.String,
        })

        data = {
            'name': 'John Doe',
            'age': 42,
            'extra': 'extra'
        }

        values = (
            ('name', {'name': 'John Doe'}),
            ('name,extra', {'name': 'John Doe', 'extra': 'extra'}),
            ('extra', {'extra': 'extra'}),
        )

        for mask, expected in values:
            result = marshal(data, child, mask=mask)
            self.assertEqual(result, expected)

    def test_marshal_with_handle_polymorph(self):
        api = Api(self.app)

        parent = api.model('Person', {
            'name': fields.String,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        class Child1(object):
            name = 'child1'
            extra1 = 'extra1'

        class Child2(object):
            name = 'child2'
            extra2 = 'extra2'

        mapping = {
            Child1: child1,
            Child2: child2
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        @api.route('/thing-1/')
        class Thing1Resource(Resource):
            @api.marshal_with(thing)
            def get(self):
                return {'owner': Child1()}

        @api.route('/thing-2/')
        class Thing2Resource(Resource):
            @api.marshal_with(thing)
            def get(self):
                return {'owner': Child2()}

        data = self.get_json('/thing-1/', headers={
            'X-Fields': 'owner{name}'
        })

        self.assertEqual(data, {
            'owner': {'name': 'child1'},
        })

        data = self.get_json('/thing-1/', headers={
            'X-Fields': 'owner{extra1}'
        })

        self.assertEqual(data, {
            'owner': {'extra1': 'extra1'},
        })

        data = self.get_json('/thing-2/', headers={
            'X-Fields': 'owner{name}'
        })

        self.assertEqual(data, {
            'owner': {'name': 'child2'},
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
                pass

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

    def test_marshal_with_expose_default_model_mask_header(self):
        api = Api(self.app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
            'boolean': fields.Boolean,
        }, mask='{name,age}')

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                pass

        specs = self.get_specs()
        definition = specs['definitions']['Test']
        self.assertIn('x-mask', definition)
        self.assertEqual(definition['x-mask'], '{name,age}')
