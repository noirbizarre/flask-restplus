# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from textwrap import dedent

from flask import url_for, Blueprint
from werkzeug.datastructures import FileStorage

import flask_restplus as restplus

from flask_restplus import inputs


class SwaggerTest(object):
    def test_specs_endpoint(self, api, client):
        data = client.get_specs('')
        assert data['swagger'] == '2.0'
        assert data['basePath'] == '/'
        assert data['produces'] == ['application/json']
        assert data['consumes'] == ['application/json']
        assert data['paths'] == {}
        assert 'info' in data

    @pytest.mark.api(prefix='/api')
    def test_specs_endpoint_with_prefix(self, api, client):
        data = client.get_specs('/api')
        assert data['swagger'] == '2.0'
        assert data['basePath'] == '/api'
        assert data['produces'] == ['application/json']
        assert data['consumes'] == ['application/json']
        assert data['paths'] == {}
        assert 'info' in data

    def test_specs_endpoint_produces(self, api, client):
        def output_xml(data, code, headers=None):
            pass

        api.representations['application/xml'] = output_xml

        data = client.get_specs()
        assert len(data['produces']) == 2
        assert 'application/json' in data['produces']
        assert 'application/xml' in data['produces']

    def test_specs_endpoint_info(self, app, client):
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
        api.init_app(app)

        data = client.get_specs()
        assert data['swagger'] == '2.0'
        assert data['basePath'] == '/'
        assert data['produces'] == ['application/json']
        assert data['paths'] == {}

        assert 'info' in data
        assert data['info']['title'] == 'My API'
        assert data['info']['version'] == '1.0'
        assert data['info']['description'] == 'This is a testing API'
        assert data['info']['termsOfService'] == 'http://somewhere.com/terms/'
        assert data['info']['contact'] == {
            'name': 'Support',
            'url': 'http://support.somewhere.com',
            'email': 'contact@somewhere.com',
        }
        assert data['info']['license'] == {
            'name': 'Apache 2.0',
            'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        }

    def test_specs_endpoint_info_delayed(self, app, client):
        api = restplus.Api(version='1.0')
        api.init_app(app,
            title='My API',
            description='This is a testing API',
            terms_url='http://somewhere.com/terms/',
            contact='Support',
            contact_url='http://support.somewhere.com',
            contact_email='contact@somewhere.com',
            license='Apache 2.0',
            license_url='http://www.apache.org/licenses/LICENSE-2.0.html'
        )

        data = client.get_specs()

        assert data['swagger'] == '2.0'
        assert data['basePath'] == '/'
        assert data['produces'] == ['application/json']
        assert data['paths'] == {}

        assert 'info' in data
        assert data['info']['title'] == 'My API'
        assert data['info']['version'] == '1.0'
        assert data['info']['description'] == 'This is a testing API'
        assert data['info']['termsOfService'] == 'http://somewhere.com/terms/'
        assert data['info']['contact'] == {
            'name': 'Support',
            'url': 'http://support.somewhere.com',
            'email': 'contact@somewhere.com',
        }
        assert data['info']['license'] == {
            'name': 'Apache 2.0',
            'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        }

    def test_specs_endpoint_info_callable(self, app, client):
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
        api.init_app(app)

        data = client.get_specs()
        assert data['swagger'] == '2.0'
        assert data['basePath'] == '/'
        assert data['produces'] == ['application/json']
        assert data['paths'] == {}

        assert 'info' in data
        assert data['info']['title'] == 'My API'
        assert data['info']['version'] == '1.0'
        assert data['info']['description'] == 'This is a testing API'
        assert data['info']['termsOfService'] == 'http://somewhere.com/terms/'
        assert data['info']['contact'] == {
            'name': 'Support',
            'url': 'http://support.somewhere.com',
            'email': 'contact@somewhere.com',
        }
        assert data['info']['license'] == {
            'name': 'Apache 2.0',
            'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        }

    def test_specs_endpoint_no_host(self, app, client):
        restplus.Api(app)

        data = client.get_specs('')
        assert 'host' not in data

    def test_specs_endpoint_host(self, app, client):
        app.config['SERVER_NAME'] = 'api.restplus.org'
        restplus.Api(app)

        data = client.get_specs('')
        assert data['host'] == 'api.restplus.org'

    @pytest.mark.options(server_name='restplus.org')
    def test_specs_endpoint_host_and_subdomain(self, app, client):
        blueprint = Blueprint('api', __name__, subdomain='api')
        restplus.Api(blueprint)
        app.register_blueprint(blueprint)

        data = client.get_specs(base_url='http://api.restplus.org')
        assert data['host'] == 'api.restplus.org'

    def test_specs_endpoint_tags_short(self, app, client):
        restplus.Api(app, tags=['tag-1', 'tag-2', 'tag-3'])

        data = client.get_specs('')
        assert data['tags'] == [
            {'name': 'tag-1'},
            {'name': 'tag-2'},
            {'name': 'tag-3'},
            {'name': 'default', 'description': 'Default namespace'},
        ]

    def test_specs_endpoint_tags_tuple(self, app, client):
        restplus.Api(app, tags=[
            ('tag-1', 'Tag 1'),
            ('tag-2', 'Tag 2'),
            ('tag-3', 'Tag 3'),
        ])

        data = client.get_specs('')
        assert data['tags'] == [
            {'name': 'tag-1', 'description': 'Tag 1'},
            {'name': 'tag-2', 'description': 'Tag 2'},
            {'name': 'tag-3', 'description': 'Tag 3'},
            {'name': 'default', 'description': 'Default namespace'},
        ]

    def test_specs_endpoint_tags_dict(self, app, client):
        restplus.Api(app, tags=[
            {'name': 'tag-1', 'description': 'Tag 1'},
            {'name': 'tag-2', 'description': 'Tag 2'},
            {'name': 'tag-3', 'description': 'Tag 3'},
        ])

        data = client.get_specs('')
        assert data['tags'] == [
            {'name': 'tag-1', 'description': 'Tag 1'},
            {'name': 'tag-2', 'description': 'Tag 2'},
            {'name': 'tag-3', 'description': 'Tag 3'},
            {'name': 'default', 'description': 'Default namespace'},
        ]

    @pytest.mark.api(tags=['ns', 'tag'])
    def test_specs_endpoint_tags_namespaces(self, api, client):
        api.namespace('ns', 'Description')

        data = client.get_specs('')
        assert data['tags'] == [
            {'name': 'ns', 'description': 'Description'},
            {'name': 'tag'},
            {'name': 'default', 'description': 'Default namespace'},
        ]

    def test_specs_endpoint_invalid_tags(self, app, client):
        restplus.Api(app, tags=[
            {'description': 'Tag 1'}
        ])

        client.get_specs('', status=500)

    def test_specs_authorizations(self, app, client):
        authorizations = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        }
        restplus.Api(app, authorizations=authorizations)

        data = client.get_specs()

        assert 'securityDefinitions' in data
        assert data['securityDefinitions'] == authorizations

    @pytest.mark.api(prefix='/api')
    def test_minimal_documentation(self, api, client):
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = client.get_specs('/api')
        paths = data['paths']
        assert len(paths.keys()) == 1

        assert '/ns/' in paths
        assert 'get' in paths['/ns/']
        op = paths['/ns/']['get']
        assert op['tags'] == ['ns']
        assert op['operationId'] == 'get_test_resource'
        assert 'parameters' not in op
        assert 'summary' not in op
        assert 'description' not in op
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            }
        }

        assert url_for('api.test') == '/api/ns/'

    @pytest.mark.api(prefix='/api', version='1.0')
    def test_default_ns_resource_documentation(self, api, client):
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = client.get_specs('/api')
        paths = data['paths']
        assert len(paths.keys()) == 1

        assert '/test/' in paths
        assert 'get' in paths['/test/']
        op = paths['/test/']['get']
        assert op['tags'] == ['default']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            }
        }

        assert len(data['tags']) == 1
        tag = data['tags'][0]
        assert tag['name'] == 'default'
        assert tag['description'] == 'Default namespace'

        assert url_for('api.test') == '/api/test/'

    @pytest.mark.api(default='site', default_label='Site namespace')
    def test_default_ns_resource_documentation_with_override(self, api, client):
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = client.get_specs()
        paths = data['paths']
        assert len(paths.keys()) == 1

        assert '/test/' in paths
        assert 'get' in paths['/test/']
        op = paths['/test/']['get']
        assert op['tags'] == ['site']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            }
        }

        assert len(data['tags']) == 1
        tag = data['tags'][0]
        assert tag['name'] == 'site'
        assert tag['description'] == 'Site namespace'

        assert url_for('api.test') == '/test/'

    @pytest.mark.api(prefix='/api')
    def test_ns_resource_documentation(self, api, client):
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = client.get_specs('/api')
        paths = data['paths']
        assert len(paths.keys()) == 1

        assert '/ns/' in paths
        assert 'get' in paths['/ns/']
        op = paths['/ns/']['get']
        assert op['tags'] == ['ns']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            }
        }
        assert 'parameters' not in op

        assert len(data['tags']) == 2
        tag = data['tags'][-1]
        assert tag['name'] == 'ns'
        assert tag['description'] == 'Test namespace'

        assert url_for('api.test') == '/api/ns/'

    def test_ns_resource_documentation_lazy(self, app, client):
        api = restplus.Api()
        ns = api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        api.init_app(app)

        data = client.get_specs()
        paths = data['paths']
        assert len(paths.keys()) == 1

        assert '/ns/' in paths
        assert 'get' in paths['/ns/']
        op = paths['/ns/']['get']
        assert op['tags'] == ['ns']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            }
        }

        assert len(data['tags']) == 2
        tag = data['tags'][-1]
        assert tag['name'] == 'ns'
        assert tag['description'] == 'Test namespace'

        assert url_for('test') == '/ns/'

    def test_methods_docstring_to_summary(self, api, client):
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

        data = client.get_specs()
        path = data['paths']['/test/']

        assert len(path.keys()) == 4

        for method in path.keys():
            operation = path[method]
            assert method in ('get', 'post', 'put', 'delete')
            assert operation['summary'] == '{0} operation'.format(method.upper())
            assert operation['operationId'] == '{0}_test_resource'.format(method.lower())
            # assert operation['parameters'] == []

    def test_path_parameter_no_type(self, api, client):
        @api.route('/id/<id>/', endpoint='by-id')
        class ByIdResource(restplus.Resource):
            def get(self, id):
                return {}

        data = client.get_specs()
        assert '/id/{id}/' in data['paths']

        path = data['paths']['/id/{id}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'id'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True

    def test_path_parameter_with_type(self, api, client):
        @api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True

    def test_path_parameter_with_type_with_argument(self, api, client):
        @api.route('/name/<string(length=2):id>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            def get(self, id):
                return {}

        data = client.get_specs()
        assert '/name/{id}/' in data['paths']

        path = data['paths']['/name/{id}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'id'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True

    def test_path_parameter_with_explicit_details(self, api, client):
        @api.route('/name/<int:age>/', endpoint='by-name', doc={
            'params': {
                'age': {'description': 'An age'}
            }
        })
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'An age'

    def test_path_parameter_with_decorator_details(self, api, client):
        @api.route('/name/<int:age>/')
        @api.param('age', 'An age')
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'An age'

    def test_expect_parser(self, api, client):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            def get(self):
                return {}

        data = client.get_specs()
        assert '/with-parser/' in data['paths']

        op = data['paths']['/with-parser/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'param'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'Some param'

    def test_expect_parser_on_class(self, api, client):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        @api.expect(parser)
        class WithParserResource(restplus.Resource):
            def get(self):
                return {}

        data = client.get_specs()
        assert '/with-parser/' in data['paths']

        path = data['paths']['/with-parser/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'param'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'Some param'

    def test_method_parser_on_class(self, api, client):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        @api.doc(get={'expect': parser})
        class WithParserResource(restplus.Resource):
            def get(self):
                return {}

            def post(self):
                return {}

        data = client.get_specs()
        assert '/with-parser/' in data['paths']

        op = data['paths']['/with-parser/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'param'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'Some param'

        op = data['paths']['/with-parser/']['post']
        assert 'parameters' not in op

    def test_parser_parameters_override(self, api, client):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            @api.doc(params={'param': {'description': 'New description'}})
            def get(self):
                return {}

        data = client.get_specs()
        assert '/with-parser/' in data['paths']

        op = data['paths']['/with-parser/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'param'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'New description'

    def test_parser_parameter_in_form(self, api, client):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param', location='form')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            def get(self):
                return {}

        data = client.get_specs()
        assert '/with-parser/' in data['paths']

        op = data['paths']['/with-parser/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'param'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'formData'
        assert parameter['description'] == 'Some param'

        assert op['consumes'] == ['application/x-www-form-urlencoded', 'multipart/form-data']

    def test_parser_parameter_in_files(self, api, client):
        parser = api.parser()
        parser.add_argument('in_files', type=FileStorage, location='files')

        @api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @api.expect(parser)
            def get(self):
                return {}

        data = client.get_specs()
        assert '/with-parser/' in data['paths']

        op = data['paths']['/with-parser/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'in_files'
        assert parameter['type'] == 'file'
        assert parameter['in'] == 'formData'

        assert op['consumes'] == ['multipart/form-data']

    def test_explicit_parameters(self, api, client):
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

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True

        op = path['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'A query string'

    def test_explicit_parameters_with_decorator(self, api, client):
        @api.route('/name/')
        class ByNameResource(restplus.Resource):
            @api.param('q', 'A query string', type='string', _in='formData')
            def get(self, age):
                return {}

        data = client.get_specs()
        assert '/name/' in data['paths']

        op = data['paths']['/name/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'formData'
        assert parameter['description'] == 'A query string'

    def test_class_explicit_parameters(self, api, client):
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

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 2

        by_name = dict((p['name'], p) for p in path['parameters'])

        parameter = by_name['age']
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True

        parameter = by_name['q']
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'A query string'

    def test_explicit_parameters_override(self, api, client):
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

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 2

        by_name = dict((p['name'], p) for p in path['parameters'])

        parameter = by_name['age']
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'An age'

        parameter = by_name['q']
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'Overriden description'

        op = data['paths']['/name/{age}/']['get']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'A query string'

    def test_explicit_parameters_override_by_method(self, api, client):
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

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 1

        parameter = path['parameters'][0]
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'An age'

        op = path['get']
        assert len(op['parameters']) == 2

        by_name = dict((p['name'], p) for p in op['parameters'])

        parameter = by_name['age']
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'Overriden'

        parameter = by_name['q']
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'A query string'

        assert 'parameters' not in path['post']

    def test_explicit_parameters_desription_shortcut(self, api, client):
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

        data = client.get_specs()
        assert '/name/{age}/' in data['paths']

        path = data['paths']['/name/{age}/']
        assert len(path['parameters']) == 1
        parameter = path['parameters'][0]
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'An age'

        op = path['get']
        assert len(op['parameters']) == 2

        by_name = dict((p['name'], p) for p in op['parameters'])

        parameter = by_name['age']
        assert parameter['name'] == 'age'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'path'
        assert parameter['required'] is True
        assert parameter['description'] == 'Overriden'

        parameter = by_name['q']
        assert parameter['name'] == 'q'
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'A query string'

        assert 'parameters' not in path['post']

    def test_explicit_parameters_native_types(self, api, client):
        @api.route('/types/', endpoint='native')
        class NativeTypesResource(restplus.Resource):
            @api.doc(params={
                'int': {
                    'type': int,
                    'in': 'query',
                },
                'float': {
                    'type': float,
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
                'float-array': {
                    'type': [float],
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

        data = client.get_specs()

        op = data['paths']['/types/']['get']

        parameters = dict((p['name'], p) for p in op['parameters'])

        assert parameters['int']['type'] == 'integer'
        assert parameters['float']['type'] == 'number'
        assert parameters['str']['type'] == 'string'
        assert parameters['bool']['type'] == 'boolean'

        assert parameters['int-array']['type'] == 'array'
        assert parameters['int-array']['items']['type'] == 'integer'
        assert parameters['float-array']['type'] == 'array'
        assert parameters['float-array']['items']['type'] == 'number'
        assert parameters['str-array']['type'] == 'array'
        assert parameters['str-array']['items']['type'] == 'string'
        assert parameters['bool-array']['type'] == 'array'
        assert parameters['bool-array']['items']['type'] == 'boolean'

    def test_response_on_method(self, api, client):
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

        data = client.get_specs('')
        paths = data['paths']
        assert len(paths.keys()) == 1

        op = paths['/test/']['get']
        assert op['tags'] == ['default']
        assert op['responses'] == {
            '404': {
                'description': 'Not found',
            },
            '405': {
                'description': 'Some message',
                'schema': {
                    '$ref': '#/definitions/ErrorModel',
                }
            }
        }

        assert 'definitions' in data
        assert 'ErrorModel' in data['definitions']

    def test_api_response(self, api, client):
        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response(200, 'Success')
            def get(self):
                pass

        data = client.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            }
        }

    def test_api_response_multiple(self, api, client):
        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response(200, 'Success')
            @api.response(400, 'Validation error')
            def get(self):
                pass

        data = client.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
            },
            '400': {
                'description': 'Validation error',
            }
        }

    def test_api_response_with_model(self, api, client):
        model = api.model('SomeModel', {
            'message': restplus.fields.String,
        })

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response(200, 'Success', model)
            def get(self):
                pass

        data = client.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        assert op['responses'] == {
            '200': {
                'description': 'Success',
                'schema': {
                    '$ref': '#/definitions/SomeModel',
                }
            }
        }

        assert 'SomeModel' in data['definitions']

    def test_api_response_default(self, api, client):
        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.response('default', 'Error')
            def get(self):
                pass

        data = client.get_specs('')
        paths = data['paths']

        op = paths['/test/']['get']
        assert op['responses'] == {
            'default': {
                'description': 'Error',
            }
        }

    def test_api_header(self, api, client):
        @api.route('/test/')
        @api.header('X-HEADER', 'A class header')
        class TestResource(restplus.Resource):

            @api.header('X-HEADER-2', 'Another header', type=[int], collectionFormat='csv')
            @api.header('X-HEADER-3', type=int)
            @api.header('X-HEADER-4', type='boolean')
            def get(self):
                pass

        data = client.get_specs('')
        headers = data['paths']['/test/']['get']['responses']['200']['headers']

        assert 'X-HEADER' in headers
        assert headers['X-HEADER'] == {
            'type': 'string',
            'description': 'A class header',
        }

        assert 'X-HEADER-2' in headers
        assert headers['X-HEADER-2'] == {
            'type': 'array',
            'items': {'type': 'integer'},
            'description': 'Another header',
            'collectionFormat': 'csv',
        }

        assert 'X-HEADER-3' in headers
        assert headers['X-HEADER-3'] == {'type': 'integer'}

        assert 'X-HEADER-4' in headers
        assert headers['X-HEADER-4'] == {'type': 'boolean'}

    def test_response_header(self, api, client):
        @api.route('/test/')
        class TestResource(restplus.Resource):
            @api.response(200, 'Success')
            @api.response(400, 'Validation', headers={'X-HEADER': 'An header'})
            def get(self):
                pass

        data = client.get_specs('')
        headers = data['paths']['/test/']['get']['responses']['400']['headers']

        assert 'X-HEADER' in headers
        assert headers['X-HEADER'] == {
            'type': 'string',
            'description': 'An header',
        }

    def test_api_and_response_header(self, api, client):
        @api.route('/test/')
        @api.header('X-HEADER', 'A class header')
        class TestResource(restplus.Resource):

            @api.header('X-HEADER-2', type=int)
            @api.response(200, 'Success')
            @api.response(400, 'Validation', headers={'X-ERROR': 'An error header'})
            def get(self):
                pass

        data = client.get_specs('')
        headers200 = data['paths']['/test/']['get']['responses']['200']['headers']
        headers400 = data['paths']['/test/']['get']['responses']['400']['headers']

        for headers in (headers200, headers400):
            assert 'X-HEADER' in headers
            assert 'X-HEADER-2' in headers

        assert 'X-ERROR' in headers400
        assert 'X-ERROR' not in headers200

    def test_expect_header(self, api, client):
        parser = api.parser()
        parser.add_argument('X-Header', location='headers', required=True, help='A required header')
        parser.add_argument('X-Header-2', location='headers', type=int, action='split', help='Another header')
        parser.add_argument('X-Header-3', location='headers', type=int)
        parser.add_argument('X-Header-4', location='headers', type=inputs.boolean)

        @api.route('/test/')
        class TestResource(restplus.Resource):

            @api.expect(parser)
            def get(self):
                pass

        data = client.get_specs('')
        parameters = data['paths']['/test/']['get']['parameters']

        def get_param(name):
            candidates = [p for p in parameters if p['name'] == name]
            assert len(candidates) == 1, 'parameter {0} not found'.format(name)
            return candidates[0]

        parameter = get_param('X-Header')
        assert parameter['type'] == 'string'
        assert parameter['in'] == 'header'
        assert parameter['required'] is True
        assert parameter['description'] == 'A required header'

        parameter = get_param('X-Header-2')
        assert parameter['type'] == 'array'
        assert parameter['in'] == 'header'
        assert parameter['items']['type'] == 'integer'
        assert parameter['description'] == 'Another header'
        assert parameter['collectionFormat'] == 'csv'

        parameter = get_param('X-Header-3')
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'header'

        parameter = get_param('X-Header-4')
        assert parameter['type'] == 'boolean'
        assert parameter['in'] == 'header'

    def test_description(self, api, client):
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

        data = client.get_specs()

        description = lambda m: data['paths']['/description/'][m]['description']  # noqa

        assert description('get') == dedent('''\
            Parent description.
            Some details'''
        )

        assert description('post') == dedent('''\
            Parent description.
            Extra description'''
        )

        assert description('delete') == dedent('''\
            Parent description.
            A delete operation'''
        )

        assert description('put') == 'Parent description.'
        assert 'description' not in data['paths']['/descriptionless/']['get']

    def test_operation_id(self, api, client):
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc(id='get_objects')
            def get(self):
                return {}

            def post(self):
                return {}

        data = client.get_specs()
        path = data['paths']['/test/']

        assert path['get']['operationId'] == 'get_objects'
        assert path['post']['operationId'] == 'post_test_resource'

    def test_operation_id_shortcut(self, api, client):
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc('get_objects')
            def get(self):
                return {}

        data = client.get_specs()
        path = data['paths']['/test/']

        assert path['get']['operationId'] == 'get_objects'

    def test_custom_default_operation_id(self, app, client):
        def default_id(resource, method):
            return '{0}{1}'.format(method, resource)

        api = restplus.Api(app, default_id=default_id)

        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc(id='get_objects')
            def get(self):
                return {}

            def post(self):
                return {}

        data = client.get_specs()
        path = data['paths']['/test/']

        assert path['get']['operationId'] == 'get_objects'
        assert path['post']['operationId'] == 'postTestResource'

    @pytest.mark.api(default_id=lambda r, m: '{0}{1}'.format(m, r))
    def test_custom_default_operation_id_blueprint(self, api, client):
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            @api.doc(id='get_objects')
            def get(self):
                return {}

            def post(self):
                return {}

        data = client.get_specs()
        path = data['paths']['/test/']

        assert path['get']['operationId'] == 'get_objects'
        assert path['post']['operationId'] == 'postTestResource'

    def test_model_primitive_types(self, api, client):
        @api.route('/model-int/')
        class ModelInt(restplus.Resource):
            @api.doc(model=int)
            def get(self):
                return {}

        data = client.get_specs()

        assert 'definitions' not in data
        assert data['paths']['/model-int/']['get']['responses'] == {
            '200': {
                'description': 'Success',
                'schema': {
                    'type': 'integer'
                }
            }
        }

    def test_model_as_flat_dict(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        path = data['paths']['/model-as-dict/']
        assert path['get']['responses']['200']['schema']['$ref'] == '#/definitions/Person'
        assert path['post']['responses']['200']['schema']['$ref'] == '#/definitions/Person'

    def test_model_as_nested_dict(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        assert 'Address' in data['definitions'].keys()
        assert data['definitions']['Address'] == {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        }

        path = data['paths']['/model-as-dict/']
        assert path['get']['responses']['200']['schema']['$ref'] == '#/definitions/Person'
        assert path['post']['responses']['200']['schema']['$ref'] == '#/definitions/Person'

    def test_model_as_flat_dict_with_marchal_decorator(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        responses = data['paths']['/model-as-dict/']['get']['responses']
        assert responses == {
            '200': {
                'description': 'Success',
                'schema': {
                    '$ref': '#/definitions/Person'
                }
            }
        }

    def test_marchal_decorator_with_code(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        responses = data['paths']['/model-as-dict/']['delete']['responses']
        assert responses == {
            '204': {
                'description': 'Success',
                'schema': {
                    '$ref': '#/definitions/Person'
                }
            }
        }

    def test_marchal_decorator_with_description(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        responses = data['paths']['/model-as-dict/']['get']['responses']
        assert responses == {
            '200': {
                'description': 'Some details',
                'schema': {
                    '$ref': '#/definitions/Person'
                }
            }
        }

    def test_model_as_flat_dict_with_marchal_decorator_list(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        path = data['paths']['/model-as-dict/']
        assert path['get']['responses']['200']['schema'] == {
            'type': 'array',
            'items': {'$ref': '#/definitions/Person'},
        }

    def test_model_as_flat_dict_with_marchal_decorator_list_alt(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        path = data['paths']['/model-as-dict/']
        assert path['get']['responses']['200']['schema'] == {
            'type': 'array',
            'items': {'$ref': '#/definitions/Person'},
        }

    def test_model_as_flat_dict_with_marchal_decorator_list_kwargs(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        path = data['paths']['/model-as-dict/']
        assert path['get']['responses'] == {
            '201': {
                'description': 'Some details',
                'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/definitions/Person'},
                }
            }
        }

    def test_model_as_dict_with_list(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        path = data['paths']['/model-with-list/']
        assert path['get']['responses']['200']['schema'] == {'$ref': '#/definitions/Person'}

    def test_model_as_nested_dict_with_list(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert 'Address' in data['definitions']

    def test_model_list_of_primitive_types(self, api, client):
        @api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model=[int])
            def get(self):
                return {}

            @api.doc(model=[str])
            def post(self):
                return {}

        data = client.get_specs()

        assert 'definitions' not in data

        path = data['paths']['/model-list/']
        assert path['get']['responses']['200']['schema'] == {
            'type': 'array',
            'items': {'type': 'integer'},
        }
        assert path['post']['responses']['200']['schema'] == {
            'type': 'array',
            'items': {'type': 'string'},
        }

    def test_model_list_as_flat_dict(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']

        path = data['paths']['/model-as-dict/']
        for method in 'get', 'post':
            assert path[method]['responses']['200']['schema'] == {
                'type': 'array',
                'items': {'$ref': '#/definitions/Person'},
            }

    def test_model_doc_on_class(self, api, client):
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

        data = client.get_specs()
        assert 'definitions' in data
        assert 'Person' in data['definitions']

        path = data['paths']['/model-as-dict/']
        for method in 'get', 'post':
            assert path[method]['responses']['200']['schema'] == {'$ref': '#/definitions/Person'}

    def test_model_doc_for_method_on_class(self, api, client):
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

        data = client.get_specs()
        assert 'definitions' in data
        assert 'Person' in data['definitions']

        path = data['paths']['/model-as-dict/']
        assert path['get']['responses']['200']['schema'] == {'$ref': '#/definitions/Person'}
        assert 'schema' not in path['post']['responses']['200']

    def test_model_with_discriminator(self, api, client):
        fields = api.model('Person', {
            'name': restplus.fields.String(discriminator=True),
            'age': restplus.fields.Integer,
        })

        @api.route('/model-with-discriminator/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields)
            def get(self):
                return {}

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name'],
            'type': 'object'
        }

    def test_model_with_discriminator_override_require(self, api, client):
        fields = api.model('Person', {
            'name': restplus.fields.String(discriminator=True, required=False),
            'age': restplus.fields.Integer,
        })

        @api.route('/model-with-discriminator/')
        class ModelAsDict(restplus.Resource):
            @api.marshal_with(fields)
            def get(self):
                return {}

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name'],
            'type': 'object'
        }

    def test_model_not_found(self, api, client):
        @api.route('/model-not-found/')
        class ModelAsDict(restplus.Resource):
            @api.doc(model='NotFound')
            def get(self):
                return {}

        client.get_specs(status=500)

    def test_clone(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' not in data['definitions']
        assert 'Child' in data['definitions']

        path = data['paths']['/extend/']
        assert path['get']['responses']['200']['schema']['$ref'] == '#/definitions/Child'
        assert path['post']['responses']['200']['schema']['$ref'] == '#/definitions/Child'

    def test_inherit(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert 'Child' in data['definitions']
        assert data['definitions']['Person'] == {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'type': 'object'
        }
        assert data['definitions']['Child'] == {
            'allOf': [{
                '$ref': '#/definitions/Person'
            }, {
                'properties': {
                    'extra': {'type': 'string'}
                },
                'type': 'object'
            }]
        }

        path = data['paths']['/inherit/']
        assert path['get']['responses']['200']['schema']['$ref'] == '#/definitions/Child'
        assert path['post']['responses']['200']['schema']['$ref'] == '#/definitions/Child'

        data = client.get_json('/inherit/')
        assert data == {
            'name': 'John',
            'age': 42,
            'extra': 'test',
        }

    def test_inherit_inline(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert 'Child' in data['definitions']

        data = client.get_json('/inherit/')
        assert data == {
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

    def test_polymorph_inherit(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert 'Child1' in data['definitions']
        assert 'Child2' in data['definitions']
        assert 'Output' in data['definitions']

        path = data['paths']['/polymorph/']
        assert path['get']['responses']['200']['schema']['$ref'] == '#/definitions/Output'

    def test_polymorph_inherit_list(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert 'Child1' in data['definitions']
        assert 'Child2' in data['definitions']
        assert 'Output' in data['definitions']

        path = data['paths']['/polymorph/']
        assert path['get']['responses']['200']['schema']['$ref'] == '#/definitions/Output'

        data = client.get_json('/polymorph/')
        assert data == {
            'children': [{
                'name': 'Child1',
                'extra1': 'extra1',
            }, {
                'name': 'Child2',
                'extra2': 'extra2',
            }]
        }

    def test_expect_model(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        op = data['paths']['/model-as-dict/']['post']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Person'
            }
        }
        assert 'description' not in parameter

    def test_body_model_shortcut(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        op = data['paths']['/model-as-dict/']['post']
        assert op['responses']['200']['schema']['$ref'] == '#/definitions/Person'

        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]
        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Person'
            }
        }
        assert 'description' not in parameter

    def test_expect_model_list(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        op = data['paths']['/model-list/']['post']
        parameter = op['parameters'][0]

        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Person'},
            }
        }

    def test_both_model_and_parser_from_expect(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        assert '/with-parser/' in data['paths']

        op = data['paths']['/with-parser/']['get']
        assert len(op['parameters']) == 2

        parameters = dict((p['in'], p) for p in op['parameters'])

        parameter = parameters['query']
        assert parameter['name'] == 'param'
        assert parameter['type'] == 'integer'
        assert parameter['in'] == 'query'
        assert parameter['description'] == 'Some param'

        parameter = parameters['body']
        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Person'
            }
        }

    def test_expect_primitive_list(self, api, client):
        @api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @api.expect([restplus.fields.String])
            def post(self):
                return {}

        data = client.get_specs()

        op = data['paths']['/model-list/']['post']
        parameter = op['parameters'][0]
        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {'type': 'string'},
            }
        }

    def test_body_model_list(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        op = data['paths']['/model-list/']['post']
        parameter = op['parameters'][0]

        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Person'},
            }
        }

    def test_expect_model_with_description(self, api, client):
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

        data = client.get_specs()

        assert 'definitions' in data
        assert 'Person' in data['definitions']
        assert data['definitions']['Person'] == {
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
        }

        op = data['paths']['/model-as-dict/']['post']
        assert len(op['parameters']) == 1

        parameter = op['parameters'][0]

        assert parameter == {
            'name': 'payload',
            'in': 'body',
            'required': True,
            'description': 'Body description',
            'schema': {
                '$ref': '#/definitions/Person'
            }
        }

    def test_authorizations(self, app, client):
        restplus.Api(app, authorizations={
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

        data = client.get_specs()
        assert 'securityDefinitions' in data
        assert 'security' not in data

        # path = data['paths']['/authorizations/']
        # assert 'security' not in path['get']
        # assert path['post']['security'] == {'apikey': []}

    def test_single_root_security_string(self, app, client):
        api = restplus.Api(app, security='apikey', authorizations={
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

        data = client.get_specs()
        assert data['securityDefinitions'] == {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        }
        assert data['security'] == [{'apikey': []}]

        op = data['paths']['/authorizations/']['post']
        assert 'security' not in op

    def test_single_root_security_object(self, app, client):
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

        api = restplus.Api(app,
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

        data = client.get_specs()
        assert data['securityDefinitions'] == security_definitions
        assert data['security'] == [{
            'oauth2': ['read'],
            'implicit': ['read', 'write']
        }]

        op = data['paths']['/authorizations/']['post']
        assert 'security' not in op

    def test_root_security_as_list(self, app, client):
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
        api = restplus.Api(app, security=['apikey', {'oauth2': 'read'}], authorizations=security_definitions)

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            def post(self):
                return {}

        data = client.get_specs()
        assert data['securityDefinitions'] == security_definitions
        assert data['security'] == [{'apikey': []}, {'oauth2': ['read']}]

        op = data['paths']['/authorizations/']['post']
        assert 'security' not in op

    def test_method_security(self, app, client):
        api = restplus.Api(app, authorizations={
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

        data = client.get_specs()
        assert data['securityDefinitions'] == {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API'
            }
        }
        assert 'security' not in data

        path = data['paths']['/authorizations/']
        for method in 'get', 'post':
            assert path[method]['security'] == [{'apikey': []}]

    def test_security_override(self, app, client):
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
        api = restplus.Api(app, security=['apikey', {'oauth2': 'read'}], authorizations=security_definitions)

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            @api.doc(security=[{'oauth2': ['read', 'write']}])
            def get(self):
                return {}

        data = client.get_specs()
        assert data['securityDefinitions'] == security_definitions

        op = data['paths']['/authorizations/']['get']
        assert op['security'] == [{'oauth2': ['read', 'write']}]

    def test_security_nullify(self, app, client):
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
        api = restplus.Api(app, security=['apikey', {'oauth2': 'read'}], authorizations=security_definitions)

        @api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            @api.doc(security=[])
            def get(self):
                return {}

            @api.doc(security=None)
            def post(self):
                return {}

        data = client.get_specs()
        assert data['securityDefinitions'] == security_definitions

        path = data['paths']['/authorizations/']
        for method in 'get', 'post':
            assert path[method]['security'] == []

    def test_hidden_resource(self, api, client):
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

        data = client.get_specs()
        for path in '/test/', '/test2/', '/test3/':
            assert path not in data['paths']

            resp = client.get(path)
            assert resp.status_code == 200

    def test_hidden_resource_from_namespace(self, api, client):
        ns = api.namespace('ns')

        @ns.route('/test/', endpoint='test', doc=False)
        class TestResource(restplus.Resource):
            def get(self):
                '''
                GET operation
                '''
                return {}

        data = client.get_specs()
        assert '/ns/test/' not in data['paths']

        resp = client.get('/ns/test/')
        assert resp.status_code == 200

    def test_hidden_methods(self, api, client):
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

        data = client.get_specs()
        path = data['paths']['/test/']

        assert 'get' in path
        assert 'post' not in path
        assert 'put' not in path

        for method in 'GET', 'POST', 'PUT':
            resp = client.open('/test/', method=method)
            assert resp.status_code == 200

    def test_deprecated_resource(self, api, client):
        @api.deprecated
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                pass

            def post(self):
                pass

        data = client.get_specs()
        resource = data['paths']['/test/']
        for operation in resource.values():
            assert 'deprecated' in operation
            assert operation['deprecated'] is True

    def test_deprecated_method(self, api, client):
        @api.route('/test/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                pass

            @api.deprecated
            def post(self):
                pass

        data = client.get_specs()

        get_operation = data['paths']['/test/']['get']
        assert 'deprecated' not in get_operation

        post_operation = data['paths']['/test/']['post']
        assert 'deprecated' in post_operation
        assert post_operation['deprecated'] is True

    def test_vendor_as_kwargs(self, api, client):
        @api.route('/vendor_fields', endpoint='vendor_fields')
        class TestResource(restplus.Resource):
            @api.vendor(integration={'integration1': '1'})
            def get(self):
                return {}

        data = client.get_specs()

        assert '/vendor_fields' in data['paths']

        path = data['paths']['/vendor_fields']['get']

        assert 'x-integration' in path

        assert path['x-integration'] == {'integration1': '1'}

    def test_vendor_as_dict(self, api, client):
        @api.route('/vendor_fields', endpoint='vendor_fields')
        class TestResource(restplus.Resource):
            @api.vendor({
                'x-some-integration': {
                    'integration1': '1'
                },
                'another-integration': True
            }, {
                'third-integration': True
            })
            def get(self, age):
                return {}

        data = client.get_specs()

        assert '/vendor_fields' in data['paths']

        path = data['paths']['/vendor_fields']['get']
        assert 'x-some-integration' in path
        assert path['x-some-integration'] == {'integration1': '1'}

        assert 'x-another-integration' in path
        assert path['x-another-integration'] is True

        assert 'x-third-integration' in path
        assert path['x-third-integration'] is True

    def test_method_restrictions(self, api, client):
        @api.route('/foo/bar', endpoint='foo')
        @api.route('/bar', methods=['GET'], endpoint='bar')
        class TestResource(restplus.Resource):
            def get(self):
                pass

            def post(self):
                pass

        data = client.get_specs()

        path = data['paths']['/foo/bar']
        assert 'get' in path
        assert 'post' in path

        path = data['paths']['/bar']
        assert 'get' in path
        assert 'post' not in path


class SwaggerDeprecatedTest(object):
    def test_doc_parser_parameters(self, api):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        with pytest.warns(DeprecationWarning):
            @api.route('/with-parser/')
            class WithParserResource(restplus.Resource):
                @api.doc(parser=parser)
                def get(self):
                    return {}

        assert 'parser' not in WithParserResource.get.__apidoc__
        assert 'expect' in WithParserResource.get.__apidoc__
        doc_parser = WithParserResource.get.__apidoc__['expect'][0]
        assert doc_parser.__schema__ == parser.__schema__

    def test_doc_method_parser_on_class(self, api):
        parser = api.parser()
        parser.add_argument('param', type=int, help='Some param')

        with pytest.warns(DeprecationWarning):
            @api.route('/with-parser/')
            @api.doc(get={'parser': parser})
            class WithParserResource(restplus.Resource):
                def get(self):
                    return {}

                def post(self):
                    return {}

        assert 'parser' not in WithParserResource.__apidoc__['get']
        assert 'expect' in WithParserResource.__apidoc__['get']
        doc_parser = WithParserResource.__apidoc__['get']['expect'][0]
        assert doc_parser.__schema__ == parser.__schema__

    def test_doc_body_as_tuple(self, api):
        fields = api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        with pytest.warns(DeprecationWarning):
            @api.route('/model-as-dict/')
            class ModelAsDict(restplus.Resource):
                @api.doc(body=(fields, 'Body description'))
                def post(self):
                    return {}

        assert 'body' not in ModelAsDict.post.__apidoc__
        assert ModelAsDict.post.__apidoc__['expect'] == [(fields, 'Body description')]
