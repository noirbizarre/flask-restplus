# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import flask_restplus as restplus

from flask_restplus import Namespace


class NamespaceTest(object):
    def test_parser(self):
        api = Namespace('test')
        assert isinstance(api.parser(), restplus.reqparse.RequestParser)

    def test_doc_decorator(self):
        api = Namespace('test')
        params = {'q': {'description': 'some description'}}

        @api.doc(params=params)
        class TestResource(restplus.Resource):
            pass

        assert hasattr(TestResource, '__apidoc__')
        assert TestResource.__apidoc__ == {'params': params}

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

        assert TestResource.__apidoc__ == {'params': {
            'q': {
                'description': 'some new description',
                'type': 'string',
                'paramType': 'query'
            },
            'other': {'description': 'another param'},
        }}

    def test_model(self):
        api = Namespace('test')
        api.model('Person', {})
        assert 'Person' in api.models

    def test_schema_model(self):
        api = Namespace('test')
        api.schema_model('Person', {})
        assert 'Person' in api.models

    def test_clone(self):
        api = Namespace('test')
        parent = api.model('Parent', {})
        api.clone('Child', parent, {})

        assert 'Child' in api.models
        assert 'Parent' in api.models

    def test_clone_with_multiple_parents(self):
        api = Namespace('test')
        grand_parent = api.model('GrandParent', {})
        parent = api.model('Parent', {})
        api.clone('Child', grand_parent, parent, {})

        assert 'Child' in api.models
        assert 'Parent' in api.models
        assert 'GrandParent' in api.models

    def test_inherit(self):
        api = Namespace('test')
        parent = api.model('Parent', {})
        api.inherit('Child', parent, {})

        assert 'Parent' in api.models
        assert 'Child' in api.models

    def test_inherit_from_multiple_parents(self):
        api = Namespace('test')
        grand_parent = api.model('GrandParent', {})
        parent = api.model('Parent', {})
        api.inherit('Child', grand_parent, parent, {})

        assert 'GrandParent' in api.models
        assert 'Parent' in api.models
        assert 'Child' in api.models
