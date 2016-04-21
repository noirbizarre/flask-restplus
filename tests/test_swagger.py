# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from textwrap import dedent

from flask import url_for, Blueprint
from werkzeug.datastructures import FileStorage

import flask_restplus as restplus

from . import TestCase


class ApiMixin(object):
    def build_api(self, **kwargs):
        bpkwargs = {}
        if 'prefix' in kwargs:
            bpkwargs['url_prefix'] = kwargs.pop('prefix')
        if 'subdomain' in kwargs:
            bpkwargs['subdomain'] = kwargs.pop('subdomain')
        blueprint = Blueprint('api', __name__, **bpkwargs)
        api = restplus.Api(blueprint, **kwargs)
        self.app.register_blueprint(blueprint)
        return api


class SwaggerTests(ApiMixin, TestCase):
    def test_specs_endpoint(self):
        api = restplus.Api()
        api.init_app(self.app)

        data = self.get_specs('')
        self.assertEqual(data['swagger'], '2.0')
        self.assertEqual(data['basePath'], '/')
        self.assertEqual(data['produces'], ['application/json'])
        self.assertEqual(data['consumes'], ['application/json'])
        self.assertEqual(data['paths'], {})
        self.assertIn('info', data)

    def test_specs_endpoint_with_prefix(self):
        self.build_api(prefix='/api')

        data = self.get_specs('/api')
        self.assertEqual(data['swagger'], '2.0')
        self.assertEqual(data['basePath'], '/api')
        self.assertEqual(data['produces'], ['application/json'])
        self.assertEqual(data['consumes'], ['application/json'])
        self.assertEqual(data['paths'], {})
        self.assertIn('info', data)

    def test_specs_endpoint_produces(self):
        api = self.build_api()

        def output_xml(data, code, headers=None):
            pass

        api.representations['application/xml'] = output_xml

        data = self.get_specs()
        self.assertEqual(len(data['produces']), 2)
        self.assertIn('application/json', data['produces'])
        self.assertIn('application/xml', data['produces'])

    def test_specs_endpoint_info(self):
        api = restplus.Api(version='1.0',
            title='My API',
            description='This is a testing API',
            terms_url='http://somewhere.com/terms/',
            contact='Support',
            contact_url='http://support.somewhere.com',
            contact_email='contact@somewhere.com',
            license='Apache 2.0',
            license_url='http://www.apache.org/licenses/LICENSE-2.0.html'
        )
        api.init_app(self.app)

        data = self.get_specs()
        self.assertEqual(data['swagger'], '2.0')
        self.assertEqual(data['basePath'], '/')
        self.assertEqual(data['produces'], ['application/json'])
        self.assertEqual(data['paths'], {})

        self.assertIn('info', data)
        self.assertEqual(data['info']['title'], 'My API')
        self.assertEqual(data['info']['version'], '1.0')
        self.assertEqual(data['info']['description'], 'This is a testing API')
        self.assertEqual(data['info']['termsOfService'], 'http://somewhere.com/terms/')
        self.assertEqual(data['info']['contact'], {
            'name': 'Support',
            'url': 'http://support.somewhere.com',
            'email': 'contact@somewhere.com',
        })
        self.assertEqual(data['info']['license'], {
            'name': 'Apache 2.0',
            'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        })

    def test_specs_endpoint_info_delayed(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app,
            title='My API',
            description='This is a testing API',
            terms_url='http://somewhere.com/terms/',
            contact='Support',
            contact_url='http://support.somewhere.com',
            contact_email='contact@somewhere.com',
            license='Apache 2.0',
            license_url='http://www.apache.org/licenses/LICENSE-2.0.html'
        )

        data = self.get_specs()

        self.assertEqual(data['swagger'], '2.0')
        self.assertEqual(data['basePath'], '/')
        self.assertEqual(data['produces'], ['application/json'])
        self.assertEqual(data['paths'], {})

        self.assertIn('info', data)
        self.assertEqual(data['info']['title'], 'My API')
        self.assertEqual(data['info']['version'], '1.0')
        self.assertEqual(data['info']['description'], 'This is a testing API')
        self.assertEqual(data['info']['termsOfService'], 'http://somewhere.com/terms/')
        self.assertEqual(data['info']['contact'], {
            'name': 'Support',
            'url': 'http://support.somewhere.com',
            'email': 'contact@somewhere.com',
        })
        self.assertEqual(data['info']['license'], {
            'name': 'Apache 2.0',
            'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        })

    def test_specs_endpoint_info_callable(self):
        api = restplus.Api(version=lambda: '1.0',
            title=lambda: 'My API',
            description=lambda: 'This is a testing API',
            terms_url=lambda: 'http://somewhere.com/terms/',
            contact=lambda: 'Support',
            contact_url=lambda: 'http://support.somewhere.com',
            contact_email=lambda: 'contact@somewhere.com',
            license=lambda: 'Apache 2.0',
            license_url=lambda: 'http://www.apache.org/licenses/LICENSE-2.0.html'
        )
        api.init_app(self.app)

        data = self.get_specs()
        self.assertEqual(data['swagger'], '2.0')
        self.assertEqual(data['basePath'], '/')
        self.assertEqual(data['produces'], ['application/json'])
        self.assertEqual(data['paths'], {})

        self.assertIn('info', data)
        self.assertEqual(data['info']['title'], 'My API')
        self.assertEqual(data['info']['version'], '1.0')
        self.assertEqual(data['info']['description'], 'This is a testing API')
        self.assertEqual(data['info']['termsOfService'], 'http://somewhere.com/terms/')
        self.assertEqual(data['info']['contact'], {
            'name': 'Support',
            'url': 'http://support.somewhere.com',
            'email': 'contact@somewhere.com',
        })
        self.assertEqual(data['info']['license'], {
            'name': 'Apache 2.0',
            'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        })

    def test_specs_endpoint_no_host(self):
        restplus.Api(self.app)

        data = self.get_specs('')
        self.assertNotIn('host', data)

    def test_specs_endpoint_host(self):
        self.app.config['SERVER_NAME'] = 'api.restplus.org'
        restplus.Api(self.app)

        data = self.get_specs('')
        self.assertEqual(data['host'], 'api.restplus.org')

    def test_specs_endpoint_host_and_subdomain(self):
        self.app.config['SERVER_NAME'] = 'restplus.org'
        blueprint = Blueprint('api', __name__, subdomain='api')
        restplus.Api(blueprint)
        self.app.register_blueprint(blueprint)

        data = self.get_specs(base_url='http://api.restplus.org')
        self.assertEqual(data['host'], 'api.restplus.org')

    def test_specs_endpoint_tags_short(self):
        restplus.Api(self.app, tags=['tag-1', 'tag-2', 'tag-3'])

        data = self.get_specs('')
        self.assertEqual(data['tags'], [
            {'name': 'tag-1'},
            {'name': 'tag-2'},
            {'name': 'tag-3'},
            {'name': 'default', 'description': 'Default namespace'},
        ])

    def test_specs_endpoint_tags_tuple(self):
        restplus.Api(self.app, tags=[
            ('tag-1', 'Tag 1'),
            ('tag-2', 'Tag 2'),
            ('tag-3', 'Tag 3'),
        ])

        data = self.get_specs('')
        self.assertEqual(data['tags'], [
            {'name': 'tag-1', 'description': 'Tag 1'},
            {'name': 'tag-2', 'description': 'Tag 2'},
            {'name': 'tag-3', 'description': 'Tag 3'},
            {'name': 'default', 'description': 'Default namespace'},
        ])

    def test_specs_endpoint_tags_dict(self):
        restplus.Api(self.app, tags=[
            {'name': 'tag-1', 'description': 'Tag 1'},
            {'name': 'tag-2', 'description': 'Tag 2'},
            {'name': 'tag-3', 'description': 'Tag 3'},
        ])

        data = self.get_specs('')
        self.assertEqual(data['tags'], [
            {'name': 'tag-1', 'description': 'Tag 1'},
            {'name': 'tag-2', 'description': 'Tag 2'},
            {'name': 'tag-3', 'description': 'Tag 3'},
            {'name': 'default', 'description': 'Default namespace'},
        ])

    def test_specs_endpoint_tags_namespaces(self):
        api = restplus.Api(self.app, tags=['ns', 'tag'])
        api.namespace('ns', 'Description')

        data = self.get_specs('')
        self.assertEqual(data['tags'], [
            {'name': 'ns', 'description': 'Description'},
            {'name': 'tag'},
            {'name': 'default', 'description': 'Default namespace'},
        ])

    def test_specs_endpoint_invalid_tags(self):
        restplus.Api(self.app, tags=[
            {'description': 'Tag 1'}
        ])

        self.get_specs('', status=500)

    def test_specs_authorizations(self):
        authorizations = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        }
        restplus.Api(self.app, authorizations=authorizations)

        data = self.get_specs()

        self.assertIn('securityDefinitions', data)
        self.assertEqual(data['securityDefinitions'], authorizations)

    def test_minimal_documentation(self):
        api = self.build_api(prefix='/api')
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs('/api')
        paths = data['paths']
        self.assertEqual(len(paths.keys()), 1)

        self.assertIn('/ns/', paths)
        self.assertIn('get', paths['/ns/'])
        op = paths['/ns/']['get']
        self.assertEqual(op['tags'], ['ns'])
        self.assertEqual(op['operationId'], 'get_test_resource')
        self.assertNotIn('parameters', op)
        self.assertNotIn('summary', op)
        self.assertNotIn('description', op)
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            }
        })

        with self.context():
            self.assertEqual(url_for('api.test'), '/api/ns/')

    def test_default_ns_resource_documentation(self):
        api = self.build_api(prefix='/api', version='1.0')

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs('/api')
        paths = data['paths']
        self.assertEqual(len(paths.keys()), 1)

        self.assertIn('/test/', paths)
        self.assertIn('get', paths['/test/'])
        op = paths['/test/']['get']
        self.assertEqual(op['tags'], ['default'])
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            }
        })

        self.assertEqual(len(data['tags']), 1)
        tag = data['tags'][0]
        self.assertEqual(tag['name'], 'default')
        self.assertEqual(tag['description'], 'Default namespace')

        with self.context():
            self.assertEqual(url_for('api.test'), '/api/test/')

    def test_default_ns_resource_documentation_with_override(self):
        api = self.build_api(default='site', default_label='Site namespace')

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs()
        paths = data['paths']
        self.assertEqual(len(paths.keys()), 1)

        self.assertIn('/test/', paths)
        self.assertIn('get', paths['/test/'])
        op = paths['/test/']['get']
        self.assertEqual(op['tags'], ['site'])
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            }
        })

        self.assertEqual(len(data['tags']), 1)
        tag = data['tags'][0]
        self.assertEqual(tag['name'], 'site')
        self.assertEqual(tag['description'], 'Site namespace')

        with self.context():
            self.assertEqual(url_for('api.test'), '/test/')

    def test_ns_resource_documentation(self):
        api = self.build_api(prefix='/api')
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs('/api')
        paths = data['paths']
        self.assertEqual(len(paths.keys()), 1)

        self.assertIn('/ns/', paths)
        self.assertIn('get', paths['/ns/'])
        op = paths['/ns/']['get']
        self.assertEqual(op['tags'], ['ns'])
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            }
        })
        self.assertNotIn('parameters', op)

        self.assertEqual(len(data['tags']), 2)
        tag = data['tags'][-1]
        self.assertEqual(tag['name'], 'ns')
        self.assertEqual(tag['description'], 'Test namespace')

        with self.context():
            self.assertEqual(url_for('api.test'), '/api/ns/')

    def test_ns_resource_documentation_lazy(self):
        api = restplus.Api()
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        api.init_app(self.app)

        data = self.get_specs()
        paths = data['paths']
        self.assertEqual(len(paths.keys()), 1)

        self.assertIn('/ns/', paths)
        self.assertIn('get', paths['/ns/'])
        op = paths['/ns/']['get']
        self.assertEqual(op['tags'], ['ns'])
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            }
        })

        self.assertEqual(len(data['tags']), 2)
        tag = data['tags'][-1]
        self.assertEqual(tag['name'], 'ns')
        self.assertEqual(tag['description'], 'Test namespace')

        with self.context():
            self.assertEqual(url_for('test'), '/ns/')

    def test_methods_docstring_to_summary(self):
        api = self.build_api()

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

            def post(self):
                '''POST operation.

                Should be ignored
                '''
                return {}

            def put(self):
                '''PUT operation. Should be ignored'''
                return {}

            def delete(self):
                '''
                DELETE operation.
                Should be ignored.
                '''
                return {}

        data = self.get_specs()
        path = data['paths']['/test/']

        self.assertEqual(len(path.keys()), 4)

        for method in path.keys():
            operation = path[method]
            self.assertIn(method, ('get', 'post', 'put', 'delete'))
            self.assertEqual(operation['summary'], '{0} operation'.format(method.upper()))
            self.assertEqual(operation['operationId'], '{0}_test_resource'.format(method.lower()))
            # self.assertEqual(operation['parameters'], [])

    def test_path_parameter_no_type(self):
        api = self.build_api()

        @api.route('/id/<id>/', endpoint='by-id')
        class ByIdResource(restplus.Resource):
            def get(self, id):
                return {}

        data = self.get_specs()
        self.assertIn('/id/{id}/', data['paths'])

        path = data['paths']['/id/{id}/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'id')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)

    def test_path_parameter_with_type(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)

    def test_path_parameter_with_explicit_details(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name', doc={
            'params': {
                'age': {'description': 'An age'}
            }
        })
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

    def test_path_parameter_with_decorator_details(self):
        api = self.build_api()

        @api.route('/name/<int:age>/')
        @api.param('age', 'An age')
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

    def test_expect_parser(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            def get(self):
                return {}

        data = self.get_specs()
        self.assertIn('/with-parser/', data['paths'])

        op = data['paths']['/with-parser/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'Some param')

    def test_expect_parser_on_class(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        @api.expect(parser)
        class WithParserResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_specs()
        self.assertIn('/with-parser/', data['paths'])

        path = data['paths']['/with-parser/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'Some param')

    def test_method_parser_on_class(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        @api.doc(get={'expect': parser})
        class WithParserResource(restplus.Resource):
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_specs()
        self.assertIn('/with-parser/', data['paths'])

        op = data['paths']['/with-parser/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'Some param')

        op = data['paths']['/with-parser/']['post']
        self.assertNotIn('parameters', op)

    def test_parser_parameters_override(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            @api.doc(params={'param': {'description': 'New description'}})
            def get(self):
                return {}

        data = self.get_specs()
        self.assertIn('/with-parser/', data['paths'])

        op = data['paths']['/with-parser/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'New description')

    def test_parser_parameter_in_form(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param', location='form')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            def get(self):
                return {}

        data = self.get_specs()
        self.assertIn('/with-parser/', data['paths'])

        op = data['paths']['/with-parser/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'formData')
        self.assertEqual(parameter['description'], 'Some param')

        self.assertEqual(op['consumes'], ['application/x-www-form-urlencoded', 'multipart/form-data'])

    def test_parser_parameter_in_files(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('in_files', type=FileStorage, location='files')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            def get(self):
                return {}

        data = self.get_specs()
        self.assertIn('/with-parser/', data['paths'])

        op = data['paths']['/with-parser/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'in_files')
        self.assertEqual(parameter['type'], 'file')
        self.assertEqual(parameter['in'], 'formData')

        self.assertEqual(op['consumes'], ['multipart/form-data'])

    def test_explicit_parameters(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            @api.doc(params={
                'q': {
                    'type': 'string',
                    'in': 'query',
                    'description': 'A query string',
                }
            })
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)

        op = path['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

    def test_explicit_parameters_with_decorator(self):
        api = self.build_api()

        @api.route('/name/')
        class ByNameResource(restplus.Resource):
            @api.param('q', 'A query string', type='string', _in='formData')
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/', data['paths'])

        op = data['paths']['/name/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'formData')
        self.assertEqual(parameter['description'], 'A query string')

    def test_class_explicit_parameters(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name', doc={
            'params': {
                'q': {
                    'type': 'string',
                    'in': 'query',
                    'description': 'A query string',
                }
            }
        })
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 2)

        by_name = dict((p['name'], p) for p in path['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

    def test_explicit_parameters_override(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name', doc={
            'params': {
                'q': {
                    'type': 'string',
                    'in': 'query',
                    'description': 'Overriden description',
                },
                'age': {
                    'description': 'An age'
                }
            }
        })
        class ByNameResource(restplus.Resource):
            @api.doc(params={'q': {'description': 'A query string'}})
            def get(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 2)

        by_name = dict((p['name'], p) for p in path['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'Overriden description')

        op = data['paths']['/name/{age}/']['get']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

    def test_explicit_parameters_override_by_method(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name', doc={
            'get': {
                'params': {
                    'q': {
                        'type': 'string',
                        'in': 'query',
                        'description': 'A query string',
                    }
                }
            },
            'params': {
                'age': {
                    'description': 'An age'
                }
            }
        })
        class ByNameResource(restplus.Resource):
            @api.doc(params={'age': {'description': 'Overriden'}})
            def get(self, age):
                return {}

            def post(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 1)

        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

        op = path['get']
        self.assertEqual(len(op['parameters']), 2)

        by_name = dict((p['name'], p) for p in op['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'Overriden')

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

        self.assertNotIn('parameters', path['post'])

    def test_explicit_parameters_desription_shortcut(self):
        api = self.build_api()

        @api.route('/name/<int:age>/', endpoint='by-name', doc={
            'get': {
                'params': {
                    'q': 'A query string',
                }
            },
            'params': {
                'age': 'An age'
            }
        })
        class ByNameResource(restplus.Resource):
            @api.doc(params={'age': 'Overriden'})
            def get(self, age):
                return {}

            def post(self, age):
                return {}

        data = self.get_specs()
        self.assertIn('/name/{age}/', data['paths'])

        path = data['paths']['/name/{age}/']
        self.assertEqual(len(path['parameters']), 1)
        parameter = path['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

        op = path['get']
        self.assertEqual(len(op['parameters']), 2)

        by_name = dict((p['name'], p) for p in op['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'Overriden')

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

        self.assertNotIn('parameters', path['post'])

    def test_explicit_parameters_native_types(self):
        api = self.build_api()

        @api.route('/types/', endpoint='native')
        class NativeTypesResource(restplus.Resource):
            @api.doc(params={
                'int': {
                    'type': int,
                    'in': 'query',
                },
                'bool': {
                    'type': bool,
                    'in': 'query',
                },
                'str': {
                    'type': str,
                    'in': 'query',
                },
                'int-array': {
                    'type': [int],
                    'in': 'query',
                },
                'bool-array': {
                    'type': [bool],
                    'in': 'query',
                },
                'str-array': {
                    'type': [str],
                    'in': 'query',
                }
            })
            def get(self, age):
                return {}

        data = self.get_specs()

        op = data['paths']['/types/']['get']

        parameters = dict((p['name'], p) for p in op['parameters'])

        self.assertEqual(parameters['int']['type'], 'integer')
        self.assertEqual(parameters['str']['type'], 'string')
        self.assertEqual(parameters['bool']['type'], 'boolean')

        self.assertEqual(parameters['int-array']['type'], 'array')
        self.assertEqual(parameters['int-array']['items']['type'], 'integer')
        self.assertEqual(parameters['str-array']['type'], 'array')
        self.assertEqual(parameters['str-array']['items']['type'], 'string')
        self.assertEqual(parameters['bool-array']['type'], 'array')
        self.assertEqual(parameters['bool-array']['items']['type'], 'boolean')

    def test_response_on_method(self):
        api = self.build_api()

        api.model('ErrorModel', {
            'message': restplus.fields.String,
        })

        @api.route('/test/')
        class ByNameResource(restplus.Resource):
            @api.doc(responses={
                404: 'Not found',
                405: ('Some message', 'ErrorModel'),
            })
            def get(self):
                return {}

        data = self.get_specs('')
        paths = data['paths']
        self.assertEqual(len(paths.keys()), 1)

        op = paths['/test/']['get']
        self.assertEqual(op['tags'], ['default'])
        self.assertEqual(op['responses'], {
            '404': {
                'description': 'Not found',
            },
            '405': {
                'description': 'Some message',
                'schema': {
                    '$ref': '#/definitions/ErrorModel',
                }
            }
        })

        self.assertIn('definitions', data)
        self.assertIn('ErrorModel', data['definitions'])

    def test_api_response(self):
        api = self.build_api()

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response(200, 'Success')
            def get(self):
                pass

        data = self.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            }
        })

    def test_api_response_multiple(self):
        api = self.build_api()

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response(200, 'Success')
            @api.response(400, 'Validation error')
            def get(self):
                pass

        data = self.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
            },
            '400': {
                'description': 'Validation error',
            }
        })

    def test_api_response_with_model(self):
        api = self.build_api()

        model = api.model('SomeModel', {
            'message': restplus.fields.String,
        })

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response(200, 'Success', model)
            def get(self):
                pass

        data = self.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        self.assertEqual(op['responses'], {
            '200': {
                'description': 'Success',
                'schema': {
                    '$ref': '#/definitions/SomeModel',
                }
            }
        })

        self.assertIn('SomeModel', data['definitions'])

    def test_api_response_default(self):
        api = self.build_api()

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response('default', 'Error')
            def get(self):
                pass

        data = self.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        self.assertEqual(op['responses'], {
            'default': {
                'description': 'Error',
            }
        })

    def test_api_header(self):
        api = self.build_api()

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.header('X-HEADER', 'A required header', required=True)
            def get(self):
                pass

            @api.header('X-HEADER-2', 'Another header', type=[int], collectionFormat='csv')
            def post(self):
                pass

            @api.header('X-HEADER-3', type=int)
            def put(self):
                pass

            @api.header('X-HEADER-4', type='boolean')
            def delete(self):
                pass

        data = self.get_specs('')
        paths = data['paths']

        def param_for(method):
            return paths['/test/'][method]['parameters'][0]

        parameter = param_for('get')
        self.assertEqual(parameter['name'], 'X-HEADER')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['in'], 'header')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'A required header')

        parameter = param_for('post')
        self.assertEqual(parameter['name'], 'X-HEADER-2')
        self.assertEqual(parameter['type'], 'array')
        self.assertEqual(parameter['in'], 'header')
        self.assertEqual(parameter['items']['type'], 'integer')
        self.assertEqual(parameter['description'], 'Another header')
        self.assertEqual(parameter['collectionFormat'], 'csv')

        parameter = param_for('put')
        self.assertEqual(parameter['name'], 'X-HEADER-3')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'header')

        parameter = param_for('delete')
        self.assertEqual(parameter['name'], 'X-HEADER-4')
        self.assertEqual(parameter['type'], 'boolean')
        self.assertEqual(parameter['in'], 'header')

    def test_description(self):
        api = self.build_api()

        @api.route('/description/', endpoint='description', doc={
            'description': 'Parent description.',
            'delete': {'description': 'A delete operation'},
        })
        class ResourceWithDescription(restplus.Resource):
            @api.doc(description='Some details')
            def get(self):
                return {}

            def post(self):
                '''
                Do something.

                Extra description
                '''
                return {}

            def put(self):
                '''No description (only summary)'''

            def delete(self):
                '''No description (only summary)'''

        @api.route('/descriptionless/', endpoint='descriptionless')
        class ResourceWithoutDescription(restplus.Resource):
            def get(self):
                '''No description (only summary)'''
                return {}

        data = self.get_specs()

        description = lambda m: data['paths']['/description/'][m]['description']

        self.assertEqual(description('get'), dedent('''\
            Parent description.
            Some details'''
        ))

        self.assertEqual(description('post'), dedent('''\
            Parent description.
            Extra description'''
        ))

        self.assertEqual(description('delete'), dedent('''\
            Parent description.
            A delete operation'''
        ))

        self.assertEqual(description('put'), 'Parent description.')
        self.assertNotIn('description', data['paths']['/descriptionless/']['get'])

    def test_operation_id(self):
        api = self.build_api()

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc(id='get_objects')
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_specs()
        path = data['paths']['/test/']

        self.assertEqual(path['get']['operationId'], 'get_objects')
        self.assertEqual(path['post']['operationId'], 'post_test_resource')

    def test_operation_id_shortcut(self):
        api = self.build_api()

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc('get_objects')
            def get(self):
                return {}

        data = self.get_specs()
        path = data['paths']['/test/']

        self.assertEqual(path['get']['operationId'], 'get_objects')

    def test_custom_default_operation_id(self):
        def default_id(resource, method):
            return '{0}{1}'.format(method, resource)

        api = self.build_api(default_id=default_id)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc(id='get_objects')
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_specs()
        path = data['paths']['/test/']

        self.assertEqual(path['get']['operationId'], 'get_objects')
        self.assertEqual(path['post']['operationId'], 'postTestResource')

    def test_model_primitive_types(self):
        api = self.build_api()

        @api.route('/model-int/')
        class ModelInt(restplus.Resource):
            @api.doc(model=int)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertNotIn('definitions', data)
        self.assertEqual(data['paths']['/model-int/']['get']['responses'], {
            '200': {
                'description': 'Success',
                'schema': {
                    'type': 'integer'
                }
            }
        })

    def test_model_as_flat_dict(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=fields)
            def get(self):
                return {}

            @api.doc(model='Person')
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        path = data['paths']['/model-as-dict/']
        self.assertEqual(path['get']['responses']['200']['schema']['$ref'], '#/definitions/Person')
        self.assertEqual(path['post']['responses']['200']['schema']['$ref'], '#/definitions/Person')

    def test_model_as_nested_dict(self):
        api = self.build_api()

        address_fields = api.model('Address', {
            'road': restplus.fields.String,
        })

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
            'address': restplus.fields.Nested(address_fields)
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=fields)
            def get(self):
                return {}

            @api.doc(model='Person')
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        self.assertIn('Address', data['definitions'].keys())
        self.assertEqual(data['definitions']['Address'], {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        })

        path = data['paths']['/model-as-dict/']
        self.assertEqual(path['get']['responses']['200']['schema']['$ref'], '#/definitions/Person')
        self.assertEqual(path['post']['responses']['200']['schema']['$ref'], '#/definitions/Person')

    def test_model_as_flat_dict_with_marchal_decorator(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        responses = data['paths']['/model-as-dict/']['get']['responses']
        self.assertEqual(responses, {
            '200': {
                'description': 'Success',
                'schema': {
                    '$ref': '#/definitions/Person'
                }
            }
        })

    def test_marchal_decorator_with_code(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields, code=204)
            def delete(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        responses = data['paths']['/model-as-dict/']['delete']['responses']
        self.assertEqual(responses, {
            '204': {
                'description': 'Success',
                'schema': {
                    '$ref': '#/definitions/Person'
                }
            }
        })

    def test_marchal_decorator_with_description(self):
        api = self.build_api()

        person = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(person, description='Some details')
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        responses = data['paths']['/model-as-dict/']['get']['responses']
        self.assertEqual(responses, {
            '200': {
                'description': 'Some details',
                'schema': {
                    '$ref': '#/definitions/Person'
                }
            }
        })

    def test_model_as_flat_dict_with_marchal_decorator_list(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields, as_list=True)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        path = data['paths']['/model-as-dict/']
        self.assertEqual(path['get']['responses']['200']['schema'], {
            'type': 'array',
            'items': {'$ref': '#/definitions/Person'},
        })

    def test_model_as_flat_dict_with_marchal_decorator_list_alt(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_list_with(fields)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        path = data['paths']['/model-as-dict/']
        self.assertEqual(path['get']['responses']['200']['schema'], {
            'type': 'array',
            'items': {'$ref': '#/definitions/Person'},
        })

    def test_model_as_flat_dict_with_marchal_decorator_list_kwargs(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_list_with(fields, code=201, description='Some details')
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        path = data['paths']['/model-as-dict/']
        self.assertEqual(path['get']['responses'], {
            '201': {
                'description': 'Some details',
                'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/definitions/Person'},
                }
            }
        })

    def test_model_as_dict_with_list(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'tags': restplus.fields.List(restplus.fields.String),
        })

        @api.route('/model-with-list/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=fields)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'tags': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'type': 'object'
        })

        path = data['paths']['/model-with-list/']
        self.assertEqual(path['get']['responses']['200']['schema'], {'$ref': '#/definitions/Person'})

    def test_model_as_nested_dict_with_list(self):
        api = self.build_api()

        address = api.model('Address', {
            'road': restplus.fields.String,
        })

        person = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
            'addresses': restplus.fields.List(restplus.fields.Nested(address))
        })

        @api.route('/model-with-list/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=person)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertIn('Address', data['definitions'])

    def test_model_list_of_primitive_types(self):
        api = self.build_api()

        @api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=[int])
            def get(self):
                return {}

            @api.doc(model=[str])
            def post(self):
                return {}

        data = self.get_specs()

        self.assertNotIn('definitions', data)

        path = data['paths']['/model-list/']
        self.assertEqual(path['get']['responses']['200']['schema'], {
            'type': 'array',
            'items': {'type': 'integer'},
        })
        self.assertEqual(path['post']['responses']['200']['schema'], {
            'type': 'array',
            'items': {'type': 'string'},
        })

    def test_model_list_as_flat_dict(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=[fields])
            def get(self):
                return {}

            @api.doc(model=['Person'])
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        path = data['paths']['/model-as-dict/']
        for method in 'get', 'post':
            self.assertEqual(path[method]['responses']['200']['schema'], {
                'type': 'array',
                'items': {'$ref': '#/definitions/Person'},
            })

    def test_model_doc_on_class(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        @api.doc(model=fields)
        class ModelAsDict(restplus.Resource):
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_specs()
        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        path = data['paths']['/model-as-dict/']
        for method in 'get', 'post':
            self.assertEqual(path[method]['responses']['200']['schema'], {'$ref': '#/definitions/Person'})

    def test_model_doc_for_method_on_class(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        @api.doc(get={'model': fields})
        class ModelAsDict(restplus.Resource):
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_specs()
        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])

        path = data['paths']['/model-as-dict/']
        self.assertEqual(path['get']['responses']['200']['schema'], {'$ref': '#/definitions/Person'})
        self.assertNotIn('schema', path['post']['responses']['200'])

    def test_model_with_discriminator(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String(discriminator=True),
            'age': restplus.fields.Integer,
        })

        @api.route('/model-with-discriminator/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name'],
            'type': 'object'
        })

    def test_model_with_discriminator_override_require(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String(discriminator=True, required=False),
            'age': restplus.fields.Integer,
        })

        @api.route('/model-with-discriminator/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name'],
            'type': 'object'
        })

    def test_model_not_found(self):
        api = self.build_api()

        @api.route('/model-not-found/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model='NotFound')
            def get(self):
                return {}

        self.get_specs(status=500)

    def test_clone(self):
        api = self.build_api()

        parent = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        child = api.clone('Child', parent, {
            'extra': restplus.fields.String,
        })

        @api.route('/extend/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=child)
            def get(self):
                return {}

            @api.doc(model='Child')
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertNotIn('Person', data['definitions'])
        self.assertIn('Child', data['definitions'])

        path = data['paths']['/extend/']
        self.assertEqual(path['get']['responses']['200']['schema']['$ref'], '#/definitions/Child')
        self.assertEqual(path['post']['responses']['200']['schema']['$ref'], '#/definitions/Child')

    def test_inherit(self):
        api = self.build_api()

        parent = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
        })

        child = api.inherit('Child', parent, {
            'extra': restplus.fields.String,
        })

        @api.route('/inherit/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(child)
            def get(self):
                return {
                    'name': 'John',
                    'age': 42,
                    'extra': 'test',
                }

            @api.doc(model='Child')
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertIn('Child', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'type': 'object'
        })
        self.assertEqual(data['definitions']['Child'], {
            'allOf': [{
                '$ref': '#/definitions/Person'
            }, {
                'properties': {
                    'extra': {'type': 'string'}
                },
                'type': 'object'
            }]
        })

        path = data['paths']['/inherit/']
        self.assertEqual(path['get']['responses']['200']['schema']['$ref'], '#/definitions/Child')
        self.assertEqual(path['post']['responses']['200']['schema']['$ref'], '#/definitions/Child')

        data = self.get_json('/inherit/')
        self.assertEqual(data, {
            'name': 'John',
            'age': 42,
            'extra': 'test',
        })

    def test_inherit_inline(self):
        api = self.build_api()

        parent = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
        })

        child = api.inherit('Child', parent, {
            'extra': restplus.fields.String,
        })

        output = api.model('Output', {
            'child': restplus.fields.Nested(child),
            'children': restplus.fields.List(restplus.fields.Nested(child))
        })

        @api.route('/inherit/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(output)
            def get(self):
                return {
                    'child': {
                        'name': 'John',
                        'age': 42,
                        'extra': 'test',
                    },
                    'children': [{
                        'name': 'John',
                        'age': 42,
                        'extra': 'test',
                    }, {
                        'name': 'Doe',
                        'age': 33,
                        'extra': 'test2',
                    }]
                }

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertIn('Child', data['definitions'])

        data = self.get_json('/inherit/')
        self.assertEqual(data, {
            'child': {
                'name': 'John',
                'age': 42,
                'extra': 'test',
            },
            'children': [{
                'name': 'John',
                'age': 42,
                'extra': 'test',
            }, {
                'name': 'Doe',
                'age': 33,
                'extra': 'test2',
            }]
        })

    def test_polymorph_inherit(self):
        api = self.build_api()

        class Child1:
            pass

        class Child2:
            pass

        parent = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': restplus.fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': restplus.fields.String,
        })

        mapping = {
            Child1: child1,
            Child2: child2,
        }

        output = api.model('Output', {
            'child': restplus.fields.Polymorph(mapping)
        })

        @api.route('/polymorph/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(output)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertIn('Child1', data['definitions'])
        self.assertIn('Child2', data['definitions'])
        self.assertIn('Output', data['definitions'])

        path = data['paths']['/polymorph/']
        self.assertEqual(path['get']['responses']['200']['schema']['$ref'], '#/definitions/Output')

    def test_polymorph_inherit_list(self):
        api = self.build_api()

        class Child1:
            name = 'Child1'
            extra1 = 'extra1'

        class Child2:
            name = 'Child2'
            extra2 = 'extra2'

        parent = api.model('Person', {
            'name': restplus.fields.String,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': restplus.fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': restplus.fields.String,
        })

        mapping = {
            Child1: child1,
            Child2: child2,
        }

        output = api.model('Output', {
            'children': restplus.fields.List(restplus.fields.Polymorph(mapping))
        })

        @api.route('/polymorph/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(output)
            def get(self):
                return {
                    'children': [Child1(), Child2()]
                }

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertIn('Child1', data['definitions'])
        self.assertIn('Child2', data['definitions'])
        self.assertIn('Output', data['definitions'])

        path = data['paths']['/polymorph/']
        self.assertEqual(path['get']['responses']['200']['schema']['$ref'], '#/definitions/Output')

        data = self.get_json('/polymorph/')
        self.assertEqual(data, {
            'children': [{
                'name': 'Child1',
                'extra1': 'extra1',
            }, {
                'name': 'Child2',
                'extra2': 'extra2',
            }]
        })

    def test_expect_model(self):
        api = self.build_api()

        person = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.expect(person)
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        op = data['paths']['/model-as-dict/']['post']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Person'
            }
        })
        self.assertNotIn('description', parameter)

    def test_body_model_shortcut(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model='Person')
            @api.expect(fields)
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        op = data['paths']['/model-as-dict/']['post']
        self.assertEqual(op['responses']['200']['schema']['$ref'], '#/definitions/Person')

        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]
        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Person'
            }
        })
        self.assertNotIn('description', parameter)

    def test_expect_model_list(self):
        api = self.build_api()

        model = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @api.expect([model])
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        op = data['paths']['/model-list/']['post']
        parameter = op['parameters'][0]

        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Person'},
            }
        })

    def test_both_model_and_parser_from_expect(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        person = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser, person)
            def get(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        self.assertIn('/with-parser/', data['paths'])

        op = data['paths']['/with-parser/']['get']
        self.assertEqual(len(op['parameters']), 2)

        parameters = dict((p['in'], p) for p in op['parameters'])

        parameter = parameters['query']
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['in'], 'query')
        self.assertEqual(parameter['description'], 'Some param')

        parameter = parameters['body']
        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Person'
            }
        })

    def test_expect_primitive_list(self):
        api = self.build_api()

        @api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @api.expect([restplus.fields.String])
            def post(self):
                return {}

        data = self.get_specs()

        op = data['paths']['/model-list/']['post']
        parameter = op['parameters'][0]
        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {'type': 'string'},
            }
        })

    def test_body_model_list(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @api.expect([fields])
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        op = data['paths']['/model-list/']['post']
        parameter = op['parameters'][0]

        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Person'},
            }
        })

    def test_expect_model_with_description(self):
        api = self.build_api()

        person = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @api.expect((person, 'Body description'))
            def post(self):
                return {}

        data = self.get_specs()

        self.assertIn('definitions', data)
        self.assertIn('Person', data['definitions'])
        self.assertEqual(data['definitions']['Person'], {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'type': 'object'
        })

        op = data['paths']['/model-as-dict/']['post']
        self.assertEqual(len(op['parameters']), 1)

        parameter = op['parameters'][0]

        self.assertEqual(parameter, {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'description': 'Body description',
            'schema': {
                '$ref': '#/definitions/Person'
            }
        })

    def test_authorizations(self):
        restplus.Api(self.app, authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })

        # @api.route('/authorizations/')
        # class ModelAsDict(restplus.Resource):
        #     def get(self):
        #         return {}

        #     def post(self):
        #         return {}

        data = self.get_specs()
        self.assertIn('securityDefinitions', data)
        self.assertNotIn('security', data)

        # path = data['paths']['/authorizations/']
        # self.assertNotIn('security', path['get'])
        # self.assertEqual(path['post']['security'], {'apikey': []})

    def test_single_root_security_string(self):
        api = restplus.Api(self.app, security='apikey', authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            def post(self):
                return {}

        data = self.get_specs()
        self.assertEqual(data['securityDefinitions'], {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })
        self.assertEqual(data['security'], [{'apikey': []}])

        op = data['paths']['/authorizations/']['post']
        self.assertNotIn('security', op)

    def test_single_root_security_object(self):
        security_definitions = {
            'oauth2': {
                'type': 'oauth2',
                'flow': 'accessCode',
                'tokenUrl': 'https://somewhere.com/token',
                'scopes': {
                    'read': 'Grant read-only access',
                    'write': 'Grant read-write access',
                }
            },
            'implicit': {
                'type': 'oauth2',
                'flow': 'implicit',
                'tokenUrl': 'https://somewhere.com/token',
                'scopes': {
                    'read': 'Grant read-only access',
                    'write': 'Grant read-write access',
                }
            }
        }

        api = restplus.Api(self.app,
            security={
                'oauth2': 'read',
                'implicit': ['read', 'write']
            },
            authorizations=security_definitions
        )

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            def post(self):
                return {}

        data = self.get_specs()
        self.assertEqual(data['securityDefinitions'], security_definitions)
        self.assertEqual(data['security'], [{
            'oauth2': ['read'],
            'implicit': ['read', 'write']
        }])

        op = data['paths']['/authorizations/']['post']
        self.assertNotIn('security', op)

    def test_root_security_as_list(self):
        security_definitions = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            },
            'oauth2': {
                'type': 'oauth2',
                'flow': 'accessCode',
                'tokenUrl': 'https://somewhere.com/token',
                'scopes': {
                    'read': 'Grant read-only access',
                    'write': 'Grant read-write access',
                }
            }
        }
        api = restplus.Api(self.app, security=['apikey', {'oauth2': 'read'}], authorizations=security_definitions)

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            def post(self):
                return {}

        data = self.get_specs()
        self.assertEqual(data['securityDefinitions'], security_definitions)
        self.assertEqual(data['security'], [{'apikey': []}, {'oauth2': ['read']}])

        op = data['paths']['/authorizations/']['post']
        self.assertNotIn('security', op)

    def test_method_security(self):
        api = restplus.Api(self.app, authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            @api.doc(security=['apikey'])
            def get(self):
                return {}

            @api.doc(security='apikey')
            def post(self):
                return {}

        data = self.get_specs()
        self.assertEqual(data['securityDefinitions'], {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        })
        self.assertNotIn('security', data)

        path = data['paths']['/authorizations/']
        for method in 'get', 'post':
            self.assertEqual(path[method]['security'], [{'apikey': []}])

    def test_security_override(self):
        security_definitions = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            },
            'oauth2': {
                'type': 'oauth2',
                'flow': 'accessCode',
                'tokenUrl': 'https://somewhere.com/token',
                'scopes': {
                    'read': 'Grant read-only access',
                    'write': 'Grant read-write access',
                }
            }
        }
        api = restplus.Api(self.app, security=['apikey', {'oauth2': 'read'}], authorizations=security_definitions)

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            @api.doc(security=[{'oauth2': ['read', 'write']}])
            def get(self):
                return {}

        data = self.get_specs()
        self.assertEqual(data['securityDefinitions'], security_definitions)

        op = data['paths']['/authorizations/']['get']
        self.assertEqual(op['security'], [{'oauth2': ['read', 'write']}])

    def test_security_nullify(self):
        security_definitions = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            },
            'oauth2': {
                'type': 'oauth2',
                'flow': 'accessCode',
                'tokenUrl': 'https://somewhere.com/token',
                'scopes': {
                    'read': 'Grant read-only access',
                    'write': 'Grant read-write access',
                }
            }
        }
        api = restplus.Api(self.app, security=['apikey', {'oauth2': 'read'}], authorizations=security_definitions)

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            @api.doc(security=[])
            def get(self):
                return {}

            @api.doc(security=None)
            def post(self):
                return {}

        data = self.get_specs()
        self.assertEqual(data['securityDefinitions'], security_definitions)

        path = data['paths']['/authorizations/']
        for method in 'get', 'post':
            self.assertEqual(path[method]['security'], [])

    def test_hidden_resource(self):
        api = self.build_api()

        @api.route('/test/', endpoint='test', doc=False)
        class TestResource(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

        @api.hide
        @api.route('/test2/', endpoint='test2')
        class TestResource2(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

        @api.doc(False)
        @api.route('/test3/', endpoint='test3')
        class TestResource3(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

        data = self.get_specs()
        for path in '/test/', '/test2/', '/test3/':
            self.assertNotIn(path, data['paths'])

            with self.app.test_client() as client:
                resp = client.get(path)
                self.assertEqual(resp.status_code, 200)

    def test_hidden_resource_from_namespace(self):
        api = self.build_api()
        ns = api.namespace('ns')

        @ns.route('/test/', endpoint='test', doc=False)
        class TestResource(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

        data = self.get_specs()
        self.assertNotIn('/ns/test/', data['paths'])

        with self.app.test_client() as client:
            resp = client.get('/ns/test/')
            self.assertEqual(resp.status_code, 200)

    def test_hidden_methods(self):
        api = self.build_api()

        @api.route('/test/', endpoint='test')
        @api.doc(delete=False)
        class TestResource(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

            @api.doc(False)
            def post(self):
                '''POST operation.

                Should be ignored
                '''
                return {}

            @api.hide
            def put(self):
                '''PUT operation. Should be ignored'''
                return {}

            def delete(self):
                return {}

        data = self.get_specs()
        path = data['paths']['/test/']

        self.assertIn('get', path)
        self.assertNotIn('post', path)
        self.assertNotIn('put', path)

        for method in 'GET', 'POST', 'PUT':
            with self.app.test_client() as client:
                resp = client.open('/test/', method=method)
                self.assertEqual(resp.status_code, 200)

    def test_deprecated_resource(self):
        api = self.build_api()

        @api.deprecated
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                pass

            def post(self):
                pass

        data = self.get_specs()
        resource = data['paths']['/test/']
        for operation in resource.values():
            self.assertIn('deprecated', operation)
            self.assertTrue(operation['deprecated'])

    def test_deprecated_method(self):
        api = self.build_api()

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                pass

            @api.deprecated
            def post(self):
                pass

        data = self.get_specs()

        get_operation = data['paths']['/test/']['get']
        self.assertNotIn('deprecated', get_operation)

        post_operation = data['paths']['/test/']['post']
        self.assertIn('deprecated', post_operation)
        self.assertTrue(post_operation['deprecated'])

    def test_method_restrictions(self):
        api = self.build_api()

        @api.route('/foo/bar', endpoint='foo')
        @api.route('/bar', methods=['GET'], endpoint='bar')
        class TestResource(restplus.Resource):
            def get(self):
                pass

            def post(self):
                pass

        data = self.get_specs()

        path = data['paths']['/foo/bar']
        self.assertIn('get', path)
        self.assertIn('post', path)

        path = data['paths']['/bar']
        self.assertIn('get', path)
        self.assertNotIn('post', path)


class SwaggerDeprecatedTest(ApiMixin, TestCase):
    def test_doc_parser_parameters(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        with self.assert_warning(DeprecationWarning):
            @api.route('/with-parser/')
            class WithParserResource(restplus.Resource):
                @api.doc(parser=parser)
                def get(self):
                    return {}

        self.assertNotIn('parser', WithParserResource.get.__apidoc__)
        self.assertIn('expect', WithParserResource.get.__apidoc__)
        doc_parser = WithParserResource.get.__apidoc__['expect'][0]
        self.assertEqual(doc_parser.__schema__, parser.__schema__)

    def test_doc_method_parser_on_class(self):
        api = self.build_api()
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        with self.assert_warning(DeprecationWarning):
            @api.route('/with-parser/')
            @api.doc(get={'parser': parser})
            class WithParserResource(restplus.Resource):
                def get(self):
                    return {}

                def post(self):
                    return {}

        self.assertNotIn('parser', WithParserResource.__apidoc__['get'])
        self.assertIn('expect', WithParserResource.__apidoc__['get'])
        doc_parser = WithParserResource.__apidoc__['get']['expect'][0]
        self.assertEqual(doc_parser.__schema__, parser.__schema__)

    def test_doc_body_as_tuple(self):
        api = self.build_api()

        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        with self.assert_warning(DeprecationWarning):
            @api.route('/model-as-dict/')
            class ModelAsDict(restplus.Resource):
                @api.doc(body=(fields, 'Body description'))
                def post(self):
                    return {}

        self.assertNotIn('body', ModelAsDict.post.__apidoc__)
        self.assertEqual(ModelAsDict.post.__apidoc__['expect'], [(fields, 'Body description')])
