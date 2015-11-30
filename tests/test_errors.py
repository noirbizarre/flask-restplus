# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from flask import Blueprint
from flask.ext import restplus

from . import TestCase


class APITestCase(TestCase):
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

    def test_errorhandler_for_custom_exception(self):
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

    def test_default_errorhandler(self):
        api = restplus.Api(self.app)

        @api.route('/test/')
        class TestResource(restplus.Resource):
            def get(self):
                raise Exception('error')

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 500)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertIn('message', data)

    def test_default_errorhandler_with_propagate_true(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint)

        @api.route('/test/')
        class TestResource(restplus.Resource):
            def get(self):
                raise Exception('error')

        self.app.register_blueprint(blueprint)

        self.app.config['PROPAGATE_EXCEPTIONS'] = True
        with self.app.test_client() as client:
            response = client.get('/api/test/')
            self.assertEquals(response.status_code, 500)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertIn('message', data)

    def test_custom_default_errorhandler(self):
        api = restplus.Api(self.app)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise Exception('error')

        @api.errorhandler
        def default_error_handler(error):
            return {'message': str(error), 'test': 'value'}, 500

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 500)
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
