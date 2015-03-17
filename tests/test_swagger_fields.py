# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint
from flask.ext.restplus import fields, Api

from . import TestCase


class SwaggerFieldsTestCase(TestCase):
    def setUp(self):
        super(SwaggerFieldsTestCase, self).setUp()
        blueprint = Blueprint('api', __name__)
        self.api = Api(blueprint)
        self.app.register_blueprint(blueprint)

    def test_classname_field(self):
        model = self.api.model('Test', {
            'name': fields.ClassName(),
        })

        class FakeClass(object):
            pass

        data = self.api.marshal(FakeClass(), model)
        self.assertEqual(data, {'name': 'FakeClass'})

    def test_classname_field_dash(self):
        model = self.api.model('Test', {
            'name': fields.ClassName(dash=True),
        })

        class FakeClass(object):
            pass

        data = self.api.marshal(FakeClass(), model)
        self.assertEqual(data, {'name': 'fake_class'})

    def test_polymorph_field(self):
        parent = self.api.model('Person', {
            'name': fields.String,
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child1', parent, {
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

    def test_discriminator_field(self):
        model = self.api.model('Test', {
            'name': fields.String(discriminator=True),
        })

        data = self.api.marshal(object(), model)
        self.assertEqual(data, {'name': 'Test'})

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
