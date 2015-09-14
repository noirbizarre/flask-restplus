# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint
from flask.ext.restplus import fields, Api

from . import TestCase


class FieldTestCase(TestCase):
    def setUp(self):
        super(FieldTestCase, self).setUp()
        blueprint = Blueprint('api', __name__)
        self.api = Api(blueprint)
        self.app.register_blueprint(blueprint)


class RawFieldTest(FieldTestCase):
    def test_simple_raw_field(self):
        field = fields.Raw()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'object'})

    def test_raw_field_with_description(self):
        field = fields.Raw(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'object', 'description': 'A description'})

    def test_raw_field_with_title(self):
        field = fields.Raw(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'object', 'title': 'A title'})

    def test_raw_field_with_required(self):
        field = fields.Raw(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'object'})

    def test_raw_field_with_readonly(self):
        field = fields.Raw(readonly=True)
        self.assertEqual(field.__schema__, {'type': 'object', 'readOnly': True})

    def test_raw_field_with_default(self):
        field = fields.Raw(default='aaa')
        self.assertEqual(field.__schema__, {'type': 'object', 'default': 'aaa'})


class StringFieldTest(FieldTestCase):
    def test_simple_string_field(self):
        field = fields.String()
        self.assertFalse(field.required)
        self.assertFalse(field.discriminator)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_string_field_with_description(self):
        field = fields.String(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'description': 'A description'})

    def test_string_field_with_title(self):
        field = fields.String(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'title': 'A title'})

    def test_string_field_with_required(self):
        field = fields.String(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_string_field_with_readonly(self):
        field = fields.String(readonly=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'readOnly': True})

    def test_string_field_with_enum(self):
        enum = ['A', 'B', 'C']
        field = fields.String(enum=enum)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'enum': enum, 'example': enum[0]})

    def test_string_field_with_callable_enum(self):
        enum = lambda: ['A', 'B', 'C']  # noqa
        field = fields.String(enum=enum)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'enum': ['A', 'B', 'C'], 'example': 'A'})

    def test_string_field_with_default(self):
        field = fields.String(default='aaa')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'default': 'aaa'})

    def test_string_field_with_discriminator(self):
        field = fields.String(discriminator=True)
        self.assertTrue(field.discriminator)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_string_field_with_discriminator_override_require(self):
        field = fields.String(discriminator=True, required=False)
        self.assertTrue(field.discriminator)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_discriminator_output(self):
        model = self.api.model('Test', {
            'name': fields.String(discriminator=True),
        })

        data = self.api.marshal({}, model)
        self.assertEqual(data, {'name': 'Test'})

    def test_multiple_discriminator_field(self):
        model = self.api.model('Test', {
            'name': fields.String(discriminator=True),
            'name2': fields.String(discriminator=True),
        })

        with self.assertRaises(ValueError):
            self.api.marshal(object(), model)


class IntegerFieldTest(FieldTestCase):
    def test_simple_integer_field(self):
        field = fields.Integer()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer'})

    def test_integer_field_with_description(self):
        field = fields.Integer(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer', 'description': 'A description'})

    def test_integer_field_with_title(self):
        field = fields.Integer(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer', 'title': 'A title'})

    def test_integer_field_with_required(self):
        field = fields.Integer(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer'})

    def test_integer_field_with_readonly(self):
        field = fields.Integer(readonly=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer', 'readOnly': True})

    def test_integer_field_with_min_max(self):
        field = fields.Integer(min=0, max=5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer', 'minimum': 0, 'maximum': 5})

    def test_integer_field_with_default(self):
        field = fields.Integer(default=42)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer', 'default': 42})


class BooleanFieldTest(FieldTestCase):
    def test_simple_boolean_field(self):
        field = fields.Boolean()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean'})

    def test_boolean_field_with_description(self):
        field = fields.Boolean(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean', 'description': 'A description'})

    def test_boolean_field_with_title(self):
        field = fields.Boolean(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean', 'title': 'A title'})

    def test_boolean_field_with_required(self):
        field = fields.Boolean(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean'})

    def test_boolean_field_with_readonly(self):
        field = fields.Boolean(readonly=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean', 'readOnly': True})

    def test_boolean_field_with_default(self):
        field = fields.Boolean(default=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean', 'default': True})


class FloatFieldTest(FieldTestCase):
    def test_simple_float_field(self):
        field = fields.Float()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_float_field_with_description(self):
        field = fields.Float(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'description': 'A description'})

    def test_float_field_with_title(self):
        field = fields.Float(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'title': 'A title'})

    def test_float_field_with_required(self):
        field = fields.Float(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_float_field_with_readonly(self):
        field = fields.Float(readonly=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'readOnly': True})

    def test_float_field_with_min_max(self):
        field = fields.Float(min=0, max=5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'minimum': 0, 'maximum': 5})

    def test_float_field_with_default(self):
        field = fields.Float(default=0.5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'default': 0.5})


class FixedFieldTest(FieldTestCase):
    def test_simple_fixed_field(self):
        field = fields.Fixed()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_fixed_field_with_description(self):
        field = fields.Fixed(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'description': 'A description'})

    def test_fixed_field_with_title(self):
        field = fields.Fixed(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'title': 'A title'})

    def test_fixed_field_with_required(self):
        field = fields.Fixed(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_fixed_field_with_readonly(self):
        field = fields.Fixed(readonly=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'readOnly': True})

    def test_fixed_field_with_min_max(self):
        field = fields.Fixed(min=0, max=5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'minimum': 0, 'maximum': 5})

    def test_fixed_field_with_default(self):
        field = fields.Fixed(default=0.5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'default': 0.5})


class ArbitraryFieldTest(FieldTestCase):
    def test_simple_arbitrary_field(self):
        field = fields.Arbitrary()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_arbitrary_field_with_required(self):
        field = fields.Arbitrary(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_arbitrary_field_with_description(self):
        field = fields.Arbitrary(description='A description')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'description': 'A description'})

    def test_arbitrary_field_with_title(self):
        field = fields.Arbitrary(title='A title')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'title': 'A title'})

    def test_arbitrary_field_with_readonly(self):
        field = fields.Arbitrary(readonly=True)
        self.assertEqual(field.__schema__, {'type': 'number', 'readOnly': True})

    def test_arbitrary_field_with_min_max(self):
        field = fields.Arbitrary(min=0, max=5)
        self.assertEqual(field.__schema__, {'type': 'number', 'minimum': 0, 'maximum': 5})

    def test_arbitrary_field_with_default(self):
        field = fields.Arbitrary(default=0.5)
        self.assertEqual(field.__schema__, {'type': 'number', 'default': 0.5})


