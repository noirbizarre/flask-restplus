# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus import (
    marshal, marshal_with, marshal_with_field, fields, Api, Resource
)

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from . import TestCase


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(Resource):
    def get(self):
        return {}


class MarshallingTestCase(TestCase):
    def test_marshal(self):
        model = OrderedDict([('foo', fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal(marshal_dict, model)
        self.assertEquals(output, {'foo': 'bar'})

    def test_marshal_with_envelope(self):
        model = OrderedDict([('foo', fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal(marshal_dict, model, envelope='hey')
        self.assertEquals(output, {'hey': {'foo': 'bar'}})

    def test_marshal_decorator(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        self.assertEquals(try_me(), {'foo': 'bar'})

    def test_marshal_decorator_with_envelope(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model, envelope='hey')
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])

        self.assertEquals(try_me(), {'hey': {'foo': 'bar'}})

    def test_marshal_decorator_tuple(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model)
        def try_me():
            headers = {'X-test': 123}
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, headers
        self.assertEquals(try_me(), ({'foo': 'bar'}, 200, {'X-test': 123}))

    def test_marshal_decorator_tuple_with_envelope(self):
        model = OrderedDict([('foo', fields.Raw)])

        @marshal_with(model, envelope='hey')
        def try_me():
            headers = {'X-test': 123}
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, headers

        self.assertEquals(try_me(),
                          ({'hey': {'foo': 'bar'}}, 200, {'X-test': 123}))

    def test_marshal_field_decorator(self):
        model = fields.Raw

        @marshal_with_field(model)
        def try_me():
            return 'foo'
        self.assertEquals(try_me(), 'foo')

    def test_marshal_field_decorator_tuple(self):
        model = fields.Raw

        @marshal_with_field(model)
        def try_me():
            return 'foo', 200, {'X-test': 123}
        self.assertEquals(('foo', 200, {'X-test': 123}), try_me())

    def test_marshal_field(self):
        model = OrderedDict({'foo': fields.Raw()})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal(marshal_fields, model)
        self.assertEquals(output, {'foo': 'bar'})

    def test_marshal_tuple(self):
        model = OrderedDict({'foo': fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal((marshal_fields,), model)
        self.assertEquals(output, [{'foo': 'bar'}])

    def test_marshal_tuple_with_envelope(self):
        model = OrderedDict({'foo': fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = marshal((marshal_fields,), model, envelope='hey')
        self.assertEquals(output, {'hey': [{'foo': 'bar'}]})

    def test_marshal_nested(self):
        model = OrderedDict([
            ('foo', fields.Raw),
            ('fee', fields.Nested({
                'fye': fields.String,
            }))
        ])

        marshal_fields = OrderedDict([
            ('foo', 'bar'), ('bat', 'baz'), ('fee', {'fye': 'fum'})
        ])
        output = marshal(marshal_fields, model)
        expected = OrderedDict([
            ('foo', 'bar'), ('fee', OrderedDict([('fye', 'fum')]))
        ])
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

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
        self.assertEquals(output, expected)

    def test_will_prettyprint_json_in_debug_mode(self):
        self.app.config['DEBUG'] = True
        api = Api(self.app)

        class Foo1(Resource):
            def get(self):
                return {'foo': 'bar', 'baz': 'asdf'}

        api.add_resource(Foo1, '/foo', endpoint='bar')

        with self.app.test_client() as client:
            foo = client.get('/foo')

            # Python's dictionaries have random order (as of "new" Pythons,
            # anyway), so we can't verify the actual output here.  We just
            # assert that they're properly prettyprinted.
            lines = foo.data.splitlines()
            lines = [line.decode() for line in lines]
            self.assertEquals("{", lines[0])
            self.assertTrue(lines[1].startswith('    '))
            self.assertTrue(lines[2].startswith('    '))
            self.assertEquals("}", lines[3])

            # Assert our trailing newline.
            self.assertTrue(foo.data.endswith(b'\n'))

    def test_json_float_marshalled(self):
        api = Api(self.app)

        class FooResource(Resource):
            fields = {'foo': fields.Float}

            def get(self):
                return marshal({"foo": 3.0}, self.fields)

        api.add_resource(FooResource, '/api')

        app = self.app.test_client()
        resp = app.get('/api')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.data.decode('utf-8'), '{"foo": 3.0}\n')
