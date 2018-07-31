# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest

from collections import OrderedDict

from flask_restplus import mask, Api, Resource, fields, marshal, Mask


def assert_data(tested, expected):
    '''Compare data without caring about order and type (dict vs. OrderedDict)'''
    tested = json.loads(json.dumps(tested))
    expected = json.loads(json.dumps(expected))
    assert tested == expected


class MaskMixin(object):

    def test_empty_mask(self):
        assert Mask('') == {}

    def test_one_field(self):
        assert Mask('field_name') == {'field_name': True}

    def test_multiple_field(self):
        mask = Mask('field1, field2, field3')
        assert_data(mask, {
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
        assert parsed == expected

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
        assert_data(parsed, expected)

    def test_star(self):
        parsed = Mask('nested{field1,field2},*')
        expected = {
            'nested': {
                'field1': True,
                'field2': True,
            },
            '*': True,
        }
        assert_data(parsed, expected)

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
        assert parsed == expected

    def test_missing_closing_bracket(self):
        with pytest.raises(mask.ParseError):
            Mask('nested{')

    def test_consecutive_coma(self):
        with pytest.raises(mask.ParseError):
            Mask('field,,')

    def test_coma_before_bracket(self):
        with pytest.raises(mask.ParseError):
            Mask('field,{}')

    def test_coma_after_bracket(self):
        with pytest.raises(mask.ParseError):
            Mask('nested{,}')

    def test_unexpected_opening_bracket(self):
        with pytest.raises(mask.ParseError):
            Mask('{{field}}')

    def test_unexpected_closing_bracket(self):
        with pytest.raises(mask.ParseError):
            Mask('{field}}')

    def test_support_colons(self):
        assert Mask('field:name') == {'field:name': True}

    def test_support_dash(self):
        assert Mask('field-name') == {'field-name': True}

    def test_support_underscore(self):
        assert Mask('field_name') == {'field_name': True}


class MaskUnwrappedTest(MaskMixin):
    def parse(self, value):
        return Mask(value)


class MaskWrappedTest(MaskMixin):
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


class ApplyMaskTest(object):
    def test_empty(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '{}')
        assert result == {}

    def test_single_field(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '{integer}')
        assert result == {'integer': 42}

    def test_multiple_fields(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '{integer, string}')
        assert result == {'integer': 42, 'string': 'a string'}

    def test_star_only(self):
        data = {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }
        result = mask.apply(data, '*')
        assert result == data

    def test_with_objects(self):
        data = DObject({
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        })
        result = mask.apply(data, '{integer, string}')
        assert result == {'integer': 42, 'string': 'a string'}

    def test_with_ordered_dict(self):
        data = OrderedDict({
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        })
        result = mask.apply(data, '{integer, string}')
        assert result == {'integer': 42, 'string': 'a string'}

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
        assert result == {'nested': {
            'integer': 42,
            'string': 'a string',
            'boolean': True,
        }}

    def test_nested_fields(self):
        data = {
            'nested': {
                'integer': 42,
                'string': 'a string',
                'boolean': True,
            }
        }
        result = mask.apply(data, '{nested{integer}}')
        assert result == {'nested': {'integer': 42}}

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
        assert result == {'nested': {'integer': 42}, 'other': 'value'}

    def test_nested_fields_when_none(self):
        data = {'nested': None}
        result = mask.apply(data, '{nested{integer}}')
        assert result == {'nested': None}

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

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, family_fields), data)

    def test_nested_api_fields(self):
        family_fields = {
            'father': fields.Nested(person_fields),
            'mother': fields.Nested(person_fields),
        }

        result = mask.apply(family_fields, 'father{name},mother{age}')
        assert set(result.keys()) == set(['father', 'mother'])
        assert isinstance(result['father'], fields.Nested)
        assert set(result['father'].nested.keys()) == set(['name'])
        assert isinstance(result['mother'], fields.Nested)
        assert set(result['mother'].nested.keys()) == set(['age'])

        data = {
            'father': {'name': 'John', 'age': 42},
            'mother': {'name': 'Jane', 'age': 42},
        }
        expected = {'father': {'name': 'John'}, 'mother': {'age': 42}}

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, family_fields), data)

    def test_multiple_nested_api_fields(self):
        level_2 = {'nested_2': fields.Nested(person_fields)}
        level_1 = {'nested_1': fields.Nested(level_2)}
        root = {'nested': fields.Nested(level_1)}

        result = mask.apply(root, 'nested{nested_1{nested_2{name}}}')
        assert set(result.keys()) == set(['nested'])
        assert isinstance(result['nested'], fields.Nested)
        assert set(result['nested'].nested.keys()) == set(['nested_1'])

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

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, root), data)

    def test_list_fields_with_simple_field(self):
        family_fields = {
            'name': fields.String,
            'members': fields.List(fields.String)
        }

        result = mask.apply(family_fields, 'members')
        assert set(result.keys()) == set(['members'])
        assert isinstance(result['members'], fields.List)
        assert isinstance(result['members'].container, fields.String)

        data = {'name': 'Doe', 'members': ['John', 'Jane']}
        expected = {'members': ['John', 'Jane']}

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, family_fields), data)

    def test_list_fields_with_nested(self):
        family_fields = {
            'members': fields.List(fields.Nested(person_fields))
        }

        result = mask.apply(family_fields, 'members{name}')
        assert set(result.keys()) == set(['members'])
        assert isinstance(result['members'], fields.List)
        assert isinstance(result['members'].container, fields.Nested)
        assert set(result['members'].container.nested.keys()) == set(['name'])

        data = {'members': [
            {'name': 'John', 'age': 42},
            {'name': 'Jane', 'age': 42},
        ]}
        expected = {'members': [{'name': 'John'}, {'name': 'Jane'}]}

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, family_fields), data)

    def test_list_fields_with_nested_inherited(self, app):
        api = Api(app)

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

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, family), data)

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

        assert_data(marshal(data, result), expected)
        # Should leave th original mask untouched
        assert_data(marshal(data, family_fields), data)

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
        assert result == [
            {'integer': 42, 'string': 'a string'},
            {'integer': 404, 'string': 'another string'}
        ]

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
        assert result == {'list': [{
            'integer': 42,
            'string': 'a string',
        }, {
            'integer': 404,
            'string': 'another string',
        }]}

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
        assert result == {'list': [{'integer': 42}, {'integer': 404}]}

    def test_missing_field_none_by_default(self):
        result = mask.apply({}, '{integer}')
        assert result == {'integer': None}

    def test_missing_field_skipped(self):
        result = mask.apply({}, '{integer}', skip=True)
        assert result == {}

    def test_missing_nested_field_skipped(self):
        result = mask.apply({}, 'nested{integer}', skip=True)
        assert result == {}

    def test_mask_error_on_simple_fields(self):
        model = {
            'name': fields.String,
        }

        with pytest.raises(mask.MaskError):
            mask.apply(model, 'name{notpossible}')

    def test_mask_error_on_list_field(self):
        model = {
            'nested': fields.List(fields.String)
        }

        with pytest.raises(mask.MaskError):
            mask.apply(model, 'nested{notpossible}')


