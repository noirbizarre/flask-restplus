# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import json

from os.path import join, dirname

from jsonschema import validate
from werkzeug.datastructures import FileStorage

import flask_restplus as restplus

from six.moves.urllib.parse import parse_qs, urlparse


with open(join(dirname(__file__), 'postman-v1.schema.json')) as f:
    schema = json.load(f)


class PostmanTest(object):
    def test_basic_export(self, app):
        api = restplus.Api(app)

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 0

    def test_export_infos(self, app):
        api = restplus.Api(app, version='1.0',
            title='My API',
            description='This is a testing API',
        )

        data = api.as_postman()

        validate(data, schema)

        assert data['name'] == 'My API 1.0'
        assert data['description'] == 'This is a testing API'

    def test_export_with_one_entry(self, app):
        api = restplus.Api(app)

        @api.route('/test')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                '''A test post'''
                pass

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['name'] == 'test_post'
        assert request['description'] == 'A test post'

        assert len(data['folders']) == 1
        folder = data['folders'][0]
        assert folder['name'] == 'default'
        assert folder['description'] == 'Default namespace'

        assert request['folder'] == folder['id']

    def test_export_with_namespace(self, app):
        api = restplus.Api(app)
        ns = api.namespace('test', 'A test namespace')

        @ns.route('/test')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                '''A test post'''
                pass

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['name'] == 'test_post'
        assert request['description'] == 'A test post'

        assert len(data['folders']) == 2
        folder = data['folders'][1]
        assert folder['name'] == 'test'
        assert folder['description'] == 'A test namespace'

        assert request['folder'] == folder['id']

    def test_id_is_the_same(self, app):
        api = restplus.Api(app)

        first = api.as_postman()

        second = api.as_postman()

        assert first['id'] == second['id']

    def test_resources_order_in_folder(self, app):
        '''It should preserve resources order'''
        api = restplus.Api(app)
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

        assert len(data['requests']) == 3

        assert len(data['folders']) == 2
        folder = data['folders'][1]
        assert folder['name'] == 'test'

        expected_order = ('test_post_z', 'test_post_y', 'test_post_x')
        assert len(folder['order']) == len(expected_order)

        for request_id, expected in zip(folder['order'], expected_order):
            request = list(filter(lambda r: r['id'] == request_id, data['requests']))[0]
            assert request['name'] == expected

    def test_prefix_with_trailing_slash(self, app):
        api = restplus.Api(app, prefix='/prefix/')

        @api.route('/test/')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['url'] == 'http://localhost/prefix/test/'

    def test_prefix_without_trailing_slash(self, app):
        api = restplus.Api(app, prefix='/prefix')

        @api.route('/test/')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['url'] == 'http://localhost/prefix/test/'

    def test_path_variables(self, app):
        api = restplus.Api(app)

        @api.route('/test/<id>/<int:integer>/<float:number>/')
        class Test(restplus.Resource):
            @api.doc('test_post')
            def post(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['url'] == 'http://localhost/test/:id/:integer/:number/'
        assert request['pathVariables'] == {
            'id': '',
            'integer': 0,
            'number': 0,
        }

    def test_url_variables_disabled(self, app):
        api = restplus.Api(app)

        parser = api.parser()
        parser.add_argument('int', type=int)
        parser.add_argument('default', type=int, default=5)
        parser.add_argument('str', type=str)

        @api.route('/test/')
        class Test(restplus.Resource):
            @api.expect(parser)
            def get(self):
                pass

        data = api.as_postman()

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['url'] == 'http://localhost/test/'

    def test_url_variables_enabled(self, app):
        api = restplus.Api(app)

        parser = api.parser()
        parser.add_argument('int', type=int)
        parser.add_argument('default', type=int, default=5)
        parser.add_argument('str', type=str)

        @api.route('/test/')
        class Test(restplus.Resource):
            @api.expect(parser)
            def get(self):
                pass

        data = api.as_postman(urlvars=True)

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        qs = parse_qs(urlparse(request['url']).query, keep_blank_values=True)

        assert 'int' in qs
        assert qs['int'][0] == '0'

        assert 'default' in qs
        assert qs['default'][0] == '5'

        assert 'str' in qs
        assert qs['str'][0] == ''

    def test_headers(self, app):
        api = restplus.Api(app)

        parser = api.parser()
        parser.add_argument('X-Header-1', location='headers', default='xxx')
        parser.add_argument('X-Header-2', location='headers', required=True)

        @api.route('/headers/')
        class TestHeaders(restplus.Resource):
            @api.doc('headers')
            @api.expect(parser)
            def get(self):
                pass

        data = api.as_postman(urlvars=True)

        validate(data, schema)
        request = data['requests'][0]
        headers = dict(r.split(':') for r in request['headers'].splitlines())

        assert headers['X-Header-1'] == 'xxx'
        assert headers['X-Header-2'] == ''

    def test_content_type_header(self, app):
        api = restplus.Api(app)
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
            @api.doc('form')
            @api.expect(form_parser)
            def post(self):
                pass

        @api.route('/file/')
        class TestFile(restplus.Resource):
            @api.doc('file')
            @api.expect(file_parser)
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

        assert requests['json'] == 'Content-Type:application/json'
        assert requests['form'] == 'Content-Type:multipart/form-data'
        assert requests['file'] == 'Content-Type:multipart/form-data'

        # No content-type on get
        assert requests['get'] == ''

    def test_method_security_headers(self, app):
        api = restplus.Api(app, authorizations={
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

        assert requests['unsecure'] == ''
        assert requests['secure'] == 'X-API:'

    def test_global_security_headers(self, app):
        api = restplus.Api(app, security='apikey', authorizations={
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

        assert headers['X-API'] == ''

    def test_oauth_security_headers(self, app):
        api = restplus.Api(app, security='oauth', authorizations={
            'oauth': {
                'type': 'oauth2',
                'authorizationUrl': 'https://somewhere.com/oauth/authorize',
                'flow': 'implicit',
                'scopes': {
                    'read': 'Can read',
                    'write': 'Can write'
                }
            }
        })

        @api.route('/test/')
        class Test(restplus.Resource):
            def get(self):
                pass

        data = api.as_postman()

        validate(data, schema)
        # request = data['requests'][0]
        # headers = dict(r.split(':') for r in request['headers'].splitlines())
        #
        # assert headers['X-API'] == ''

    def test_export_with_swagger(self, app):
        api = restplus.Api(app)

        data = api.as_postman(swagger=True)

        validate(data, schema)

        assert len(data['requests']) == 1
        request = data['requests'][0]
        assert request['name'] == 'Swagger specifications'
        assert request['description'] == 'The API Swagger specifications as JSON'
        assert request['url'] == 'http://localhost/swagger.json'
