# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import flask
import six

from flask import Blueprint, request

import flask_restplus as restplus

from nose.tools import assert_true, assert_false  # you need it for tests in form of continuations

from .. import TestCase, Mock


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(restplus.Resource):
    def get(self):
        return {}


class GoodbyeWorld(restplus.Resource):
    def __init__(self, err):
        self.err = err

    def get(self):
        flask.abort(self.err)


class APIWithBlueprintTestCase(TestCase):

    def test_api_base(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        self.app.register_blueprint(blueprint)
        self.assertEquals(api.urls, {})
        self.assertEquals(api.prefix, '')
        self.assertEquals(api.default_mediatype, 'application/json')

    def test_api_delayed_initialization(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api()
        api.init_app(blueprint)
        self.app.register_blueprint(blueprint)
        api.add_resource(HelloWorld, '/', endpoint="hello")

    def test_add_resource_endpoint(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        view = Mock(**{'as_view.return_value.__name__': str('test_view')})
        api.add_resource(view, '/foo', endpoint='bar')
        self.app.register_blueprint(blueprint)
        view.as_view.assert_called_with('bar', api)

    def test_add_resource_endpoint_after_registration(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        self.app.register_blueprint(blueprint)
        view = Mock(**{'as_view.return_value.__name__': str('test_view')})
        api.add_resource(view, '/foo', endpoint='bar')
        view.as_view.assert_called_with('bar', api)

    def test_url_with_api_prefix(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint, prefix='/api')
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        self.app.register_blueprint(blueprint)
        with self.app.test_request_context('/api/hi'):
            self.assertEquals(request.endpoint, 'test.hello')

    def test_url_with_blueprint_prefix(self):
        blueprint = Blueprint('test', __name__, url_prefix='/bp')
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        self.app.register_blueprint(blueprint)
        with self.app.test_request_context('/bp/hi'):
            self.assertEquals(request.endpoint, 'test.hello')

    def test_url_with_registration_prefix(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        self.app.register_blueprint(blueprint, url_prefix='/reg')
        with self.app.test_request_context('/reg/hi'):
            self.assertEquals(request.endpoint, 'test.hello')

    def test_registration_prefix_overrides_blueprint_prefix(self):
        blueprint = Blueprint('test', __name__, url_prefix='/bp')
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        self.app.register_blueprint(blueprint, url_prefix='/reg')
        with self.app.test_request_context('/reg/hi'):
            self.assertEquals(request.endpoint, 'test.hello')

    def test_url_with_api_and_blueprint_prefix(self):
        blueprint = Blueprint('test', __name__, url_prefix='/bp')
        api = restplus.Api(blueprint, prefix='/api')
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        self.app.register_blueprint(blueprint)
        with self.app.test_request_context('/bp/api/hi'):
            self.assertEquals(request.endpoint, 'test.hello')

    def test_error_routing(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint="hello")
        api.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        self.app.register_blueprint(blueprint)
        with self.app.test_request_context('/hi', method='POST'):
            assert_true(api._should_use_fr_error_handler())
            assert_true(api._has_fr_route())
        with self.app.test_request_context('/bye'):
            api._should_use_fr_error_handler = Mock(return_value=False)
            assert_true(api._has_fr_route())

    def test_non_blueprint_rest_error_routing(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint="hello")
        api.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        self.app.register_blueprint(blueprint, url_prefix='/blueprint')
        api2 = restplus.Api(self.app)
        api2.add_resource(HelloWorld(api), '/hi', endpoint="hello")
        api2.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        with self.app.test_request_context('/hi', method='POST'):
            assert_false(api._should_use_fr_error_handler())
            assert_true(api2._should_use_fr_error_handler())
            assert_false(api._has_fr_route())
            assert_true(api2._has_fr_route())
        with self.app.test_request_context('/blueprint/hi', method='POST'):
            assert_true(api._should_use_fr_error_handler())
            assert_false(api2._should_use_fr_error_handler())
            assert_true(api._has_fr_route())
            assert_false(api2._has_fr_route())
        api._should_use_fr_error_handler = Mock(return_value=False)
        api2._should_use_fr_error_handler = Mock(return_value=False)
        with self.app.test_request_context('/bye'):
            assert_false(api._has_fr_route())
            assert_true(api2._has_fr_route())
        with self.app.test_request_context('/blueprint/bye'):
            assert_true(api._has_fr_route())
            assert_false(api2._has_fr_route())

    def test_non_blueprint_non_rest_error_routing(self):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint="hello")
        api.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        self.app.register_blueprint(blueprint, url_prefix='/blueprint')

        @self.app.route('/hi')
        def hi():
            return 'hi'

        @self.app.route('/bye')
        def bye():
            flask.abort(404)
        with self.app.test_request_context('/hi', method='POST'):
            assert_false(api._should_use_fr_error_handler())
            assert_false(api._has_fr_route())
        with self.app.test_request_context('/blueprint/hi', method='POST'):
            assert_true(api._should_use_fr_error_handler())
            assert_true(api._has_fr_route())
        api._should_use_fr_error_handler = Mock(return_value=False)
        with self.app.test_request_context('/bye'):
            assert_false(api._has_fr_route())
        with self.app.test_request_context('/blueprint/bye'):
            assert_true(api._has_fr_route())
