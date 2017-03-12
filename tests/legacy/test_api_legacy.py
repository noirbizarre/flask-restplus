# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import flask
import pytest
import six

from json import dumps, JSONEncoder

from flask import Blueprint, redirect, views
from werkzeug.exceptions import HTTPException, Unauthorized, BadRequest

import flask_restplus as restplus


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(restplus.Resource):
    def get(self):
        return {}


class APITest(object):
    def test_unauthorized_no_challenge_by_default(self, api, mocker):
        response = mocker.Mock()
        response.headers = {}
        response = api.unauthorized(response)
        assert 'WWW-Authenticate' not in response.headers

    @pytest.mark.api(serve_challenge_on_401=True)
    def test_unauthorized(self, api, mocker):
        response = mocker.Mock()
        response.headers = {}
        response = api.unauthorized(response)
        assert response.headers['WWW-Authenticate'] == 'Basic realm="flask-restplus"'

    @pytest.mark.options(HTTP_BASIC_AUTH_REALM='Foo')
    @pytest.mark.api(serve_challenge_on_401=True)
    def test_unauthorized_custom_realm(self, api, mocker):
        response = mocker.Mock()
        response.headers = {}
        response = api.unauthorized(response)
        assert response.headers['WWW-Authenticate'] == 'Basic realm="Foo"'

    def test_handle_error_401_no_challenge_by_default(self, api):
        resp = api.handle_error(Unauthorized())
        assert resp.status_code == 401
        assert 'WWW-Autheneticate' not in resp.headers

    @pytest.mark.api(serve_challenge_on_401=True)
    def test_handle_error_401_sends_challege_default_realm(self, api):
        exception = HTTPException()
        exception.code = 401
        exception.data = {'foo': 'bar'}

        resp = api.handle_error(exception)
        assert resp.status_code == 401
        assert resp.headers['WWW-Authenticate'] == 'Basic realm="flask-restplus"'

    @pytest.mark.api(serve_challenge_on_401=True)
    @pytest.mark.options(HTTP_BASIC_AUTH_REALM='test-realm')
    def test_handle_error_401_sends_challege_configured_realm(self, api):
        resp = api.handle_error(Unauthorized())
        assert resp.status_code == 401
        assert resp.headers['WWW-Authenticate'] == 'Basic realm="test-realm"'

    def test_handle_error_does_not_swallow_exceptions(self, api):
        exception = BadRequest('x')

        resp = api.handle_error(exception)
        assert resp.status_code == 400
        assert resp.get_data() == b'{"message": "x"}\n'

    def test_api_representation(self, api):
        @api.representation('foo')
        def foo():
            pass

        assert api.representations['foo'] == foo

    def test_api_base(self, app):
        api = restplus.Api(app)
        assert api.urls == {}
        assert api.prefix == ''
        assert api.default_mediatype == 'application/json'

    def test_api_delayed_initialization(self, app, client):
        api = restplus.Api()
        api.add_resource(HelloWorld, '/', endpoint="hello")
        api.init_app(app)
        assert client.get('/').status_code == 200

    def test_api_prefix(self, app):
        api = restplus.Api(app, prefix='/foo')
        assert api.prefix == '/foo'

    @pytest.mark.api(serve_challenge_on_401=True)
    def test_handle_auth(self, api):
        resp = api.handle_error(Unauthorized())
        assert resp.status_code == 401
        expected_data = dumps({'message': Unauthorized.description}) + "\n"
        assert resp.data.decode() == expected_data

        assert 'WWW-Authenticate' in resp.headers

    def test_media_types(self, app):
        api = restplus.Api(app)

        with app.test_request_context("/foo", headers={
            'Accept': 'application/json'
        }):
            assert api.mediatypes() == ['application/json']

    def test_media_types_method(self, app, mocker):
        api = restplus.Api(app)

        with app.test_request_context("/foo", headers={
            'Accept': 'application/xml; q=.5'
        }):
            assert api.mediatypes_method()(mocker.Mock()) == ['application/xml', 'application/json']

    def test_media_types_q(self, app):
        api = restplus.Api(app)

        with app.test_request_context("/foo", headers={
            'Accept': 'application/json; q=1, application/xml; q=.5'
        }):
            assert api.mediatypes() == ['application/json', 'application/xml']

    def test_decorator(self, mocker):
        def return_zero(func):
            return 0

        app = mocker.Mock(flask.Flask)
        app.view_functions = {}
        app.extensions = {}
        app.config = {}
        view = mocker.Mock()
        api = restplus.Api(app)
        api.decorators.append(return_zero)
        api.output = mocker.Mock()
        api.add_resource(view, '/foo', endpoint='bar')

        app.add_url_rule.assert_called_with('/foo', view_func=0)

    def test_add_resource_endpoint(self, app, mocker):
        view = mocker.Mock(**{'as_view.return_value.__name__': str('test_view')})

        api = restplus.Api(app)
        api.add_resource(view, '/foo', endpoint='bar')

        view.as_view.assert_called_with('bar', api)

    def test_add_two_conflicting_resources_on_same_endpoint(self, app):
        api = restplus.Api(app)

        class Foo1(restplus.Resource):
            def get(self):
                return 'foo1'

        class Foo2(restplus.Resource):
            def get(self):
                return 'foo2'

        api.add_resource(Foo1, '/foo', endpoint='bar')
        with pytest.raises(ValueError):
            api.add_resource(Foo2, '/foo/toto', endpoint='bar')

    def test_add_the_same_resource_on_same_endpoint(self, app):
        api = restplus.Api(app)

        class Foo1(restplus.Resource):
            def get(self):
                return 'foo1'

        api.add_resource(Foo1, '/foo', endpoint='bar')
        api.add_resource(Foo1, '/foo/toto', endpoint='blah')

        with app.test_client() as client:
            foo1 = client.get('/foo')
            assert foo1.data == b'"foo1"\n'
            foo2 = client.get('/foo/toto')
            assert foo2.data == b'"foo1"\n'

    def test_add_resource(self, mocker):
        app = mocker.Mock(flask.Flask)
        app.view_functions = {}
        app.extensions = {}
        app.config = {}
        api = restplus.Api(app)
        api.output = mocker.Mock()
        api.add_resource(views.MethodView, '/foo')

        app.add_url_rule.assert_called_with('/foo',
                                            view_func=api.output())

    def test_add_resource_kwargs(self, mocker):
        app = mocker.Mock(flask.Flask)
        app.view_functions = {}
        app.extensions = {}
        app.config = {}
        api = restplus.Api(app)
        api.output = mocker.Mock()
        api.add_resource(views.MethodView, '/foo', defaults={"bar": "baz"})

        app.add_url_rule.assert_called_with('/foo',
                                            view_func=api.output(),
                                            defaults={"bar": "baz"})

    def test_add_resource_forward_resource_class_parameters(self, app, client):
        api = restplus.Api(app)

        class Foo(restplus.Resource):
            def __init__(self, api, *args, **kwargs):
                self.one = args[0]
                self.two = kwargs['secret_state']
                super(Foo, self).__init__(api, *args, **kwargs)

            def get(self):
                return "{0} {1}".format(self.one, self.two)

        api.add_resource(Foo, '/foo',
                resource_class_args=('wonderful',),
                resource_class_kwargs={'secret_state': 'slurm'})

        foo = client.get('/foo')
        assert foo.data == b'"wonderful slurm"\n'

    def test_output_unpack(self, app):

        def make_empty_response():
            return {'foo': 'bar'}

        api = restplus.Api(app)

        with app.test_request_context("/foo"):
            wrapper = api.output(make_empty_response)
            resp = wrapper()
            assert resp.status_code == 200
            assert resp.data.decode() == '{"foo": "bar"}\n'

    def test_output_func(self, app):

        def make_empty_resposne():
            return flask.make_response('')

        api = restplus.Api(app)

        with app.test_request_context("/foo"):
            wrapper = api.output(make_empty_resposne)
            resp = wrapper()
            assert resp.status_code == 200
            assert resp.data.decode() == ''

    def test_resource(self, app, mocker):
        resource = restplus.Resource()
        resource.get = mocker.Mock()
        with app.test_request_context("/foo"):
            resource.dispatch_request()

    def test_resource_resp(self, app, mocker):
        resource = restplus.Resource()
        resource.get = mocker.Mock()
        with app.test_request_context("/foo"):
            resource.get.return_value = flask.make_response('')
            resource.dispatch_request()

    def test_resource_text_plain(self, app):
        def text(data, code, headers=None):
            return flask.make_response(six.text_type(data))

        class Foo(restplus.Resource):
            representations = {
                'text/plain': text,
            }

            def get(self):
                return 'hello'

        with app.test_request_context("/foo", headers={'Accept': 'text/plain'}):
            resource = Foo(None)
            resp = resource.dispatch_request()
            assert resp.data.decode() == 'hello'

    @pytest.mark.request_context('/foo')
    def test_resource_error(self, app):
        resource = restplus.Resource()
        with pytest.raises(AssertionError):
            resource.dispatch_request()

    @pytest.mark.request_context('/foo', method='HEAD')
    def test_resource_head(self, app):
        resource = restplus.Resource()
        with pytest.raises(AssertionError):
            resource.dispatch_request()

    def test_endpoints(self, app):
        api = restplus.Api(app)
        api.add_resource(HelloWorld, '/ids/<int:id>', endpoint="hello")
        with app.test_request_context('/foo'):
            assert api._has_fr_route() is False

        with app.test_request_context('/ids/3'):
            assert api._has_fr_route() is True

    def test_url_for(self, app):
        api = restplus.Api(app)
        api.add_resource(HelloWorld, '/ids/<int:id>')
        with app.test_request_context('/foo'):
            assert api.url_for(HelloWorld, id=123) == '/ids/123'

    def test_url_for_with_blueprint(self, app):
        """Verify that url_for works when an Api object is mounted on a
        Blueprint.
        """
        api_bp = Blueprint('api', __name__)
        api = restplus.Api(api_bp)
        api.add_resource(HelloWorld, '/foo/<string:bar>')
        app.register_blueprint(api_bp)
        with app.test_request_context('/foo'):
            assert api.url_for(HelloWorld, bar='baz') == '/foo/baz'

    def test_exception_header_forwarding_doesnt_duplicate_headers(self, api):
        """Test that HTTPException's headers do not add a duplicate
        Content-Length header

        https://github.com/flask-restful/flask-restful/issues/534
        """
        r = api.handle_error(BadRequest())
        assert len(r.headers.getlist('Content-Length')) == 1

    def test_read_json_settings_from_config(self, app, client):
        class TestConfig(object):
            RESTPLUS_JSON = {'indent': 2,
                             'sort_keys': True,
                             'separators': (', ', ': ')}

        app.config.from_object(TestConfig)
        api = restplus.Api(app)

        class Foo(restplus.Resource):
            def get(self):
                return {'foo': 'bar', 'baz': 'qux'}

        api.add_resource(Foo, '/foo')

        data = client.get('/foo').data

        expected = b'{\n  "baz": "qux", \n  "foo": "bar"\n}\n'

        assert data == expected

    def test_use_custom_jsonencoder(self, app, client):
        class CabageEncoder(JSONEncoder):
            def default(self, obj):
                return 'cabbage'

        class TestConfig(object):
            RESTPLUS_JSON = {'cls': CabageEncoder}

        app.config.from_object(TestConfig)
        api = restplus.Api(app)

        class Cabbage(restplus.Resource):
            def get(self):
                return {'frob': object()}

        api.add_resource(Cabbage, '/cabbage')

        data = client.get('/cabbage').data

        expected = b'{"frob": "cabbage"}\n'
        assert data == expected

    def test_json_with_no_settings(self, api, client):
        class Foo(restplus.Resource):
            def get(self):
                return {'foo': 'bar'}

        api.add_resource(Foo, '/foo')

        data = client.get('/foo').data

        expected = b'{"foo": "bar"}\n'
        assert data == expected

    def test_redirect(self, api, client):
        class FooResource(restplus.Resource):
            def get(self):
                return redirect('/')

        api.add_resource(FooResource, '/api')

        resp = client.get('/api')
        assert resp.status_code == 302
        assert resp.headers['Location'] == 'http://localhost/'

    def test_calling_owns_endpoint_before_api_init(self):
        api = restplus.Api()
        api.owns_endpoint('endpoint')
        # with pytest.raises(AttributeError):
        # try:
        # except AttributeError as ae:
        #     self.fail(ae.message)