class DatetimeFieldTest(FieldTestCase):
    def test_simple_datetime_field(self):
        field = fields.DateTime()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time'})

    def test_datetime_field_with_required(self):
        field = fields.DateTime(required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time'})

    def test_datetime_field_with_description(self):
        field = fields.DateTime(description='A description')
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time', 'description': 'A description'})

    def test_datetime_field_with_title(self):
        field = fields.DateTime(title='A title')
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time', 'title': 'A title'})

    def test_datetime_field_with_default(self):
        field = fields.DateTime(default='2014-08-25')
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time', 'default': '2014-08-25'})


class FormatedStringFieldTest(FieldTestCase):
    def test_simple_formatted_string_field(self):
        field = fields.FormattedString('Hello {name}')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_formatted_string_field_with_required(self):
        field = fields.FormattedString('Hello {name}', required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_formatted_string_field_with_description(self):
        field = fields.FormattedString('Hello {name}', description='A description')
        self.assertEqual(field.__schema__, {'type': 'string', 'description': 'A description'})

    def test_formatted_field_with_title(self):
        field = fields.FormattedString('Hello {name}', title='A title')
        self.assertEqual(field.__schema__, {'type': 'string', 'title': 'A title'})

    def test_formatted_string_field_with_readonly(self):
        field = fields.FormattedString('Hello {name}', readonly=True)
        self.assertEqual(field.__schema__, {'type': 'string', 'readOnly': True})


class UrlFieldTest(FieldTestCase):
    def test_simple_url_field(self):
        field = fields.Url('endpoint')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_url_field_with_required(self):
        field = fields.Url('endpoint', required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_url_field_with_description(self):
        field = fields.Url('endpoint', description='A description')
        self.assertEqual(field.__schema__, {'type': 'string', 'description': 'A description'})

    def test_url_field_with_title(self):
        field = fields.Url('endpoint', title='A title')
        self.assertEqual(field.__schema__, {'type': 'string', 'title': 'A title'})

    def test_url_field_with_readonly(self):
        field = fields.Url('endpoint', readonly=True)
        self.assertEqual(field.__schema__, {'type': 'string', 'readOnly': True})


class NestedFieldTest(FieldTestCase):
    def test_nested_field(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})

    def test_nested_field_with_required(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, required=True)
        self.assertTrue(field.required)
        self.assertFalse(field.allow_null)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})

    def test_nested_field_with_description(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, description='A description')
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel', 'description': 'A description'})

    def test_nested_field_with_title(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, title='A title')
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel', 'title': 'A title'})

    def test_nested_field_with_allow_null(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, allow_null=True)
        self.assertFalse(field.required)
        self.assertTrue(field.allow_null)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})

    def test_nested_field_with_readonly(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, readonly=True)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel', 'readOnly': True})

    def test_nested_field_as_list(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, as_list=True)
        self.assertTrue(field.as_list)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}})

    def test_nested_field_as_list_is_reusable(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})

        field = fields.Nested(nested_fields, as_list=True)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}})

        field = fields.Nested(nested_fields)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})


