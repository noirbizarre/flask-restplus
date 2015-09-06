# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import json

from os.path import join, dirname

from jsonschema import validate
from werkzeug.datastructures import FileStorage

from flask.ext import restplus

from . import TestCase

try:
    from urlparse import parse_qs, urlparse
except:
    from urllib.parse import urlparse, parse_qs


with open(join(dirname(__file__), 'postman-v1.schema.json')) as f:
    schema = json.load(f)


class PostmanTestCase(TestCase):
    def setUp(self):
        super(PostmanTestCase, self).setUp()
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearsDown(self):
        super(PostmanTestCase, self).tearsDown()
        self.ctx.pop()

    def test_basic_export(self):
        api = restplus.Api(self.app)

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(len(data['requests']), 0)

    def test_export_infos(self):
        api = restplus.Api(self.app, version='1.0',
            title='My API',
            description='This is a testing API',
        )

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(data['name'], 'My API 1.0')
        self.assertEqual(data['description'], 'This is a testing API')

    def test_export_with_one_entry(self):
        api = restplus.Api(self.app)

        @api.route('/test')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                '''A test post'''
                pass

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(len(data['requests']), 1)
        request = data['requests'][0]
        self.assertEqual(request['name'], 'test_post')
        self.assertEqual(request['description'], 'A test post')

        self.assertEqual(len(data['folders']), 1)
        folder = data['folders'][0]
        self.assertEqual(folder['name'], 'default')
        self.assertEqual(folder['description'], 'Default namespace')

        self.assertEqual(request['folder'], folder['id'])

    def test_export_with_namespace(self):
        api = restplus.Api(self.app)
        ns = api.namespace('test', 'A test namespace')

        @ns.route('/test')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                '''A test post'''
                pass

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(len(data['requests']), 1)
        request = data['requests'][0]
        self.assertEqual(request['name'], 'test_post')
        self.assertEqual(request['description'], 'A test post')

        self.assertEqual(len(data['folders']), 2)
        folder = data['folders'][1]
        self.assertEqual(folder['name'], 'test')
        self.assertEqual(folder['description'], 'A test namespace')

        self.assertEqual(request['folder'], folder['id'])

    def test_id_is_the_same(self):
        api = restplus.Api(self.app)

        first = api.as_postman()

        second = api.as_postman()

        self.assertEqual(first['id'], second['id'])

    def test_resources_order_in_folder(self):
        '''It should preserve resources order'''
        api = restplus.Api(self.app)
        ns = api.namespace('test', 'A test namespace')

        @ns.route('/test1')
        class Test1(restplus.Resource):
            @api.doc('test_post_z')
            def post(self):
                pass

        @ns.route('/test2')
        class Test2(restplus.Resource):
            @api.doc('test_post_y')
            def post(self):
                pass

        @ns.route('/test3')
        class Test3(restplus.Resource):
            @api.doc('test_post_x')
            def post(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(len(data['requests']), 3)

        self.assertEqual(len(data['folders']), 2)
        folder = data['folders'][1]
        self.assertEqual(folder['name'], 'test')

        expected_order = ('test_post_z', 'test_post_y', 'test_post_x')
        self.assertEqual(len(folder['order']), len(expected_order))

        for request_id, expected in zip(folder['order'], expected_order):
            request = list(filter(lambda r: r['id'] == request_id, data['requests']))[0]
            self.assertEqual(request['name'], expected)

    def test_path_variables(self):
        api = restplus.Api(self.app)

        @api.route('/test/<id>/<int:integer>/<float:number>/')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(len(data['requests']), 1)
        request = data['requests'][0]
        self.assertEqual(request['url'], 'http://localhost/test/:id/:integer/:number/')
        self.assertEqual(request['pathVariables'], {
            'id': '',
            'integer': 0,
            'number': 0,
        })

    def test_url_variables_disabled(self):
        api = restplus.Api(self.app)

        parser = api.parser()
        parser.add_argument('int', type=int)
        parser.add_argument('default', type=int, default=5)
        parser.add_argument('str', type=str)

        @api.route('/test/')
        class Test(restplus.Resource):
            @api.doc(parser=parser)
            def get(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        self.assertEqual(len(data['requests']), 1)
        request = data['requests'][0]
        self.assertEqual(request['url'], 'http://localhost/test/')

    def test_url_variables_enabled(self):
        api = restplus.Api(self.app)

        parser = api.parser()
        parser.add_argument('int', type=int)
        parser.add_argument('default', type=int, default=5)
        parser.add_argument('str', type=str)

        @api.route('/test/')
        class Test(restplus.Resource):
            @api.doc(parser=parser)
            def get(self):
                pass

        data = api.as_postman(urlvars=True)

        validate(data, schema)

        self.assertEqual(len(data['requests']), 1)
        request = data['requests'][0]
        qs = parse_qs(urlparse(request['url']).query, keep_blank_values=True)

        self.assertIn('int', qs)
        self.assertEqual(qs['int'][0], '0')

        self.assertIn('default', qs)
        self.assertEqual(qs['default'][0], '5')

        self.assertIn('str', qs)
        self.assertEqual(qs['str'][0], '')

    def test_headers(self):
        api = restplus.Api(self.app)

        @api.route('/headers/')
        class TestHeaders(restplus.Resource):
            @api.doc('headers')
            @api.header('X-Header-1', default='xxx')
            @api.header('X-Header-2', required=True)
            def get(self):
                pass

        data = api.as_postman(urlvars=True)

        validate(data, schema)
        request = data['requests'][0]
        headers = dict(r.split(':') for r in request['headers'].splitlines())

        self.assertEqual(headers['X-Header-1'], 'xxx')
        self.assertEqual(headers['X-Header-2'], '')

    def test_content_type_header(self):
        api = restplus.Api(self.app)
        form_parser = api.parser()
        form_parser.add_argument('param', type=int, help='Some param', location='form')

        file_parser = api.parser()
        file_parser.add_argument('in_files', type=FileStorage, location='files')

        @api.route('/json/')
        class TestJson(restplus.Resource):
            @api.doc('json')
            def post(self):
                pass

        @api.route('/form/')
        class TestForm(restplus.Resource):
            @api.doc('form', parser=form_parser)
            def post(self):
                pass

        @api.route('/file/')
        class TestFile(restplus.Resource):
            @api.doc('file', parser=file_parser)
            def post(self):
                pass

        @api.route('/get/')
        class TestGet(restplus.Resource):
            @api.doc('get')
            def get(self):
                pass

        data = api.as_postman(urlvars=True)

        validate(data, schema)
        requests = dict((r['name'], r['headers']) for r in data['requests'])

        self.assertEqual(requests['json'], 'Content-Type:application/json')
        self.assertEqual(requests['form'], 'Content-Type:multipart/form-data')
        self.assertEqual(requests['file'], 'Content-Type:multipart/form-data')

        # No content-type on get
        self.assertEqual(requests['get'], '')

    def test_method_security_headers(self):
        api = restplus.Api(self.app, authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })

        @api.route('/secure/')
        class Secure(restplus.Resource):
            @api.doc('secure', security='apikey')
            def get(self):
                pass

        @api.route('/unsecure/')
        class Unsecure(restplus.Resource):
            @api.doc('unsecure')
            def get(self):
                pass

        data = api.as_postman()

        validate(data, schema)
        requests = dict((r['name'], r['headers']) for r in data['requests'])

        self.assertEqual(requests['unsecure'], '')
        self.assertEqual(requests['secure'], 'X-API:')

    def test_global_security_headers(self):
        api = restplus.Api(self.app, security='apikey', authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })

        @api.route('/test/')
        class Test(restplus.Resource):
            def get(self):
                pass

        data = api.as_postman()

        validate(data, schema)
        request = data['requests'][0]
        headers = dict(r.split(':') for r in request['headers'].splitlines())

        self.assertEqual(headers['X-API'], '')

    def test_export_with_swagger(self):
        api = restplus.Api(self.app)

        data = api.as_postman(swagger=True)

        validate(data, schema)

        self.assertEqual(len(data['requests']), 1)
        request = data['requests'][0]
        self.assertEqual(request['name'], 'Swagger specifications')
        self.assertEqual(request['description'], 'The API Swagger specifications as JSON')
        self.assertEqual(request['url'], 'http://localhost/swagger.json')
