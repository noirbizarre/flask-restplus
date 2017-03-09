# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import flask
import pytest
import six

from collections import OrderedDict
from json import dumps, loads, JSONEncoder

from flask import Blueprint, redirect, views, abort as flask_abort
from flask.signals import got_request_exception
from werkzeug.exceptions import HTTPException, Unauthorized, BadRequest, NotFound
from werkzeug.http import quote_etag, unquote_etag

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

    def test_marshal(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal(marshal_dict, fields)
        assert output == {'foo': 'bar'}

    def test_marshal_with_envelope(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal(marshal_dict, fields, envelope='hey')
        assert output == {'hey': {'foo': 'bar'}}

    def test_marshal_decorator(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        assert try_me() == {'foo': 'bar'}

    def test_marshal_decorator_with_envelope(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields, envelope='hey')
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])

        assert try_me() == {'hey': {'foo': 'bar'}}

    def test_marshal_decorator_tuple(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, {'X-test': 123}
        assert try_me() == ({'foo': 'bar'}, 200, {'X-test': 123})

    def test_marshal_decorator_tuple_with_envelope(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields, envelope='hey')
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, {'X-test': 123}

        assert try_me() == ({'hey': {'foo': 'bar'}}, 200, {'X-test': 123})

    def test_marshal_field_decorator(self):
        field = restplus.fields.Raw

        @restplus.marshal_with_field(field)
        def try_me():
            return 'foo'
        assert try_me() == 'foo'

    def test_marshal_field_decorator_tuple(self):
        field = restplus.fields.Raw

        @restplus.marshal_with_field(field)
        def try_me():
            return 'foo', 200, {'X-test': 123}
        assert try_me() == ('foo', 200, {'X-test': 123})

    def test_marshal_field(self):
        fields = OrderedDict({'foo': restplus.fields.Raw()})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal(marshal_fields, fields)
        assert output == {'foo': 'bar'}

    def test_marshal_tuple(self):
        fields = OrderedDict({'foo': restplus.fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal((marshal_fields,), fields)
        assert output == [{'foo': 'bar'}]

    def test_marshal_tuple_with_envelope(self):
        fields = OrderedDict({'foo': restplus.fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal((marshal_fields,), fields, envelope='hey')
        assert output == {'hey': [{'foo': 'bar'}]}

    def test_marshal_nested(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.Nested({
                'fye': restplus.fields.String,
            }))
        ])

        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', {'fye': 'fum'})])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', OrderedDict([('fye', 'fum')]))])
        assert output == expected

    def test_marshal_nested_with_non_null(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.Nested(
                OrderedDict([
                    ('fye', restplus.fields.String),
                    ('blah', restplus.fields.String)
                ]), allow_null=False))
        ])
        marshal_fields = [OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', None)])]
        output = restplus.marshal(marshal_fields, fields)
        expected = [OrderedDict([('foo', 'bar'), ('fee', OrderedDict([('fye', None), ('blah', None)]))])]
        assert output == expected

    def test_marshal_nested_with_null(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.Nested(
                OrderedDict([
                    ('fye', restplus.fields.String),
                    ('blah', restplus.fields.String)
                ]), allow_null=True))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', None)])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', None)])
        assert output == expected

    def test_allow_null_presents_data(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.Nested(
                OrderedDict([
                    ('fye', restplus.fields.String),
                    ('blah', restplus.fields.String)
                ]), allow_null=True))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', {'blah': 'cool'})])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', OrderedDict([('fye', None), ('blah', 'cool')]))])
        assert output == expected

    def test_marshal_nested_property(self):
        class TestObject(object):
            @property
            def fee(self):
                return {'blah': 'cool'}
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.Nested(
                OrderedDict([
                    ('fye', restplus.fields.String),
                    ('blah', restplus.fields.String)
                ]), allow_null=True))
        ])
        obj = TestObject()
        obj.foo = 'bar'
        obj.bat = 'baz'
        output = restplus.marshal([obj], fields)
        expected = [OrderedDict([('foo', 'bar'), ('fee', OrderedDict([('fye', None), ('blah', 'cool')]))])]
        assert output == expected

    def test_marshal_list(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.List(restplus.fields.String))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', ['fye', 'fum'])])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', (['fye', 'fum']))])
        assert output == expected

    def test_marshal_list_of_nesteds(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.List(restplus.fields.Nested({
                'fye': restplus.fields.String
            })))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', {'fye': 'fum'})])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', [OrderedDict([('fye', 'fum')])])])
        assert output == expected

    def test_marshal_list_of_lists(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.List(restplus.fields.List(
                restplus.fields.String)))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', [['fye'], ['fum']])])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', [['fye'], ['fum']])])
        assert output == expected

    def test_marshal_nested_dict(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('bar', OrderedDict([
                ('a', restplus.fields.Raw),
                ('b', restplus.fields.Raw),
            ])),
        ])
        marshal_fields = OrderedDict([('foo', 'foo-val'), ('bar', 'bar-val'), ('bat', 'bat-val'),
                                      ('a', 1), ('b', 2), ('c', 3)])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'foo-val'), ('bar', OrderedDict([('a', 1), ('b', 2)]))])
        assert output == expected

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

    def test_handle_server_error(self, api):
        resp = api.handle_error(Exception())
        assert resp.status_code == 500
        assert resp.data.decode() == dumps({
            "message": "Internal Server Error"
        }) + "\n"

    def test_handle_error_with_code(self, app):
        api = restplus.Api(app, serve_challenge_on_401=True)

        exception = Exception()
        exception.code = "Not an integer"
        exception.data = {'foo': 'bar'}

        resp = api.handle_error(exception)
        assert resp.status_code == 500
        assert resp.data.decode() == dumps({"foo": "bar"}) + "\n"

    @pytest.mark.api(serve_challenge_on_401=True)
    def test_handle_auth(self, api):
        resp = api.handle_error(Unauthorized())
        assert resp.status_code == 401
        expected_data = dumps({'message': Unauthorized.description}) + "\n"
        assert resp.data.decode() == expected_data

        assert 'WWW-Authenticate' in resp.headers

    def test_handle_api_error(self, api, client):
        class Test(restplus.Resource):
            def get(self):
                flask.abort(404)

        api.add_resource(Test(), '/api', endpoint='api')
        # app = app.test_client()

        resp = client.get("/api")
        assert resp.status_code == 404
        assert 'application/json' == resp.headers['Content-Type']
        data = loads(resp.data.decode())
        assert 'message' in data

    def test_handle_non_api_error(self, api, client):
        resp = client.get("/foo")
        assert resp.status_code == 404
        assert 'text/html' == resp.headers['Content-Type']

    def test_non_api_error_404_catchall(self, app, client):
        api = restplus.Api(app, catch_all_404s=True)
        # app = app.test_client()

        resp = client.get("/foo")
        assert api.default_mediatype == resp.headers['Content-Type']

    def test_handle_error_signal(self, app):
        api = restplus.Api(app)

        exception = BadRequest()

        recorded = []

        def record(sender, exception):
            recorded.append(exception)

        got_request_exception.connect(record, app)
        try:
            with app.test_request_context("/foo"):
                api.handle_error(exception)
                assert len(recorded) == 1
                assert exception is recorded[0]
        finally:
            got_request_exception.disconnect(record, app)

    def test_handle_error(self, api):
        resp = api.handle_error(BadRequest())
        assert resp.status_code == 400
        assert resp.data.decode() == dumps({
            'message': BadRequest.description,
        }) + "\n"

    def test_handle_smart_errors(self, app):
        api = restplus.Api(app)
        view = restplus.Resource

        api.add_resource(view, '/foo', endpoint='bor')
        api.add_resource(view, '/fee', endpoint='bir')
        api.add_resource(view, '/fii', endpoint='ber')

        with app.test_request_context("/faaaaa"):
            resp = api.handle_error(NotFound())
            assert resp.status_code == 404
            assert resp.data.decode() == dumps({
                "message": NotFound.description,
            }) + "\n"

        with app.test_request_context("/fOo"):
            resp = api.handle_error(NotFound())
            assert resp.status_code == 404
            assert 'did you mean /foo ?' in resp.data.decode()

        app.config['ERROR_404_HELP'] = False

        with app.test_request_context("/fOo"):
            resp = api.handle_error(NotFound())
            assert resp.status_code == 404
            assert resp.data.decode() == dumps({
                "message": NotFound.description
            }) + "\n"

    def test_error_router_falls_back_to_original(self, app, mocker):
        """Verify that if an exception occurs in the Flask-RESTPlus error handler,
        the error_router will call the original flask error handler instead.
        """
        api = restplus.Api(app)
        app.handle_exception = mocker.Mock()
        api.handle_error = mocker.Mock(side_effect=Exception())
        api._has_fr_route = mocker.Mock(return_value=True)
        exception = mocker.Mock(spec=HTTPException)

        with app.test_request_context('/foo'):
            api.error_router(exception, app.handle_exception)

        assert app.handle_exception.called_with(exception is True)

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

    def test_abort_data(self):
        with pytest.raises(Exception) as cm:
            restplus.abort(404, foo='bar')
        assert cm.value.data == {'foo': 'bar'}

    def test_abort_no_data(self):
        with pytest.raises(Exception) as cm:
            restplus.abort(404)
        assert not hasattr(cm.value, 'data')

    def test_abort_custom_message(self):
        with pytest.raises(Exception) as cm:
            restplus.abort(404, message="no user")
        assert cm.value.data['message'] == "no user"

    def test_abort_type(self):
        with pytest.raises(HTTPException):
            restplus.abort(404)

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

    def test_fr_405(self, app, client):
        api = restplus.Api(app)
        api.add_resource(HelloWorld, '/ids/<int:id>', endpoint="hello")
        resp = client.post('/ids/3')
        assert resp.status_code == 405
        assert resp.content_type == api.default_mediatype
        # Allow can be of the form 'GET, PUT, POST'
        allow = ', '.join(set(resp.headers.get_all('Allow')))
        allow = set(method.strip() for method in allow.split(','))
        assert allow == set(['HEAD', 'OPTIONS'] + HelloWorld.methods)

    @pytest.mark.options(debug=True)
    def test_exception_header_forwarded(self, api, client):
        """Test that HTTPException's headers are extended properly"""
        class NotModified(HTTPException):
            code = 304

            def __init__(self, etag, *args, **kwargs):
                super(NotModified, self).__init__(*args, **kwargs)
                self.etag = quote_etag(etag)

            def get_headers(self, *args, **kwargs):
                """Get a list of headers."""
                return [('ETag', self.etag)]

        class Foo1(restplus.Resource):
            def get(self):
                flask_abort(304, etag='myETag')

        api.add_resource(Foo1, '/foo')
        flask_abort.mapping.update({304: NotModified})

        foo = client.get('/foo')
        assert foo.get_etag() == unquote_etag(quote_etag('myETag'))

    def test_exception_header_forwarding_doesnt_duplicate_headers(self, api):
        """Test that HTTPException's headers do not add a duplicate
        Content-Length header

        https://github.com/flask-restful/flask-restful/issues/534
        """
        r = api.handle_error(BadRequest())
        assert len(r.headers.getlist('Content-Length')) == 1

    @pytest.mark.options(debug=True)
    def test_will_prettyprint_json_in_debug_mode(self, api, client):
        class Foo1(restplus.Resource):
            def get(self):
                return {'foo': 'bar', 'baz': 'asdf'}

        api.add_resource(Foo1, '/foo', endpoint='bar')

        foo = client.get('/foo')

        # Python's dictionaries have random order (as of "new" Pythons,
        # anyway), so we can't verify the actual output here.  We just
        # assert that they're properly prettyprinted.
        lines = foo.data.splitlines()
        lines = [line.decode() for line in lines]
        assert "{" == lines[0]
        assert lines[1].startswith('    ')
        assert lines[2].startswith('    ')
        assert "}" == lines[3]

        # Assert our trailing newline.
        assert foo.data.endswith(b'\n')

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

    def test_json_float_marshalled(self, api, client):
        class FooResource(restplus.Resource):
            fields = {'foo': restplus.fields.Float}

            def get(self):
                return restplus.marshal({"foo": 3.0}, self.fields)

        api.add_resource(FooResource, '/api')

        resp = client.get('/api')
        assert resp.status_code == 200
        assert resp.data.decode('utf-8') == '{"foo": 3.0}\n'

    def test_calling_owns_endpoint_before_api_init(self):
        api = restplus.Api()
        api.owns_endpoint('endpoint')
        # with pytest.raises(AttributeError):
        # try:
        # except AttributeError as ae:
        #     self.fail(ae.message)
