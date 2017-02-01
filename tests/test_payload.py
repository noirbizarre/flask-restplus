# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import flask_restplus as restplus

from . import TestCase


class PayloadTestCase(TestCase):
    def post(self, url, data):
        with self.app.test_client() as client:
            return client.post(url, data=json.dumps(data),
                               headers={'content-type': 'application/json'})

    def assert_errors(self, response, *errors):
        self.assertEquals(response.status_code, 400)
        out = json.loads(response.data.decode('utf8'))
        self.assertIn('message', out)
        self.assertIn('errors', out)
        for error in errors:
            self.assertIn(error, out['errors'])

    def test_validation_false_on_constructor(self):
        api = restplus.Api(self.app, validate=False)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assertEquals(response.status_code, 200)
        out = json.loads(response.data.decode('utf8'))
        self.assertEquals(out, {})

    def test_validation_false_on_constructor_with_override(self):
        api = restplus.Api(self.app, validate=False)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOn(restplus.Resource):
            @api.expect(fields, validate=True)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assert_errors(response, 'name')

    def test_validation_true_on_constructor(self):
        api = restplus.Api(self.app, validate=True)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assert_errors(response, 'name')

    def test_validation_true_on_constructor_with_override(self):
        api = restplus.Api(self.app, validate=True)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOff(restplus.Resource):
            @api.expect(fields, validate=False)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assert_errors(response, 'name')

    def _setup_api_format_checker_tests(self, format_checker=None):
        class IPAddress(restplus.fields.Raw):
            __schema_type__ = 'string'
            __schema_format__ = 'ipv4'

        api = restplus.Api(self.app, format_checker=format_checker)
        model = api.model('MyModel', {'ip': IPAddress(required=True)})

        @api.route('/format_checker/')
        class TestResource(restplus.Resource):
            @api.expect(model, validate=True)
            def post(self):
                return {}

    def test_format_checker_none_on_constructor(self):
        self._setup_api_format_checker_tests()

        data = {'ip': '192.168.1'}
        response = self.post('/format_checker/', data)
        self.assertEquals(response.status_code, 200)
        out = json.loads(response.data.decode('utf8'))
        self.assertEquals(out, {})

    def test_format_checker_object_on_constructor(self):
        from jsonschema import FormatChecker
        self._setup_api_format_checker_tests(format_checker=FormatChecker())

        data = {'ip': '192.168.1'}
        response = self.post('/format_checker/', data)
        self.assertEquals(response.status_code, 400)
        out = json.loads(response.data.decode('utf8'))
        self.assertIn('ipv4', out['errors']['ip'])

    def test_validation_false_in_config(self):
        with self.settings(RESTPLUS_VALIDATE=False):
            api = restplus.Api(self.app)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assertEquals(response.status_code, 200)
        out = json.loads(response.data.decode('utf8'))
        self.assertEquals(out, {})

    def test_validation_in_config(self):
        with self.settings(RESTPLUS_VALIDATE=True):
            api = restplus.Api(self.app)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOn(restplus.Resource):
            @api.expect(fields)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assert_errors(response, 'name')

    def test_api_payload(self):
        api = restplus.Api(self.app, validate=True)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class Payload(restplus.Resource):
            payload = None

            @api.expect(fields)
            def post(self):
                Payload.payload = api.payload
                return {}

        data = {
            'name': 'John Doe',
            'age': 15,
        }

        response = self.post('/validation/', data)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(Payload.payload, data)

    def test_validation_with_inheritance(self):
        '''It should perform validation with inheritance (allOf/$ref)'''
        api = restplus.Api(self.app, validate=True)

        fields = api.model('Parent', {
            'name': restplus.fields.String(required=True),
        })

        child_fields = api.inherit('Child', fields, {
            'age': restplus.fields.Integer,
        })

        @api.route('/validation/')
        class Inheritance(restplus.Resource):
            @api.expect(child_fields)
            def post(self):
                return {}

        response = self.post('/validation/', {
            'name': 'John Doe',
            'age': 15,
        })
        self.assertEquals(response.status_code, 200)

        response = self.post('/validation/', {
            'age': '15',
        })
        self.assert_errors(response, 'name', 'age')

    def test_validation_on_list(self):
        '''It should perform validation on lists'''
        api = restplus.Api(self.app, validate=True)

        person = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer(required=True),
        })

        family = api.model('Family', {
            'name': restplus.fields.String(required=True),
            'members': restplus.fields.List(restplus.fields.Nested(person))
        })

        @api.route('/validation/')
        class List(restplus.Resource):
            @api.expect(family)
            def post(self):
                return {}

        response = self.post('/validation/', {
            'name': 'Doe',
            'members': [{'name': 'Jonn'}, {'age': 42}]
        })

        self.assert_errors(response, 'members.0.age', 'members.1.name')

    def _setup_expect_validation_single_resource_tests(self):
        # Setup a minimal Api with endpoint that expects in input payload
        # a single object of a resource
        api = restplus.Api(self.app, validate=True)

        user = api.model('User', {
            'username': restplus.fields.String()
        })

        @api.route('/validation/')
        class Users(restplus.Resource):
            @api.expect(user)
            def post(self):
                return {}

    def _setup_expect_validation_collection_resource_tests(self):
        # Setup a minimal Api with endpoint that expects in input payload
        # one or more objects of a resource
        api = restplus.Api(self.app, validate=True)

        user = api.model('User', {
            'username': restplus.fields.String()
        })

        @api.route('/validation/')
        class Users(restplus.Resource):
            @api.expect([user])
            def post(self):
                return {}

    def test_expect_validation_single_resource_success(self):
        self._setup_expect_validation_single_resource_tests()

        # Input payload is a valid JSON object
        response = self.post('/validation/', {
            'username': 'alice'
        })
        self.assertEqual(200, response.status_code)
        out = json.loads(response.data.decode('utf8'))
        self.assertEqual({}, out)

    def test_expect_validation_single_resource_error(self):
        self._setup_expect_validation_single_resource_tests()

        # Input payload is an invalid JSON object
        response = self.post('/validation/', {
            'username': 123
        })
        self.assert_errors(response, 'username')

        # Input payload is a JSON array (expected JSON object)
        response = self.post('/validation/', [{
            'username': 123
        }])
        self.assert_errors(response, '')

    def test_expect_validation_collection_resource_success(self):
        self._setup_expect_validation_collection_resource_tests()

        # Input payload is a valid JSON object
        response = self.post('/validation/', {
            'username': 'alice'
        })
        self.assertEqual(200, response.status_code)
        out = json.loads(response.data.decode('utf8'))
        self.assertEqual({}, out)

        # Input payload is a JSON array with valid JSON objects
        response = self.post('/validation/', [
            {'username': 'alice'},
            {'username': 'bob'}
        ])
        self.assertEqual(200, response.status_code)
        out = json.loads(response.data.decode('utf8'))
        self.assertEqual({}, out)

    def test_expect_validation_collection_resource_error(self):
        self._setup_expect_validation_collection_resource_tests()

        # Input payload is an invalid JSON object
        response = self.post('/validation/', {
            'username': 123
        })
        self.assert_errors(response, 'username')

        # Input payload is a JSON array but with an invalid JSON object
        response = self.post('/validation/', [
            {'username': 'alice'},
            {'username': 123}
        ])
        self.assert_errors(response, 'username')

    def test_validation_with_propagate(self):
        self.app.config['PROPAGATE_EXCEPTIONS'] = True
        api = restplus.Api(self.app, validate=True)

        fields = api.model('Person', {
            'name': restplus.fields.String(required=True),
            'age': restplus.fields.Integer,
            'birthdate': restplus.fields.DateTime,
        })

        @api.route('/validation/')
        class ValidationOff(restplus.Resource):
            @api.expect(fields)
            def post(self):
                return {}

        data = {}

        response = self.post('/validation/', data)

        self.assert_errors(response, 'name')

    def test_empty_payload(self):
        api = restplus.Api(self.app, validate=True)

        @api.route('/empty/')
        class Payload(restplus.Resource):
            def post(self):

                return {}

        with self.app.test_client() as client:
            response = client.post('/empty/', data='',
                                  headers={'content-type': 'application/json'})

            self.assertEquals(response.status_code, 200)