class ListFieldTest(FieldTestCase):
    def test_list_field(self):
        field = fields.List(fields.String)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'type': 'string'}})

    def test_list_field_with_required(self):
        field = fields.List(fields.String, required=True)
        self.assertTrue(field.required)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'type': 'string'}})

    def test_list_field_with_description(self):
        field = fields.List(fields.String, description='A description')
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'type': 'string'}, 'description': 'A description'})

    def test_list_field_with_title(self):
        field = fields.List(fields.String, title='A title')
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'type': 'string'}, 'title': 'A title'})

    def test_list_field_with_readonly(self):
        field = fields.List(fields.String, readonly=True)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'type': 'string'}, 'readOnly': True})

    def test_list_field_with_nested_field(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.List(fields.Nested(nested_fields))
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}})



class ClassNameFieldTest(FieldTestCase):
    def test_simple_string_field(self):
        field = fields.ClassName()
        self.assertFalse(field.required)
        self.assertFalse(field.discriminator)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_default_output_classname(self):
        model = self.api.model('Test', {
            'name': fields.ClassName(),
        })

        class FakeClass(object):
            pass

        data = self.api.marshal(FakeClass(), model)
        self.assertEqual(data, {'name': 'FakeClass'})

    def test_output_dash(self):
        model = self.api.model('Test', {
            'name': fields.ClassName(dash=True),
        })

        class FakeClass(object):
            pass

        data = self.api.marshal(FakeClass(), model)
        self.assertEqual(data, {'name': 'fake_class'})


class PolymorphTest(FieldTestCase):
    def test_polymorph_field(self):
        parent = self.api.model('Person', {
            'name': fields.String,
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child2', parent, {
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

        thing = self.api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        def data(cls):
            return self.api.marshal({'owner': cls()}, thing)

        self.assertEqual(data(Child1), {'owner': {
            'name': 'child1',
            'extra1': 'extra1'
        }})

        self.assertEqual(data(Child2), {'owner': {
            'name': 'child2',
            'extra2': 'extra2'
        }})

    def test_polymorph_field_no_common_ancestor(self):
        child1 = self.api.model('Child1', {
            'extra1': fields.String,
        })

        child2 = self.api.model('Child2', {
            'extra2': fields.String,
        })

        class Child1(object):
            pass

        class Child2(object):
            pass

        mapping = {
            Child1: child1,
            Child2: child2
        }

        with self.assertRaises(ValueError):
            fields.Polymorph(mapping)

    def test_polymorph_field_unknown_class(self):
        parent = self.api.model('Person', {
            'name': fields.String,
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child2', parent, {
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

        thing = self.api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        with self.assertRaises(ValueError):
            self.api.marshal({'owner': object()}, thing)

    def test_polymorph_field_ambiguous_mapping(self):
        parent = self.api.model('Parent', {
            'name': fields.String,
        })

        child = self.api.inherit('Child', parent, {
            'extra': fields.String,
        })

        class Parent(object):
            name = 'parent'

        class Child(Parent):
            extra = 'extra'

        mapping = {
            Parent: parent,
            Child: child
        }

        thing = self.api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        with self.assertRaises(ValueError):
            self.api.marshal({'owner': Child()}, thing)

    def test_polymorph_field_required_default(self):
        parent = self.api.model('Person', {
            'name': fields.String,
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child2', parent, {
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

        thing = self.api.model('Thing', {
            'owner': fields.Polymorph(mapping, required=True, default={'name': 'default'}),
        })

        data = self.api.marshal({}, thing)

        self.assertEqual(data, {'owner': {
            'name': 'default'
        }})

    def test_polymorph_field_not_required(self):
        parent = self.api.model('Person', {
            'name': fields.String,
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child2', parent, {
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

        thing = self.api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        data = self.api.marshal({}, thing)

        self.assertEqual(data, {'owner': None})

    def test_polymorph_with_discriminator(self):
        parent = self.api.model('Person', {
            'name': fields.String,
            'model': fields.String(discriminator=True),
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child2', parent, {
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

        thing = self.api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        def data(cls):
            return self.api.marshal({'owner': cls()}, thing)

        self.assertEqual(data(Child1), {'owner': {
            'name': 'child1',
            'model': 'Child1',
            'extra1': 'extra1'
        }})

        self.assertEqual(data(Child2), {'owner': {
            'name': 'child2',
            'model': 'Child2',
            'extra2': 'extra2'
        }})


class CustomFieldTest(FieldTestCase):
    def test_custom_field(self):
        class CustomField(fields.Integer):
            __schema_format__ = 'int64'

        field = CustomField()

        self.assertEqual(field.__schema__, {'type': 'integer', 'format': 'int64'})
