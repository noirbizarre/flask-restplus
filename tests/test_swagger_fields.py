# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, datetime
from functools import partial

from flask import Blueprint
from flask.ext.restplus import fields, Api

from . import TestCase


class FieldTestCase(TestCase):
    field_class = None

    def setUp(self):
        super(FieldTestCase, self).setUp()
        blueprint = Blueprint('api', __name__)
        self.api = Api(blueprint)
        self.app.register_blueprint(blueprint)


class BaseFieldTestMixin(object):
    def test_description(self):
        field = self.field_class(description='A description')
        self.assertIn('description', field.__schema__)
        self.assertEqual(field.__schema__['description'], 'A description')

    def test_title(self):
        field = self.field_class(title='A title')
        self.assertIn('title', field.__schema__)
        self.assertEqual(field.__schema__['title'], 'A title')

    def test_required(self):
        field = self.field_class(required=True)
        self.assertTrue(field.required)

    def test_readonly(self):
        field = self.field_class(readonly=True)
        self.assertIn('readOnly', field.__schema__)
        self.assertTrue(field.__schema__['readOnly'])


class NumberTestMixin(object):
    def test_min(self):
        field = self.field_class(min=0)
        self.assertIn('minimum', field.__schema__)
        self.assertEqual(field.__schema__['minimum'], 0)
        self.assertNotIn('exclusiveMinimum', field.__schema__)

    def test_min_exlusive(self):
        field = self.field_class(min=0, exclusiveMin=True)
        self.assertIn('minimum', field.__schema__)
        self.assertEqual(field.__schema__['minimum'], 0)
        self.assertIn('exclusiveMinimum', field.__schema__)
        self.assertEqual(field.__schema__['exclusiveMinimum'], True)

    def test_max(self):
        field = self.field_class(max=42)
        self.assertIn('maximum', field.__schema__)
        self.assertEqual(field.__schema__['maximum'], 42)
        self.assertNotIn('exclusiveMaximum', field.__schema__)

    def test_max_exclusive(self):
        field = self.field_class(max=42, exclusiveMax=True)
        self.assertIn('maximum', field.__schema__)
        self.assertEqual(field.__schema__['maximum'], 42)
        self.assertIn('exclusiveMaximum', field.__schema__)
        self.assertEqual(field.__schema__['exclusiveMaximum'], True)

    def test_mulitple_of(self):
        field = self.field_class(multiple=5)
        self.assertIn('multipleOf', field.__schema__)
        self.assertEqual(field.__schema__['multipleOf'], 5)


class StringTestMixin(object):
    def test_min_length(self):
        field = self.field_class(min_length=1)
        self.assertIn('minLength', field.__schema__)
        self.assertEqual(field.__schema__['minLength'], 1)

    def test_max_length(self):
        field = self.field_class(max_length=42)
        self.assertIn('maxLength', field.__schema__)
        self.assertEqual(field.__schema__['maxLength'], 42)

    def test_pattern(self):
        field = self.field_class(pattern='[a-z]')
        self.assertIn('pattern', field.__schema__)
        self.assertEqual(field.__schema__['pattern'], '[a-z]')


class RawFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = fields.Raw

    def test_type(self):
        field = fields.Raw()
        self.assertEqual(field.__schema__['type'], 'object')

    def test_default(self):
        field = fields.Raw(default='aaa')
        self.assertEqual(field.__schema__['default'], 'aaa')


class StringFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = fields.String

    def test_defaults(self):
        field = fields.String()
        self.assertFalse(field.required)
        self.assertFalse(field.discriminator)
        self.assertEqual(field.__schema__, {'type': 'string'})

    def test_with_enum(self):
        enum = ['A', 'B', 'C']
        field = fields.String(enum=enum)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'enum': enum, 'example': enum[0]})

    def test_with_callable_enum(self):
        enum = lambda: ['A', 'B', 'C']  # noqa
        field = fields.String(enum=enum)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'enum': ['A', 'B', 'C'], 'example': 'A'})

    def test_with_default(self):
        field = fields.String(default='aaa')
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


class IntegerFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Integer

    def test_defaults(self):
        field = fields.Integer()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer'})

    def test_with_default(self):
        field = fields.Integer(default=42)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'integer', 'default': 42})


class BooleanFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = fields.Boolean

    def test_defaults(self):
        field = fields.Boolean()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean'})

    def test_with_default(self):
        field = fields.Boolean(default=True)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'boolean', 'default': True})


class FloatFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Float

    def test_defaults(self):
        field = fields.Float()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_with_default(self):
        field = fields.Float(default=0.5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'default': 0.5})


class FixedFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Fixed

    def test_defaults(self):
        field = fields.Fixed()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_with_default(self):
        field = fields.Fixed(default=0.5)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number', 'default': 0.5})


class ArbitraryFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Arbitrary

    def test_defaults(self):
        field = fields.Arbitrary()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'number'})

    def test_with_default(self):
        field = fields.Arbitrary(default=0.5)
        self.assertEqual(field.__schema__, {'type': 'number', 'default': 0.5})


class DatetimeFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = fields.DateTime

    def test_defaults(self):
        field = fields.DateTime()
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time'})

    def test_with_default(self):
        field = fields.DateTime(default='2014-08-25')
        self.assertEqual(field.__schema__, {'type': 'string', 'format': 'date-time', 'default': '2014-08-25'})

    def test_min(self):
        field = fields.DateTime(min='1984-06-07')
        self.assertIn('minimum', field.__schema__)
        self.assertEqual(field.__schema__['minimum'], '1984-06-07')
        self.assertNotIn('exclusiveMinimum', field.__schema__)

    def test_min_as_date(self):
        field = fields.DateTime(min=date(1984, 6, 7))
        self.assertIn('minimum', field.__schema__)
        self.assertEqual(field.__schema__['minimum'], '1984-06-07')
        self.assertNotIn('exclusiveMinimum', field.__schema__)

    def test_min_as_datetime(self):
        field = fields.DateTime(min=datetime(1984, 6, 7, 1, 2, 0))
        self.assertIn('minimum', field.__schema__)
        self.assertEqual(field.__schema__['minimum'], '1984-06-07T01:02:00')
        self.assertNotIn('exclusiveMinimum', field.__schema__)

    def test_min_exlusive(self):
        field = fields.DateTime(min='1984-06-07', exclusiveMin=True)
        self.assertIn('minimum', field.__schema__)
        self.assertEqual(field.__schema__['minimum'], '1984-06-07')
        self.assertIn('exclusiveMinimum', field.__schema__)
        self.assertEqual(field.__schema__['exclusiveMinimum'], True)

    def test_max(self):
        field = fields.DateTime(max='1984-06-07')
        self.assertIn('maximum', field.__schema__)
        self.assertEqual(field.__schema__['maximum'], '1984-06-07')
        self.assertNotIn('exclusiveMaximum', field.__schema__)

    def test_max_as_date(self):
        field = fields.DateTime(max=date(1984, 6, 7))
        self.assertIn('maximum', field.__schema__)
        self.assertEqual(field.__schema__['maximum'], '1984-06-07')
        self.assertNotIn('exclusiveMaximum', field.__schema__)

    def test_max_as_datetime(self):
        field = fields.DateTime(max=datetime(1984, 6, 7, 1, 2, 0))
        self.assertIn('maximum', field.__schema__)
        self.assertEqual(field.__schema__['maximum'], '1984-06-07T01:02:00')
        self.assertNotIn('exclusiveMaximum', field.__schema__)

    def test_max_exclusive(self):
        field = fields.DateTime(max='1984-06-07', exclusiveMax=True)
        self.assertIn('maximum', field.__schema__)
        self.assertEqual(field.__schema__['maximum'], '1984-06-07')
        self.assertIn('exclusiveMaximum', field.__schema__)
        self.assertEqual(field.__schema__['exclusiveMaximum'], True)


class FormatedStringFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.FormattedString, 'Hello {name}')

    def test_defaults(self):
        field = fields.FormattedString('Hello {name}')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})


class UrlFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.Url, 'endpoint')

    def test_defaults(self):
        field = fields.Url('endpoint')
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'string'})


class NestedFieldTest(FieldTestCase):
    def test_defaults(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})

    def test_with_required(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, required=True)
        self.assertTrue(field.required)
        self.assertFalse(field.allow_null)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})

    def test_with_description(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, description='A description')
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel', 'description': 'A description'})

    def test_with_title(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, title='A title')
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel', 'title': 'A title'})

    def test_with_allow_null(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, allow_null=True)
        self.assertFalse(field.required)
        self.assertTrue(field.allow_null)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})

    def test_with_readonly(self):
        api = Api(self.app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, readonly=True)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel', 'readOnly': True})

    def test_as_list(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, as_list=True)
        self.assertTrue(field.as_list)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}})

    def test_as_list_is_reusable(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})

        field = fields.Nested(nested_fields, as_list=True)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}})

        field = fields.Nested(nested_fields)
        self.assertEqual(field.__schema__, {'$ref': '#/definitions/NestedModel'})


class ListFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.List, fields.String)

    def test_defaults(self):
        field = fields.List(fields.String)
        self.assertFalse(field.required)
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'type': 'string'}})

    def test_with_nested_field(self):
        nested_fields = self.api.model('NestedModel', {'name': fields.String})
        field = fields.List(fields.Nested(nested_fields))
        self.assertEqual(field.__schema__, {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}})

    def test_min_items(self):
        field = fields.List(fields.String, min_items=5)
        self.assertIn('minItems', field.__schema__)
        self.assertEqual(field.__schema__['minItems'], 5)

    def test_max_items(self):
        field = fields.List(fields.String, max_items=42)
        self.assertIn('maxItems', field.__schema__)
        self.assertEqual(field.__schema__['maxItems'], 42)

    def test_unique(self):
        field = fields.List(fields.String, unique=True)
        self.assertIn('uniqueItems', field.__schema__)
        self.assertEqual(field.__schema__['uniqueItems'], True)


class ClassNameFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = fields.ClassName

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
