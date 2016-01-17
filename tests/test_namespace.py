# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for, Blueprint

import flask_restplus as restplus

from flask_restplus import Namespace, Api

from . import TestCase


class NamespaceTest(TestCase):
    def test_parser(self):
        api = Namespace('test')
        self.assertIsInstance(api.parser(), restplus.reqparse.RequestParser)

    def test_doc_decorator(self):
        api = Namespace('test')
        params = {'q': {'description': 'some description'}}

        @api.doc(params=params)
        class TestResource(restplus.Resource):
            pass

        self.assertTrue(hasattr(TestResource, '__apidoc__'))
        self.assertEqual(TestResource.__apidoc__, {'params': params})

    def test_doc_with_inheritance(self):
        api = Namespace('test')
        base_params = {'q': {'description': 'some description', 'type': 'string', 'paramType': 'query'}}
        child_params = {'q': {'description': 'some new description'}, 'other': {'description': 'another param'}}

        @api.doc(params=base_params)
        class BaseResource(restplus.Resource):
            pass

        @api.doc(params=child_params)
        class TestResource(BaseResource):
            pass

        self.assertEqual(TestResource.__apidoc__, {'params': {
            'q': {
                'description': 'some new description',
                'type': 'string',
                'paramType': 'query'
            },
            'other': {'description': 'another param'},
        }})

    def test_model(self):
        api = Namespace('test')
        api.model('Person', {})
        self.assertIn('Person', api.models)

    def test_clone(self):
        api = Namespace('test')
        parent = api.model('Parent', {})
        api.clone('Child', parent, {})

        self.assertIn('Child', api.models)
        self.assertIn('Parent', api.models)

    def test_clone_with_multiple_parents(self):
        api = Namespace('test')
        grand_parent = api.model('GrandParent', {})
        parent = api.model('Parent', {})
        api.clone('Child', grand_parent, parent, {})

        self.assertIn('Child', api.models)
        self.assertIn('Parent', api.models)
        self.assertIn('GrandParent', api.models)

    def test_inherit(self):
        api = Namespace('test')
        parent = api.model('Parent', {})
        api.inherit('Child', parent, {})

        self.assertIn('Parent', api.models)
        self.assertIn('Child', api.models)

    def test_inherit_from_multiple_parents(self):
        api = Namespace('test')
        grand_parent = api.model('GrandParent', {})
        parent = api.model('Parent', {})
        api.inherit('Child', grand_parent, parent, {})

        self.assertIn('GrandParent', api.models)
        self.assertIn('Parent', api.models)
        self.assertIn('Child', api.models)
