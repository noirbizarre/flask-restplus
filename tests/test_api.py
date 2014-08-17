# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from flask import url_for
from flask.ext import restplus

from . import TestCase


class APITestCase(TestCase):
    def test_root_endpoint(self):
        api = restplus.Api(self.app, version='1.0')

        with self.context():
            url = url_for('api.root')
            self.assertEqual(url, '/')
            self.assertEqual(api.base_url, 'http://localhost/')

        with self.app.test_client() as client:
            response = client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_root_endpoint_lazy(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app)

        with self.context():
            url = url_for('api.root')
            self.assertEqual(url, '/')
            self.assertEqual(api.base_url, 'http://localhost/')

        with self.app.test_client() as client:
            response = client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_root_endpoint_with_params(self):
        api = restplus.Api(version='1.0', prefix='/api', endpoint='apiv1')
        api.init_app(self.app)

        with self.context():
            url = url_for('apiv1.root')
            self.assertEqual(url, '/api/')
            self.assertEqual(api.base_url, 'http://localhost/api/')

        with self.app.test_client() as client:
            response = client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_specs_endpoint(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app)

        data = self.get_specs('')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['apis'], [])
        self.assertNotIn('infos', data)

    def test_specs_endpoint_infos(self):
        api = restplus.Api(version='1.0',
            title='My API',
            description='This is a testing API',
            terms_url='http://somewhere.com/terms/',
            contact='contact@somewhere.com',
            license='Apache 2.0',
            license_url='http://www.apache.org/licenses/LICENSE-2.0.html'
        )
        api.init_app(self.app)

        data = self.get_specs('')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['apis'], [])

        self.assertIn('infos', data)
        self.assertEqual(data['infos']['title'], 'My API')
        self.assertEqual(data['infos']['description'], 'This is a testing API')
        self.assertEqual(data['infos']['termsOfServiceUrl'], 'http://somewhere.com/terms/')
        self.assertEqual(data['infos']['contact'], 'contact@somewhere.com')
        self.assertEqual(data['infos']['license'], 'Apache 2.0')
        self.assertEqual(data['infos']['licenseUrl'], 'http://www.apache.org/licenses/LICENSE-2.0.html')

    def test_specs_endpoint_infos_delayed(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app,
            title='My API',
            description='This is a testing API',
            terms_url='http://somewhere.com/terms/',
            contact='contact@somewhere.com',
            license='Apache 2.0',
            license_url='http://www.apache.org/licenses/LICENSE-2.0.html'
        )

        data = self.get_specs('')

        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['apis'], [])

        self.assertIn('infos', data)
        self.assertEqual(data['infos']['title'], 'My API')
        self.assertEqual(data['infos']['description'], 'This is a testing API')
        self.assertEqual(data['infos']['termsOfServiceUrl'], 'http://somewhere.com/terms/')
        self.assertEqual(data['infos']['contact'], 'contact@somewhere.com')
        self.assertEqual(data['infos']['license'], 'Apache 2.0')
        self.assertEqual(data['infos']['licenseUrl'], 'http://www.apache.org/licenses/LICENSE-2.0.html')

    def test_specs_authorizations(self):
        authorizations = {
            'apikey': {
                'type': 'apiKey',
                'passAs': 'header',
                'keyname': 'X-API'
            }
        }
        restplus.Api(self.app, authorizations=authorizations)

        data = self.get_specs('')

        self.assertIn('authorizations', data)
        self.assertEqual(data['authorizations'], authorizations)

    def test_default_ns_resource_documentation_with_override(self):
        api = restplus.Api(self.app, prefix='/api', version='1.0',
            default='site', default_label='Site namespace')

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs()
        apis = data['apis']
        self.assertEqual(len(apis), 1)
        self.assertEqual(apis[0]['path'], 'http://localhost/api/site.json')
        self.assertEqual(apis[0]['description'], 'Site namespace')

        data = self.get_declaration('site')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['basePath'], 'http://localhost/api')
        self.assertEqual(data['resourcePath'], '/')
        self.assertEqual(len(data['apis']), 1)

        test_api = data['apis'][0]
        self.assertEqual(test_api['path'], '/test/')
        self.assertEqual(len(test_api['operations']), 1)

        with self.context():
            self.assertEqual(url_for('api.site-declaration'), '/api/site.json')
            self.assertEqual(url_for('api.test'), '/api/test/')

    def test_default_ns_resource_documentation(self):
        api = restplus.Api(self.app, prefix='/api', version='1.0')

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs()
        apis = data['apis']
        self.assertEqual(len(apis), 1)
        self.assertEqual(apis[0]['path'], 'http://localhost/api/default.json')
        self.assertEqual(apis[0]['description'], 'Default namespace')

        data = self.get_declaration('default')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['basePath'], 'http://localhost/api')
        self.assertEqual(data['resourcePath'], '/')
        self.assertEqual(len(data['apis']), 1)

        test_api = data['apis'][0]
        self.assertEqual(test_api['path'], '/test/')
        self.assertEqual(len(test_api['operations']), 1)

        with self.context():
            self.assertEqual(url_for('api.test'), '/api/test/')

    def test_ns_resource_documentation(self):
        api = restplus.Api(self.app, prefix='/api', version='1.0')
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs()
        apis = data['apis']
        self.assertEqual(len(apis), 1)
        self.assertEqual(apis[0]['path'], 'http://localhost/api/ns.json')
        self.assertEqual(apis[0]['description'], 'Test namespace')

        data = self.get_declaration('ns')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['basePath'], 'http://localhost/api')
        self.assertEqual(data['resourcePath'], '/ns')

        test_api = data['apis'][0]
        self.assertEqual(test_api['path'], '/ns/')
        self.assertEqual(len(test_api['operations']), 1)
        with self.context():
            self.assertEqual(url_for('api.test'), '/api/ns/')

    def test_ns_resource_documentation_lazy(self):
        api = restplus.Api(prefix='/api', version='1.0')
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        api.init_app(self.app)

        data = self.get_specs()
        apis = data['apis']
        self.assertEqual(len(apis), 1)
        self.assertEqual(apis[0]['path'], 'http://localhost/api/ns.json')
        self.assertEqual(apis[0]['description'], 'Test namespace')

        data = self.get_declaration('ns')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['basePath'], 'http://localhost/api')
        self.assertEqual(data['resourcePath'], '/ns')

        test_api = data['apis'][0]
        self.assertEqual(test_api['path'], '/ns/')
        self.assertEqual(len(test_api['operations']), 1)
        with self.context():
            self.assertEqual(url_for('api.test'), '/api/ns/')

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
            self.assertEqual(data['status'], 403)
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
            self.assertEqual(data['status'], 403)
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
            self.assertEqual(data['status'], 403)
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
            self.assertEqual(data['status'], 500)
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
            self.assertEqual(data['status'], 500)
            self.assertIn('message', data)

    def test_parser(self):
        api = restplus.Api()
        self.assertIsInstance(api.parser(), restplus.reqparse.RequestParser)
