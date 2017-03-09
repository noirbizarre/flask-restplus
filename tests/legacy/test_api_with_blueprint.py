# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import flask

from flask import Blueprint, request

import flask_restplus as restplus


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(restplus.Resource):
    def get(self):
        return {}


class GoodbyeWorld(restplus.Resource):
    def __init__(self, err):
        self.err = err

    def get(self):
        flask.abort(self.err)


class APIWithBlueprintTest(object):
    def test_api_base(self, app):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        app.register_blueprint(blueprint)
        assert api.urls == {}
        assert api.prefix == ''
        assert api.default_mediatype == 'application/json'

    def test_api_delayed_initialization(self, app):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api()
        api.init_app(blueprint)
        app.register_blueprint(blueprint)
        api.add_resource(HelloWorld, '/', endpoint="hello")

    def test_add_resource_endpoint(self, app, mocker):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        view = mocker.Mock(**{'as_view.return_value.__name__': str('test_view')})
        api.add_resource(view, '/foo', endpoint='bar')
        app.register_blueprint(blueprint)
        view.as_view.assert_called_with('bar', api)

    def test_add_resource_endpoint_after_registration(self, app, mocker):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        app.register_blueprint(blueprint)
        view = mocker.Mock(**{'as_view.return_value.__name__': str('test_view')})
        api.add_resource(view, '/foo', endpoint='bar')
        view.as_view.assert_called_with('bar', api)

    def test_url_with_api_prefix(self, app):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint, prefix='/api')
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        app.register_blueprint(blueprint)
        with app.test_request_context('/api/hi'):
            assert request.endpoint == 'test.hello'

    def test_url_with_blueprint_prefix(self, app):
        blueprint = Blueprint('test', __name__, url_prefix='/bp')
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        app.register_blueprint(blueprint)
        with app.test_request_context('/bp/hi'):
            assert request.endpoint == 'test.hello'

    def test_url_with_registration_prefix(self, app):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        app.register_blueprint(blueprint, url_prefix='/reg')
        with app.test_request_context('/reg/hi'):
            assert request.endpoint == 'test.hello'

    def test_registration_prefix_overrides_blueprint_prefix(self, app):
        blueprint = Blueprint('test', __name__, url_prefix='/bp')
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        app.register_blueprint(blueprint, url_prefix='/reg')
        with app.test_request_context('/reg/hi'):
            assert request.endpoint == 'test.hello'

    def test_url_with_api_and_blueprint_prefix(self, app):
        blueprint = Blueprint('test', __name__, url_prefix='/bp')
        api = restplus.Api(blueprint, prefix='/api')
        api.add_resource(HelloWorld, '/hi', endpoint='hello')
        app.register_blueprint(blueprint)
        with app.test_request_context('/bp/api/hi'):
            assert request.endpoint == 'test.hello'

    def test_error_routing(self, app, mocker):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint="hello")
        api.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        app.register_blueprint(blueprint)
        with app.test_request_context('/hi', method='POST'):
            assert api._should_use_fr_error_handler() is True
            assert api._has_fr_route() is True
        with app.test_request_context('/bye'):
            api._should_use_fr_error_handler = mocker.Mock(return_value=False)
            assert api._has_fr_route() is True

    def test_non_blueprint_rest_error_routing(self, app, mocker):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint="hello")
        api.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        app.register_blueprint(blueprint, url_prefix='/blueprint')
        api2 = restplus.Api(app)
        api2.add_resource(HelloWorld(api), '/hi', endpoint="hello")
        api2.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        with app.test_request_context('/hi', method='POST'):
            assert api._should_use_fr_error_handler() is False
            assert api2._should_use_fr_error_handler() is True
            assert api._has_fr_route() is False
            assert api2._has_fr_route() is True
        with app.test_request_context('/blueprint/hi', method='POST'):
            assert api._should_use_fr_error_handler() is True
            assert api2._should_use_fr_error_handler() is False
            assert api._has_fr_route() is True
            assert api2._has_fr_route() is False
        api._should_use_fr_error_handler = mocker.Mock(return_value=False)
        api2._should_use_fr_error_handler = mocker.Mock(return_value=False)
        with app.test_request_context('/bye'):
            assert api._has_fr_route() is False
            assert api2._has_fr_route() is True
        with app.test_request_context('/blueprint/bye'):
            assert api._has_fr_route() is True
            assert api2._has_fr_route() is False

    def test_non_blueprint_non_rest_error_routing(self, app, mocker):
        blueprint = Blueprint('test', __name__)
        api = restplus.Api(blueprint)
        api.add_resource(HelloWorld, '/hi', endpoint="hello")
        api.add_resource(GoodbyeWorld(404), '/bye', endpoint="bye")
        app.register_blueprint(blueprint, url_prefix='/blueprint')

        @app.route('/hi')
        def hi():
            return 'hi'

        @app.route('/bye')
        def bye():
            flask.abort(404)
        with app.test_request_context('/hi', method='POST'):
            assert api._should_use_fr_error_handler() is False
            assert api._has_fr_route() is False
        with app.test_request_context('/blueprint/hi', method='POST'):
            assert api._should_use_fr_error_handler() is True
            assert api._has_fr_route() is True
        api._should_use_fr_error_handler = mocker.Mock(return_value=False)
        with app.test_request_context('/bye'):
            assert api._has_fr_route() is False
        with app.test_request_context('/blueprint/bye'):
            assert api._has_fr_route() is True
