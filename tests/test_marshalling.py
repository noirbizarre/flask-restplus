# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from flask_restplus import (
    marshal, marshal_with, marshal_with_field, fields, Api, Resource
)

from collections import OrderedDict


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(Resource):
    def get(self):
        return {}


class MarshallingTest(object):
    def test_marshal(self):
        model = OrderedDict([('foo', fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal(marshal_dict, model)
        assert isinstance(output, dict)
        assert not isinstance(output, OrderedDict)
        assert output == {'foo': 'bar'}

    def test_marshal_wildcard_nested(self):
        nest = fields.Nested(OrderedDict([('thumbnail', fields.String), ('video', fields.String)]))
        wild = fields.Wildcard(nest)
        wildcard_fields = OrderedDict([('*', wild)])
        model = OrderedDict([('preview', fields.Nested(wildcard_fields))])
        sub_dict = OrderedDict([
            ('9:16', {'thumbnail': 24, 'video': 12}),
            ('16:9', {'thumbnail': 25, 'video': 11}),
            ('1:1', {'thumbnail': 26, 'video': 10})
        ])
        marshal_dict = OrderedDict([('preview', sub_dict)])
        output = marshal(marshal_dict, model)
        assert output == {'preview': {'1:1': {'thumbnail': '26', 'video': '10'},
                                      '16:9': {'thumbnail': '25', 'video': '11'},
                                      '9:16': {'thumbnail': '24', 'video': '12'}}}

    def test_marshal_wildcard_list(self):
        wild = fields.Wildcard(fields.List(fields.String))
        wildcard_fields = OrderedDict([('*', wild)])
        model = OrderedDict([('preview', fields.Nested(wildcard_fields))])
        sub_dict = OrderedDict([
            ('1:1', [1, 2, 3]),
            ('16:9', [4, 5, 6]),
            ('9:16', [7, 8, 9])
        ])
        marshal_dict = OrderedDict([('preview', sub_dict)])
        output = marshal(marshal_dict, model)
        assert output == {'preview': {'9:16': ['7', '8', '9'],
                                      '16:9': ['4', '5', '6'],
                                      '1:1': ['1', '2', '3']}}

    def test_marshal_with_envelope(self):
        model = OrderedDict([('foo', fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal(marshal_dict, model, envelope='hey')
        assert output == {'hey': {'foo': 'bar'}}

    def test_marshal_wildcard_with_envelope(self):
        wild = fields.Wildcard(fields.String)
        model = OrderedDict([('foo', fields.Raw), ('*', wild)])
        marshal_dict = OrderedDict([('foo', {'bat': 'baz'}), ('a', 'toto'), ('b', 'tata')])
        output = marshal(marshal_dict, model, envelope='hey')
        assert output == {'hey': {'a': 'toto', 'b': 'tata', 'foo': {'bat': 'baz'}}}

    def test_marshal_with_skip_none(self):
        model = OrderedDict([('foo', fields.Raw), ('bat', fields.Raw), ('qux', fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', None)])
        output = marshal(marshal_dict, model, skip_none=True)
        assert output == {'foo': 'bar'}

    def test_marshal_wildcard_with_skip_none(self):
        wild = fields.Wildcard(fields.String)
        model = OrderedDict([('foo', fields.Raw), ('*', wild)])
        marshal_dict = OrderedDict([('foo', None), ('bat', None), ('baz', 'biz'), ('bar', None)])
        output = marshal(marshal_dict, model, skip_none=True)
        assert output == {'baz': 'biz'}

    def test_marshal_decorator(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        assert try_me() == {'foo': 'bar'}

    def test_marshal_decorator_with_envelope(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model, envelope='hey')
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])

        assert try_me() == {'hey': {'foo': 'bar'}}

    def test_marshal_decorator_with_skip_none(self):
        model = OrderedDict([('foo', fields.Raw), ('bat', fields.Raw), ('qux', fields.Raw)])

        @marshal_with(model, skip_none=True)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', None)])

        assert try_me() == {'foo': 'bar'}

    def test_marshal_decorator_tuple(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model)
        def try_me():
            headers = {'X-test': 123}
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, headers
        assert try_me() == ({'foo': 'bar'}, 200, {'X-test': 123})

    def test_marshal_decorator_tuple_with_envelope(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model, envelope='hey')
        def try_me():
            headers = {'X-test': 123}
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, headers

        assert try_me() == ({'hey': {'foo': 'bar'}}, 200, {'X-test': 123})

    def test_marshal_decorator_tuple_with_skip_none(self):
        model = OrderedDict([('foo', fields.Raw), ('bat', fields.Raw), ('qux', fields.Raw)])

        @marshal_with(model, skip_none=True)
        def try_me():
            headers = {'X-test': 123}
            return OrderedDict([('foo', 'bar'), ('bat', None)]), 200, headers

        assert try_me() == ({'foo': 'bar'}, 200, {'X-test': 123})

    def test_marshal_field_decorator(self):
        model = fields.Raw

        @marshal_with_field(model)
        def try_me():
            return 'foo'
        assert try_me() == 'foo'

    def test_marshal_field_decorator_tuple(self):
        model = fields.Raw

        @marshal_with_field(model)
        def try_me():
            return 'foo', 200, {'X-test': 123}
        assert try_me() == ('foo', 200, {'X-test': 123})

    def test_marshal_field(self):
        model = OrderedDict({'foo': fields.Raw()})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal(marshal_fields, model)
        assert output == {'foo': 'bar'}

    def test_marshal_tuple(self):
        model = OrderedDict({'foo': fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal((marshal_fields,), model)
        assert output == [{'foo': 'bar'}]

    def test_marshal_tuple_with_envelope(self):
        model = OrderedDict({'foo': fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal((marshal_fields,), model, envelope='hey')
        assert output == {'hey': [{'foo': 'bar'}]}

    def test_marshal_tuple_with_skip_none(self):
        model = OrderedDict([('foo', fields.Raw), ('bat', fields.Raw), ('qux', fields.Raw)])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', None)])
        output = marshal((marshal_fields,), model, skip_none=True)
        assert output == [{'foo': 'bar'}]

    def test_marshal_nested(self):
        model = {
            'foo': fields.Raw,
            'fee': fields.Nested({'fye': fields.String}),
        }

        marshal_fields = {
            'foo': 'bar',
            'bat': 'baz',
            'fee': {'fye': 'fum'},
        }
        expected = {
            'foo': 'bar',
            'fee': {'fye': 'fum'},
        }

        output = marshal(marshal_fields, model)

        assert output == expected

    def test_marshal_nested_ordered(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested({
                'fye': fields.String,
            }))
        ])

        marshal_fields = {
            'foo': 'bar',
            'bat': 'baz',
            'fee': {'fye': 'fum'},
        }
        expected = OrderedDict([
            ('foo', 'bar'),
            ('fee', OrderedDict([('fye', 'fum')]))
        ])

        output = marshal(marshal_fields, model, ordered=True)

        assert isinstance(output, OrderedDict)
        assert output == expected
        assert isinstance(output['fee'], OrderedDict)

    def test_marshal_nested_with_non_null(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String),
                    ('blah', fields.String)
                ]), allow_null=False))
        ])
        marshal_fields = [OrderedDict([('foo', 'bar'),
                                       ('bat', 'baz'),
                                       ('fee', None)])]
        output = marshal(marshal_fields, model)
        expected = [OrderedDict([
            ('foo', 'bar'),
            ('fee', OrderedDict([('fye', None), ('blah', None)]))
        ])]
        assert output == expected

    def test_marshal_nested_with_null(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String),
                    ('blah', fields.String)
                ]), allow_null=True))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', None)])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([('foo', 'bar'), ('fee', None)])
        assert output == expected

    def test_marshal_nested_with_skip_none(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String)
                ]), skip_none=True))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', None)])
        output = marshal(marshal_fields, model, skip_none=True)
        expected = OrderedDict([('foo', 'bar')])
        assert output == expected

    def test_allow_null_presents_data(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String),
                    ('blah', fields.String)
                ]), allow_null=True))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', {'blah': 'cool'})])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([
            ('foo', 'bar'),
            ('fee', OrderedDict([('fye', None), ('blah', 'cool')]))
        ])
        assert output == expected

    def test_skip_none_presents_data(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String),
                    ('blah', fields.String),
                    ('foe', fields.String)
                ]), skip_none=True))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', {'blah': 'cool', 'foe': None})])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([
            ('foo', 'bar'),
            ('fee', OrderedDict([('blah', 'cool')]))
        ])
        assert output == expected

    def test_marshal_nested_property(self):
        class TestObject(object):
            @property
            def fee(self):
                return {'blah': 'cool'}
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String),
                    ('blah', fields.String)
                ]), allow_null=True))
        ])
        obj = TestObject()
        obj.foo = 'bar'
        obj.bat = 'baz'
        output = marshal([obj], model)
        expected = [OrderedDict([
            ('foo', 'bar'),
            ('fee', OrderedDict([
                ('fye', None),
                ('blah', 'cool')
            ]))
        ])]
        assert output == expected

    def test_marshal_nested_property_with_skip_none(self):
        class TestObject(object):
            @property
            def fee(self):
                return {'blah': 'cool', 'foe': None}
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested(
                OrderedDict([
                    ('fye', fields.String),
                    ('blah', fields.String),
                    ('foe', fields.String)
                ]), skip_none=True))
        ])
        obj = TestObject()
        obj.foo = 'bar'
        obj.bat = 'baz'
        output = marshal([obj], model)
        expected = [OrderedDict([
            ('foo', 'bar'),
            ('fee', OrderedDict([
                ('blah', 'cool')
            ]))
        ])]
        assert output == expected

    def test_marshal_list(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.List(fields.String))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', ['fye', 'fum'])])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([('foo', 'bar'), ('fee', (['fye', 'fum']))])
        assert output == expected

    def test_marshal_list_of_nesteds(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.List(fields.Nested({
                'fye': fields.String
            })))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', {'fye': 'fum'})])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([('foo', 'bar'),
                                ('fee', [OrderedDict([('fye', 'fum')])])])
        assert output == expected

    def test_marshal_list_of_lists(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.List(fields.List(
                fields.String)))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'),
                                      ('bat', 'baz'),
                                      ('fee', [['fye'], ['fum']])])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([('foo', 'bar'), ('fee', [['fye'], ['fum']])])
        assert output == expected

    def test_marshal_nested_dict(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('bar', OrderedDict([
                ('a', fields.Raw),
                ('b', fields.Raw),
            ])),
        ])
        marshal_fields = OrderedDict([('foo', 'foo-val'),
                                      ('bar', 'bar-val'),
                                      ('bat', 'bat-val'),
                                      ('a', 1), ('b', 2), ('c', 3)])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([('foo', 'foo-val'),
                                ('bar', OrderedDict([('a', 1), ('b', 2)]))])
        assert output == expected

    @pytest.mark.options(debug=True)
    def test_will_prettyprint_json_in_debug_mode(self, app, client):
        api = Api(app)

        class Foo1(Resource):
            def get(self):
                return {'foo': 'bar', 'baz': 'asdf'}

        api.add_resource(Foo1, '/foo', endpoint='bar')

        foo = client.get('/foo')

        # Python's dictionaries have random order (as of "new" Pythons,
        # anyway), so we can't verify the actual output here.  We just
        # assert that they're properly prettyprinted.
        lines = foo.data.splitlines()
        lines = [line.decode() for line in lines]
        assert "{" == lines[0]
        assert lines[1].startswith('    ')
        assert lines[2].startswith('    ')
        assert "}" == lines[3]

        # Assert our trailing newline.
        assert foo.data.endswith(b'\n')

    def test_json_float_marshalled(self, app, client):
        api = Api(app)

        class FooResource(Resource):
            fields = {'foo': fields.Float}

            def get(self):
                return marshal({"foo": 3.0}, self.fields)

        api.add_resource(FooResource, '/api')

        resp = client.get('/api')
        assert resp.status_code == 200
        assert resp.data.decode('utf-8') == '{"foo": 3.0}\n'
