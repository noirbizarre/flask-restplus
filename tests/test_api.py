# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for, Blueprint

import flask_restplus as restplus

from . import TestCase


class APITestCase(TestCase):
    def test_root_endpoint(self):
        api = restplus.Api(self.app, version='1.0')

        with self.context():
            url = url_for('root')
            self.assertEqual(url, '/')
            self.assertEqual(api.base_url, 'http://localhost/')

    def test_root_endpoint_lazy(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app)

        with self.context():
            url = url_for('root')
            self.assertEqual(url, '/')
            self.assertEqual(api.base_url, 'http://localhost/')

    def test_root_endpoint_with_blueprint(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint, version='1.0')
        self.app.register_blueprint(blueprint)

        with self.context():
            url = url_for('api.root')
            self.assertEqual(url, '/api/')
            self.assertEqual(api.base_url, 'http://localhost/api/')

    def test_root_endpoint_with_blueprint_with_subdomain(self):
        blueprint = Blueprint('api', __name__, subdomain='api', url_prefix='/api')
        api = restplus.Api(blueprint, version='1.0')
        self.app.register_blueprint(blueprint)

        with self.context():
            url = url_for('api.root')
            self.assertEqual(url, 'http://api.localhost/api/')
            self.assertEqual(api.base_url, 'http://api.localhost/api/')

    def test_parser(self):
        api = restplus.Api()
        self.assertIsInstance(api.parser(), restplus.reqparse.RequestParser)

    def test_doc_decorator(self):
        api = restplus.Api(self.app, prefix='/api', version='1.0')
        params = {'q': {'description': 'some description'}}

        @api.doc(params=params)
        class TestResource(restplus.Resource):
            pass

        self.assertTrue(hasattr(TestResource, '__apidoc__'))
        self.assertEqual(TestResource.__apidoc__, {'params': params})

    def test_doc_with_inheritance(self):
        api = restplus.Api(self.app, prefix='/api', version='1.0')
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

    def test_specs_endpoint_not_added(self):
        api = restplus.Api()
        api.init_app(self.app, add_specs=False)
        self.assertNotIn('specs', api.endpoints)
        self.assertNotIn('specs', self.app.view_functions)

    def test_specs_endpoint_not_found_if_not_added(self):
        api = restplus.Api()
        api.init_app(self.app, add_specs=False)
        with self.app.test_client() as client:
            resp = client.get('/swagger.json')
        self.assertEqual(resp.status_code, 404)

    def test_default_endpoint(self):
        api = restplus.Api(self.app)

        @api.route('/test/')
        class TestResource(restplus.Resource):
            pass

        with self.context():
            self.assertEqual(url_for('test_resource'), '/test/')

    def test_default_endpoint_lazy(self):
        api = restplus.Api()

        @api.route('/test/')
        class TestResource(restplus.Resource):
            pass

        api.init_app(self.app)

        with self.context():
            self.assertEqual(url_for('test_resource'), '/test/')

    def test_default_endpoint_with_blueprint(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint)
        self.app.register_blueprint(blueprint)

        @api.route('/test/')
        class TestResource(restplus.Resource):
            pass

        with self.context():
            self.assertEqual(url_for('api.test_resource'), '/api/test/')

    def test_default_endpoint_with_blueprint_with_subdomain(self):
        blueprint = Blueprint('api', __name__, subdomain='api', url_prefix='/api')
        api = restplus.Api(blueprint)
        self.app.register_blueprint(blueprint)

        @api.route('/test/')
        class TestResource(restplus.Resource):
            pass

        with self.context():
            self.assertEqual(url_for('api.test_resource'), 'http://api.localhost/api/test/')

    def test_default_endpoint_for_namespace(self):
        api = restplus.Api(self.app)
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/test/')
        class TestResource(restplus.Resource):
            pass

        with self.context():
            self.assertEqual(url_for('ns_test_resource'), '/ns/test/')

    def test_default_endpoint_lazy_for_namespace(self):
        api = restplus.Api()
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/test/')
        class TestResource(restplus.Resource):
            pass

        api.init_app(self.app)

        with self.context():
            self.assertEqual(url_for('ns_test_resource'), '/ns/test/')

    def test_default_endpoint_for_namespace_with_blueprint(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint)
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/test/')
        class TestResource(restplus.Resource):
            pass

        self.app.register_blueprint(blueprint)

        with self.context():
            self.assertEqual(url_for('api.ns_test_resource'), '/api/ns/test/')

    def test_multiple_default_endpoint(self):
        api = restplus.Api(self.app)

        @api.route('/test2/')
        @api.route('/test/')
        class TestResource(restplus.Resource):
            pass

        with self.context():
            self.assertEqual(url_for('test_resource'), '/test/')
            self.assertEqual(url_for('test_resource_2'), '/test2/')

    def test_multiple_default_endpoint_lazy(self):
        api = restplus.Api()

        @api.route('/test2/')
        @api.route('/test/')
        class TestResource(restplus.Resource):
            pass

        api.init_app(self.app)

        with self.context():
            self.assertEqual(url_for('test_resource'), '/test/')
            self.assertEqual(url_for('test_resource_2'), '/test2/')

    def test_multiple_default_endpoint_for_namespace(self):
        api = restplus.Api(self.app)
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/test2/')
        @ns.route('/test/')
        class TestResource(restplus.Resource):
            pass

        with self.context():
            self.assertEqual(url_for('ns_test_resource'), '/ns/test/')
            self.assertEqual(url_for('ns_test_resource_2'), '/ns/test2/')

    def test_multiple_default_endpoint_lazy_for_namespace(self):
        api = restplus.Api()
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/test2/')
        @ns.route('/test/')
        class TestResource(restplus.Resource):
            pass

        api.init_app(self.app)

        with self.context():
            self.assertEqual(url_for('ns_test_resource'), '/ns/test/')
            self.assertEqual(url_for('ns_test_resource_2'), '/ns/test2/')

    def test_multiple_default_endpoint_for_namespace_with_blueprint(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint)
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/test2/')
        @ns.route('/test/')
        class TestResource(restplus.Resource):
            pass

        self.app.register_blueprint(blueprint)

        with self.context():
            self.assertEqual(url_for('api.ns_test_resource'), '/api/ns/test/')
            self.assertEqual(url_for('api.ns_test_resource_2'), '/api/ns/test2/')
