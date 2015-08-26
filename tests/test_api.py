# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from flask import url_for, Blueprint
from flask.ext import restplus

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
        # api.init_app(self.app)
        self.app.register_blueprint(blueprint)

        with self.context():
            url = url_for('api.root')
            self.assertEqual(url, '/api/')
            self.assertEqual(api.base_url, 'http://localhost/api/')

    def test_abort_code_only_with_defaults(self):
        api = restplus.Api(self.app)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                api.abort(403)

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 403)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertIn('message', data)

    def test_abort_with_message(self):
        api = restplus.Api(self.app)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                api.abort(403, 'A message')

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 403)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertEqual(data['message'], 'A message')

    def test_abort_with_lazy_init(self):
        api = restplus.Api()

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                api.abort(403)

        api.init_app(self.app)

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 403)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertIn('message', data)

    def test_abort_on_exception(self):
        api = restplus.Api(self.app)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise ValueError()

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 500)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertIn('message', data)

    def test_abort_on_exception_with_lazy_init(self):
        api = restplus.Api()

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise ValueError()

        api.init_app(self.app)

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 500)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertIn('message', data)

    def test_errorhandler(self):
        api = restplus.Api(self.app)

        class CustomException(RuntimeError):
            pass

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise CustomException('error')

        @api.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {'message': str(error), 'test': 'value'}, 400

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertEqual(data, {
                'message': 'error',
                'test': 'value',
            })

    def test_errorhandler_lazy(self):
        api = restplus.Api()

        class CustomException(RuntimeError):
            pass

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise CustomException('error')

        @api.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {'message': str(error), 'test': 'value'}, 400

        api.init_app(self.app)

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertEqual(data, {
                'message': 'error',
                'test': 'value',
            })

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
