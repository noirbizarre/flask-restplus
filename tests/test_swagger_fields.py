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