class MaskAPI(object):
    def test_marshal_with_honour_field_mask_header(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={
            'X-Fields': '{name,age}'
        })
        assert data == {'name': 'John Doe', 'age': 42}

    def test_marshal_with_honour_field_mask_list(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={'X-Fields': '{name,age}'})
        assert data == [{
            'name': 'John Doe',
            'age': 42,
        }, {
            'name': 'Jane Doe',
            'age': 33,
        }]

    def test_marshal_with_honour_complex_field_mask_header(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={
            'X-Fields': 'family{father{name},mother{age},children{name,attr},free{key-2}}'
        })
        assert data == {'family': {
            'father': {'name': 'John'},
            'mother': {'age': 42},
            'children': [{'name': 'Jack', 'attr': 'value-1'}, {'name': 'Julie', 'attr': 'value-2'}],
            'free': [{'key-2': '1-2'}, {'key-2': '2-2'}]
        }}

    def test_marshal_honour_field_mask(self, app):
        api = Api(app)

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

        assert result == {
            'name': 'John Doe',
            'age': 42,
        }

    def test_marshal_with_honour_default_mask(self, app, client):
        api = Api(app)

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

    def test_marshal_with_honour_default_model_mask(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/')
        assert data == {'name': 'John Doe', 'age': 42}

    def test_marshal_with_honour_header_field_mask_with_default_model_mask(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={
            'X-Fields': '{name}'
        })
        assert data == {'name': 'John Doe'}

    def test_marshal_with_honour_header_default_mask_with_default_model_mask(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/')
        assert data == {'name': 'John Doe'}

    def test_marshal_with_honour_header_field_mask_with_default_mask(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={'X-Fields': '{name}'})
        assert data == {'name': 'John Doe'}

    def test_marshal_with_honour_header_field_mask_with_default_mask_and_default_model_mask(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={'X-Fields': '{name}'})
        assert data == {'name': 'John Doe'}

    def test_marshal_with_honour_custom_field_mask(self, app, client):
        api = Api(app)

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

        app.config['RESTPLUS_MASK_HEADER'] = 'X-Mask'
        data = client.get_json('/test/', headers={'X-Mask': '{name,age}'})

        assert data == {'name': 'John Doe', 'age': 42}

    def test_marshal_does_not_hit_unrequired_attributes(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={'X-Fields': '{name,age}'})
        assert data == {'name': 'John Doe', 'age': 42}

    def test_marshal_with_skip_missing_fields(self, app, client):
        api = Api(app)

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

        data = client.get_json('/test/', headers={'X-Fields': '{name,missing}'})
        assert data == {'name': 'John Doe'}

    def test_marshal_handle_inheritance(self, app):
        api = Api(app)

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

        for value, expected in values:
            result = marshal(data, child, mask=value)
            assert result == expected

    def test_marshal_with_handle_polymorph(self, app, client):
        api = Api(app)

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

        data = client.get_json('/thing-1/', headers={'X-Fields': 'owner{name}'})
        assert data == {'owner': {'name': 'child1'}}

        data = client.get_json('/thing-1/', headers={'X-Fields': 'owner{extra1}'})
        assert data == {'owner': {'extra1': 'extra1'}}

        data = client.get_json('/thing-2/', headers={'X-Fields': 'owner{name}'})
        assert data == {'owner': {'name': 'child2'}}

    def test_raise_400_on_invalid_mask(self, app, client):
        api = Api(app)

        model = api.model('Test', {
            'name': fields.String,
            'age': fields.Integer,
        })

        @api.route('/test/')
        class TestResource(Resource):
            @api.marshal_with(model)
            def get(self):
                pass

        response = client.get('/test/', headers={'X-Fields': 'name{,missing}'})
        assert response.status_code == 400
        assert response.content_type == 'application/json'


class SwaggerMaskHeaderTest(object):
    def test_marshal_with_expose_mask_header(self, app, client):
        api = Api(app)

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

        specs = client.get_specs()
        op = specs['paths']['/test/']['get']

        assert 'parameters' in op
        assert len(op['parameters']) == 1

        param = op['parameters'][0]

        assert param['name'] == 'X-Fields'
        assert param['type'] == 'string'
        assert param['format'] == 'mask'
        assert param['in'] == 'header'
        assert 'required' not in param
        assert 'default' not in param

    def test_marshal_with_expose_custom_mask_header(self, app, client):
        api = Api(app)

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

        app.config['RESTPLUS_MASK_HEADER'] = 'X-Mask'
        specs = client.get_specs()

        op = specs['paths']['/test/']['get']
        assert 'parameters' in op
        assert len(op['parameters']) == 1

        param = op['parameters'][0]
        assert param['name'] == 'X-Mask'

    def test_marshal_with_disabling_mask_header(self, app, client):
        api = Api(app)

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

        app.config['RESTPLUS_MASK_SWAGGER'] = False
        specs = client.get_specs()

        op = specs['paths']['/test/']['get']

        assert 'parameters' not in op

    def test_is_only_exposed_on_marshal_with(self, app, client):
        api = Api(app)

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

        specs = client.get_specs()
        op = specs['paths']['/test/']['get']

        assert 'parameters' not in op

    def test_marshal_with_expose_default_mask_header(self, app, client):
        api = Api(app)

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

        specs = client.get_specs()
        op = specs['paths']['/test/']['get']

        assert 'parameters' in op
        assert len(op['parameters']) == 1

        param = op['parameters'][0]

        assert param['name'] == 'X-Fields'
        assert param['type'] == 'string'
        assert param['format'] == 'mask'
        assert param['default'] == '{name,age}'
        assert param['in'] == 'header'
        assert 'required' not in param

    def test_marshal_with_expose_default_model_mask_header(self, app, client):
        api = Api(app)

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

        specs = client.get_specs()
        definition = specs['definitions']['Test']
        assert 'x-mask' in definition
        assert definition['x-mask'] == '{name,age}'
