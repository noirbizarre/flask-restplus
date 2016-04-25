# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from flask import Blueprint, abort
from flask.signals import got_request_exception

from werkzeug.exceptions import HTTPException, BadRequest, NotFound
from werkzeug.http import quote_etag, unquote_etag

import flask_restplus as restplus

from . import TestCase, Mock


class ErrorsTest(TestCase):
    def test_abort_type(self):
        with self.assertRaises(HTTPException):
            restplus.abort(404)

    def test_abort_data(self):
        with self.assertRaises(HTTPException) as cm:
            restplus.abort(404, foo='bar')
        self.assertEquals(cm.exception.data, {'foo': 'bar'})

    def test_abort_no_data(self):
        with self.assertRaises(HTTPException) as cm:
            restplus.abort(404)
        self.assertFalse(hasattr(cm.exception, 'data'))

    def test_abort_custom_message(self):
        with self.assertRaises(HTTPException) as cm:
            restplus.abort(404, 'My message')
        self.assertEquals(cm.exception.data['message'], 'My message')

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

    def test_errorhandler_for_custom_exception_with_headers(self):
        api = restplus.Api(self.app)

        class CustomException(RuntimeError):
            pass

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise CustomException('error')

        @api.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {'message': 'some maintenance'}, 503, {'Retry-After': 120}

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 503)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertEqual(data, {
                'message': 'some maintenance'
            })
            self.assertEqual(response.headers['Retry-After'], '120')

    def test_errorhandler_for_httpexception(self):
        api = restplus.Api(self.app)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise BadRequest()

        @api.errorhandler(BadRequest)
        def handle_badrequest_exception(error):
            return {'message': str(error), 'test': 'value'}, 400

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertEqual(data, {
                'message': '400: Bad Request',
                'test': 'value',
            })

    def test_errorhandler_with_namespace(self):
        api = restplus.Api(self.app)

        ns = restplus.Namespace("ExceptionHandler", path="/")

        class CustomException(RuntimeError):
            pass

        @ns.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise CustomException('error')

        @ns.errorhandler(CustomException)
        def handle_custom_exception(error):
            return {'message': str(error), 'test': 'value'}, 400

        api.add_namespace(ns)

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

    def test_custom_default_errorhandler_with_headers(self):
        api = restplus.Api(self.app)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                raise Exception('error')

        @api.errorhandler
        def default_error_handler(error):
            return {'message': 'some maintenance'}, 503, {'Retry-After': 120}

        with self.app.test_client() as client:
            response = client.get('/test/')
            self.assertEquals(response.status_code, 503)
            self.assertEquals(response.content_type, 'application/json')

            data = json.loads(response.data.decode('utf8'))
            self.assertEqual(data, {
                'message': 'some maintenance'
            })
            self.assertEqual(response.headers['Retry-After'], '120')

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

    def test_handle_api_error(self):
        api = restplus.Api(self.app)

        @api.route('/api', endpoint='api')
        class Test(restplus.Resource):
            def get(self):
                abort(404)

        with self.app.test_client() as client:
            response = client.get("/api")
            self.assertEquals(response.status_code, 404)
            self.assertEquals(response.headers['Content-Type'], 'application/json')
            data = json.loads(response.data.decode())
            self.assertIn('message', data)

    def test_handle_non_api_error(self):
        restplus.Api(self.app)

        with self.app.test_client() as client:
            response = client.get("/foo")
            self.assertEquals(response.status_code, 404)
            self.assertEquals(response.headers['Content-Type'], 'text/html')

    def test_non_api_error_404_catchall(self):
        api = restplus.Api(self.app, catch_all_404s=True)

        with self.app.test_client() as client:
            response = client.get("/foo")
            self.assertEquals(response.headers['Content-Type'], api.default_mediatype)

    def test_handle_error_signal(self):
        api = restplus.Api(self.app)

        exception = BadRequest()

        recorded = []

        def record(sender, exception):
            recorded.append(exception)

        got_request_exception.connect(record, self.app)
        try:
            with self.app.test_request_context("/foo"):
                api.handle_error(exception)
                self.assertEquals(len(recorded), 1)
                self.assertTrue(exception is recorded[0])
        finally:
            got_request_exception.disconnect(record, self.app)

    def test_handle_error(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            response = api.handle_error(BadRequest())
            self.assertEquals(response.status_code, 400)
            self.assertEquals(json.loads(response.data.decode()), {
                'message': BadRequest.description,
            })

    def test_handle_error_does_not_duplicate_content_length(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            response = api.handle_error(BadRequest())
            self.assertEqual(len(response.headers.getlist('Content-Length')), 1)

    def test_handle_smart_errors(self):
        api = restplus.Api(self.app)
        view = restplus.Resource

        api.add_resource(view, '/foo', endpoint='bor')
        api.add_resource(view, '/fee', endpoint='bir')
        api.add_resource(view, '/fii', endpoint='ber')

        with self.app.test_request_context("/faaaaa"):
            response = api.handle_error(NotFound())
            self.assertEquals(response.status_code, 404)
            self.assertEquals(json.loads(response.data.decode()), {
                'message': NotFound.description,
            })

        with self.app.test_request_context("/fOo"):
            response = api.handle_error(NotFound())
            self.assertEquals(response.status_code, 404)
            self.assertTrue('did you mean /foo ?' in response.data.decode())

        self.app.config['ERROR_404_HELP'] = False

        with self.app.test_request_context("/fOo"):
            response = api.handle_error(NotFound())
            self.assertEquals(response.status_code, 404)
            self.assertEquals(json.loads(response.data.decode()), {
                'message': NotFound.description
            })

    def test_error_router_falls_back_to_original(self):
        api = restplus.Api(self.app)
        self.app.handle_exception = Mock()
        api.handle_error = Mock(side_effect=Exception())
        api._has_fr_route = Mock(return_value=True)
        exception = Mock(spec=HTTPException)

        with self.app.test_request_context('/foo'):
            api.error_router(self.app.handle_exception, exception)

        self.app.handle_exception.assert_called_with(exception)

    def test_fr_405(self):
        api = restplus.Api(self.app)

        @api.route('/ids/<int:id>', endpoint='hello')
        class HelloWorld(restplus.Resource):
            def get(self):
                return {}

        with self.app.test_client() as client:
            response = client.post('/ids/3')
            self.assertEquals(response.status_code, 405)
            self.assertEquals(response.content_type, api.default_mediatype)
            # Allow can be of the form 'GET, PUT, POST'
            allow = ', '.join(set(response.headers.get_all('Allow')))
            allow = set(method.strip() for method in allow.split(','))
            self.assertEquals(allow, set(['HEAD', 'OPTIONS', 'GET']))

    def test_exception_header_forwarded(self):
        '''Ensure that HTTPException's headers are extended properly'''
        self.app.config['DEBUG'] = True
        api = restplus.Api(self.app)

        class NotModified(HTTPException):
            code = 304

            def __init__(self, etag, *args, **kwargs):
                super(NotModified, self).__init__(*args, **kwargs)
                self.etag = quote_etag(etag)

            def get_headers(self, *args, **kwargs):
                return [('ETag', self.etag)]

        @api.route('/foo')
        class Foo1(restplus.Resource):
            def get(self):
                abort(304, etag='myETag')

        abort.mapping.update({304: NotModified})

        with self.app.test_client() as client:
            foo = client.get('/foo')
            self.assertEquals(foo.get_etag(),
                              unquote_etag(quote_etag('myETag')))

    def test_handle_server_error(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            resp = api.handle_error(Exception())
            self.assertEquals(resp.status_code, 500)
            self.assertEquals(json.loads(resp.data.decode()), {
                'message': "Internal Server Error"
            })

    def test_handle_error_with_code(self):
        api = restplus.Api(self.app, serve_challenge_on_401=True)

        exception = Exception()
        exception.code = "Not an integer"
        exception.data = {'foo': 'bar'}

        with self.app.test_request_context("/foo"):
            response = api.handle_error(exception)
            self.assertEquals(response.status_code, 500)
            self.assertEquals(json.loads(response.data.decode()), {"foo": "bar"})

    def test_errorhandler_swagger_doc(self):
        api = restplus.Api(self.app)

        class CustomException(RuntimeError):
            pass

        error = api.model('Error', {
            'message': restplus.fields.String()
        })

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                '''
                Do something

                :raises CustomException: In case of something
                '''
                pass

        @api.errorhandler(CustomException)
        @api.header('Custom-Header', 'Some custom header')
        @api.marshal_with(error, code=503)
        def handle_custom_exception(error):
            '''Some description'''
            pass

        specs = self.get_specs()

        self.assertIn('Error', specs['definitions'])
        self.assertIn('CustomException', specs['responses'])

        response = specs['responses']['CustomException']
        self.assertEqual(response['description'], 'Some description')
        self.assertEqual(response['schema'], {
            '$ref': '#/definitions/Error'
        })
        self.assertEqual(response['headers'], {
            'Custom-Header': {
                'description': 'Some custom header',
                'type': 'string'
            }
        })

        operation = specs['paths']['/test/']['get']
        self.assertIn('responses', operation)
        self.assertEqual(operation['responses'], {
            '503': {
                '$ref': '#/responses/CustomException'
            }
        })
