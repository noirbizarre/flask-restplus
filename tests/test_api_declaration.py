# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from textwrap import dedent

from flask import url_for
from flask.ext import restplus

from . import TestCase


class APITestCase(TestCase):
    def setUp(self):
        super(APITestCase, self).setUp()
        self.api = restplus.Api(self.app, prefix='/api', version='1.0')

    def test_specs_endpoint_produces_default(self):
        data = self.get_declaration()
        self.assertEqual(data['produces'], ['application/json'])

    def test_specs_endpoint_produces(self):
        def output_xml(data, code, headers=None):
            pass

        self.api.representations['application/xml'] = output_xml

        data = self.get_declaration()
        self.assertEqual(len(data['produces']), 2)
        self.assertIn('application/json', data['produces'])
        self.assertIn('application/xml', data['produces'])

    def test_minimal_documentation(self):
        ns = self.api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
        class TestResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_declaration('ns')
        self.assertEqual(data['apiVersion'], '1.0')
        self.assertEqual(data['swaggerVersion'], '1.2')
        self.assertEqual(data['basePath'], 'http://localhost/api')
        self.assertEqual(data['resourcePath'], '/ns')

        test_api = data['apis'][0]
        self.assertEqual(test_api['path'], '/ns/')
        self.assertEqual(len(test_api['operations']), 1)
        operation = test_api['operations'][0]
        self.assertEqual(operation['method'].lower(), 'get')
        self.assertEqual(operation['nickname'], 'get_test_resource')
        self.assertEqual(operation['parameters'], [])
        self.assertNotIn('summary', operation)
        self.assertNotIn('notes', operation)
        with self.context():
            self.assertEqual(url_for('api.test'), '/api/ns/')

    def test_methods_docstring_to_summary(self):
        ns = self.api.namespace('ns', 'Test namespace')

        @ns.route('/', endpoint='test')
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

        data = self.get_declaration('ns')

        api = data['apis'][0]
        self.assertEqual(api['path'], '/ns/')
        self.assertEqual(len(api['operations']), 4)
        for operation in api['operations']:
            method = operation['method']
            self.assertIn(method.lower(), ('get', 'post', 'put', 'delete'))
            self.assertEqual(operation['summary'], '{0} operation'.format(method.upper()))
            self.assertEqual(operation['nickname'], '{0}_test_resource'.format(method.lower()))
            self.assertEqual(operation['parameters'], [])

    def test_path_parameter_no_type(self):
        @self.api.route('/id/<id>/', endpoint='by-id')
        class ByIdResource(restplus.Resource):
            def get(self, id):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 1)

        parameter = operation['parameters'][0]
        self.assertEqual(parameter['name'], 'id')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)

    def test_path_parameter_with_type(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 1)

        parameter = operation['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)

    def test_path_parameter_with_explicit_details(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            @self.api.doc(params={
                'age': {'description': 'An age'}
            })
            def get(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 1)

        parameter = operation['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

    def test_parser_parameters(self):
        parser = self.api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @self.api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @self.api.doc(parser=parser)
            def get(self):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 1)

        parameter = operation['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'Some param')

    def test_parser_parameters_on_class(self):
        parser = self.api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @self.api.route('/with-parser/', endpoint='with-parser')
        @self.api.doc(parser=parser)
        class WithParserResource(restplus.Resource):
            def get(self):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 1)

        parameter = operation['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'Some param')

    def test_parser_parameters_ovrride(self):
        parser = self.api.parser()
        parser.add_argument('param', type=int, help='Some param')

        @self.api.route('/with-parser/', endpoint='with-parser')
        class WithParserResource(restplus.Resource):
            @self.api.doc(parser=parser, params={'param': {'description': 'New description'}})
            def get(self):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 1)

        parameter = operation['parameters'][0]
        self.assertEqual(parameter['name'], 'param')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'New description')

    def test_explicit_parameters(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            @self.api.doc(params={
                'q': {
                    'type': 'string',
                    'paramType': 'query',
                    'description': 'A query string',
                }
            })
            def get(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 2)

        by_name = dict((p['name'], p) for p in operation['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

    def test_class_explicit_parameters(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name', doc={
            'params': {
                'q': {
                    'type': 'string',
                    'paramType': 'query',
                    'description': 'A query string',
                }
            }
        })
        class ByNameResource(restplus.Resource):
            def get(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 2)

        by_name = dict((p['name'], p) for p in operation['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

    def test_explicit_parameters_override(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name', doc={
            'params': {
                'q': {
                    'type': 'string',
                    'paramType': 'query',
                    'description': 'Overriden description',
                },
                'age': {
                    'description': 'An age'
                }
            }
        })
        class ByNameResource(restplus.Resource):
            @self.api.doc(params={'q': {'description': 'A query string'}})
            def get(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['parameters']), 2)

        by_name = dict((p['name'], p) for p in operation['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

    def test_explicit_parameters_override_by_method(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name', doc={
            'get': {
                'params': {
                    'q': {
                        'type': 'string',
                        'paramType': 'query',
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
            @self.api.doc(params={'age': {'description': 'Overriden'}})
            def get(self, age):
                return {}

            def post(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 2)

        by_method = dict((o['method'].lower(), o) for o in api['operations'])

        op_get = by_method['get']
        self.assertEqual(len(op_get['parameters']), 2)

        by_name = dict((p['name'], p) for p in op_get['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'Overriden')

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

        op_post = by_method['post']
        self.assertEqual(len(op_post['parameters']), 1)

        parameter = op_post['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

    def test_explicit_parameters_desription_shortcut(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name', doc={
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
            @self.api.doc(params={'age': 'Overriden'})
            def get(self, age):
                return {}

            def post(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 2)

        by_method = dict((o['method'].lower(), o) for o in api['operations'])

        op_get = by_method['get']
        self.assertEqual(len(op_get['parameters']), 2)

        by_name = dict((p['name'], p) for p in op_get['parameters'])

        parameter = by_name['age']
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'Overriden')

        parameter = by_name['q']
        self.assertEqual(parameter['name'], 'q')
        self.assertEqual(parameter['type'], 'string')
        self.assertEqual(parameter['paramType'], 'query')
        self.assertEqual(parameter['description'], 'A query string')

        op_post = by_method['post']
        self.assertEqual(len(op_post['parameters']), 1)

        parameter = op_post['parameters'][0]
        self.assertEqual(parameter['name'], 'age')
        self.assertEqual(parameter['type'], 'integer')
        self.assertEqual(parameter['paramType'], 'path')
        self.assertEqual(parameter['required'], True)
        self.assertEqual(parameter['description'], 'An age')

    def test_response_on_method(self):
        @self.api.route('/name/<int:age>/', endpoint='by-name')
        class ByNameResource(restplus.Resource):
            @self.api.doc(responses={
                404: 'Not found',
                405: ('Some message', 'ErrorModel'),
            })
            def get(self, age):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        self.assertEqual(len(api['operations']), 1)

        operation = api['operations'][0]
        self.assertEqual(len(operation['responseMessages']), 2)

        by_code = dict((r['code'], r) for r in operation['responseMessages'])

        self.assertEqual(by_code[404]['message'], 'Not found')
        self.assertNotIn('responseModel', by_code[404])

        self.assertEqual(by_code[405]['message'], 'Some message')
        self.assertEqual(by_code[405]['responseModel'], 'ErrorModel')

    def test_notes(self):
        @self.api.route('/notes/', endpoint='notes', doc={
            'notes': 'Parent note.',
            'delete': {'notes': 'A delete operation'},
        })
        class ResourceWithNotes(restplus.Resource):
            @self.api.doc(notes='Some details')
            def get(self):
                return {}

            def post(self):
                '''
                Do something.

                Extra note
                '''
                return {}

            def put(self):
                '''No notes (only summary)'''

            def delete(self):
                '''No notes (only summary)'''

        @self.api.route('/noteless/', endpoint='noteless')
        class ResourceWithoutNotes(restplus.Resource):
            def get(self):
                '''No notes (only summary)'''
                return {}

        data = self.get_declaration()

        ops = dict(
            ((o['method'].lower(), a['path']), o)
            for a in data['apis']
            for o in a['operations']
        )

        notes = lambda m, p: ops[(m, p)]['notes']

        self.assertEqual(notes('get', '/notes/'), dedent('''\
            Parent note.
            Some details'''
        ))

        self.assertEqual(notes('post', '/notes/'), dedent('''\
            Parent note.
            Extra note'''
        ))

        self.assertEqual(notes('delete', '/notes/'), dedent('''\
            Parent note.
            A delete operation'''
        ))

        self.assertEqual(notes('put', '/notes/'), 'Parent note.')
        self.assertNotIn('notes', ops[('get', '/noteless/')])

    def test_nicknames(self):
        @self.api.route('/notes/', endpoint='notes')
        class TestResource(restplus.Resource):
            @self.api.doc(nickname='get_objects')
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_declaration()

        api = data['apis'][0]
        by_method = dict((o['method'].lower(), o) for o in api['operations'])

        self.assertEqual(by_method['get']['nickname'], 'get_objects')

        self.assertEqual(by_method['post']['nickname'], 'post_test_resource')

    def test_model_void(self):
        @self.api.route('/model-void/')
        class ModelVoid(restplus.Resource):
            @self.api.doc(model=None)
            def get(self):
                return {}

        data = self.get_declaration()

        self.assertNotIn('models', data)

        self.assertEqual(data['apis'][0]['operations'][0]['type'], 'void')

    def test_model_primitive_types(self):
        @self.api.route('/model-int/')
        class ModelVoid(restplus.Resource):
            @self.api.doc(model=int)
            def get(self):
                return {}

        data = self.get_declaration()

        self.assertNotIn('models', data)

        self.assertEqual(data['apis'][0]['operations'][0]['type'], 'integer')

    def test_model_as_flat_dict(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @self.api.doc(model=fields)
            def get(self):
                return {}

            @self.api.doc(model='Person')
            def post(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())
        self.assertEqual(data['models']['Person'], {
            'id': 'Person',
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
            }
        })

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        self.assertEqual(ops['get']['type'], 'Person')
        self.assertEqual(ops['post']['type'], 'Person')

    def test_model_as_flat_dict_with_marchal_decorator(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @self.api.marshal_with(fields)
            def get(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())
        self.assertEqual(data['apis'][0]['operations'][0]['type'], 'Person')

    def test_model_as_flat_dict_with_marchal_decorator_list(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @self.api.marshal_with(fields, as_list=True)
            def get(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())
        self.assertEqual(data['apis'][0]['operations'][0]['type'], 'array')
        self.assertEqual(data['apis'][0]['operations'][0]['items'], {'$ref': 'Person'})

    def test_model_as_flat_dict_with_marchal_decorator_list_alt(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @self.api.marshal_list_with(fields)
            def get(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())
        self.assertEqual(data['apis'][0]['operations'][0]['type'], 'array')
        self.assertEqual(data['apis'][0]['operations'][0]['items'], {'$ref': 'Person'})

    def test_model_as_dict_with_list(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'tags': restplus.fields.List(restplus.fields.String),
        })

        @self.api.route('/model-with-list/')
        class ModelAsDict(restplus.Resource):
            @self.api.doc(model=fields)
            def get(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())
        self.assertEqual(data['models']['Person'], {
            'id': 'Person',
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
            }
        })

    def test_model_list_of_primitive_types(self):
        @self.api.route('/model-list/')
        class ModelAsDict(restplus.Resource):
            @self.api.doc(model=[int])
            def get(self):
                return {}

            @self.api.doc(model=[str])
            def post(self):
                return {}

        data = self.get_declaration()

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        self.assertEqual(ops['get']['type'], 'array')
        self.assertEqual(ops['get']['items'], {'type': 'integer'})
        self.assertEqual(ops['post']['type'], 'array')
        self.assertEqual(ops['post']['items'], {'type': 'string'})

    def test_model_list_as_flat_dict(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        class ModelAsDict(restplus.Resource):
            @self.api.doc(model=[fields])
            def get(self):
                return {}

            @self.api.doc(model=['Person'])
            def post(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        for method in 'get', 'post':
            self.assertEqual(ops[method]['type'], 'array')
            self.assertEqual(ops[method]['items'], {'$ref': 'Person'})

    def test_model_doc_on_class(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        @self.api.doc(model=fields)
        class ModelAsDict(restplus.Resource):
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        self.assertEqual(ops['get']['type'], 'Person')
        self.assertEqual(ops['post']['type'], 'Person')

    def test_model_doc_for_method_on_class(self):
        fields = self.api.model('Person', {
            'name': restplus.fields.String,
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @self.api.route('/model-as-dict/')
        @self.api.doc(get={'model': fields})
        class ModelAsDict(restplus.Resource):
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_declaration()

        self.assertIn('models', data)
        self.assertIn('Person', data['models'].keys())

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        self.assertEqual(ops['get']['type'], 'Person')
        self.assertNotIn('type', ops['post'])

    def test_model_not_found(self):
        @self.api.route('/model-not-found/')
        class ModelAsDict(restplus.Resource):
            @self.api.doc(model='NotFound')
            def get(self):
                return {}

        data = self.get_declaration(status=500)

        self.assertEqual(data['status'], 500)

    def test_authorizations(self):
        authorizations = {
            'apikey': {
                'type': 'apiKey',
                'passAs': 'header',
                'keyname': 'X-API'
            }
        }
        self.api.authorizations = authorizations

        @self.api.route('/authorizations/')
        class ModelAsDict(restplus.Resource):
            def get(self):
                return {}

            @self.api.doc(authorizations='apikey')
            def post(self):
                return {}

        data = self.get_declaration()

        self.assertNotIn('authorizations', data)

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        self.assertNotIn('authorizations', ops['get'])
        self.assertEqual(ops['post']['authorizations'], {'apikey': []})

    def test_authorizations_overwrite(self):
        authorizations = {
            'apikey': {
                'type': 'apiKey',
                'passAs': 'header',
                'keyname': 'X-API'
            }
        }
        self.api.authorizations = authorizations

        @self.api.route('/authorizations/')
        @self.api.doc(authorizations='apikey')
        class ModelAsDict(restplus.Resource):
            @self.api.doc(authorizations=None)
            def get(self):
                return {}

            def post(self):
                return {}

        data = self.get_declaration()

        self.assertNotIn('authorizations', data)

        ops = dict((o['method'].lower(), o) for o in data['apis'][0]['operations'])
        self.assertEqual(ops['get']['authorizations'], {})
        self.assertEqual(ops['post']['authorizations'], {'apikey': []})
