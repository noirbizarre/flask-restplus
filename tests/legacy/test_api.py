# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint, redirect, views, abort as flask_abort
from flask.signals import got_request_exception, signals_available
import flask
from werkzeug.exceptions import HTTPException, Unauthorized, BadRequest, NotFound
from werkzeug.http import quote_etag, unquote_etag

import flask_restplus as restplus
from flask_restplus._compat import OrderedDict
from json import dumps, loads, JSONEncoder

from nose.tools import assert_equals, assert_true, assert_false  # you need it for tests in form of continuations
import six

from .. import TestCase, Mock


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(restplus.Resource):
    def get(self):
        return {}


class APITestCase(TestCase):
    def test_unauthorized_no_challenge_by_default(self):
        api = restplus.Api(self.app)
        response = Mock()
        response.headers = {}
        with self.app.test_request_context('/foo'):
            response = api.unauthorized(response)
        assert_false('WWW-Authenticate' in response.headers)

    def test_unauthorized(self):
        api = restplus.Api(self.app, serve_challenge_on_401=True)
        response = Mock()
        response.headers = {}
        with self.app.test_request_context('/foo'):
            response = api.unauthorized(response)
        self.assertEqual(response.headers['WWW-Authenticate'],
                         'Basic realm="flask-restplus"')

    def test_unauthorized_custom_realm(self):
        self.app.config['HTTP_BASIC_AUTH_REALM'] = 'Foo'
        api = restplus.Api(self.app, serve_challenge_on_401=True)
        response = Mock()
        response.headers = {}
        with self.app.test_request_context('/foo'):
            response = api.unauthorized(response)
        self.assertEqual(response.headers['WWW-Authenticate'], 'Basic realm="Foo"')

    def test_handle_error_401_no_challenge_by_default(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context('/foo'):
            resp = api.handle_error(Unauthorized())
            self.assertEqual(resp.status_code, 401)
            assert_false('WWW-Autheneticate' in resp.headers)

    def test_handle_error_401_sends_challege_default_realm(self):
        api = restplus.Api(self.app, serve_challenge_on_401=True)
        exception = HTTPException()
        exception.code = 401
        exception.data = {'foo': 'bar'}

        with self.app.test_request_context('/foo'):
            resp = api.handle_error(exception)
            self.assertEqual(resp.status_code, 401)
            self.assertEqual(resp.headers['WWW-Authenticate'],
                             'Basic realm="flask-restplus"')

    def test_handle_error_401_sends_challege_configured_realm(self):
        self.app.config['HTTP_BASIC_AUTH_REALM'] = 'test-realm'
        api = restplus.Api(self.app, serve_challenge_on_401=True)

        with self.app.test_request_context('/foo'):
            resp = api.handle_error(Unauthorized())
            self.assertEqual(resp.status_code, 401)
            self.assertEqual(resp.headers['WWW-Authenticate'],
                             'Basic realm="test-realm"')

    def test_handle_error_does_not_swallow_exceptions(self):
        api = restplus.Api(self.app)
        exception = BadRequest('x')

        with self.app.test_request_context('/foo'):
            resp = api.handle_error(exception)
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.get_data(), b'{"message": "x"}\n')

    def test_marshal(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal(marshal_dict, fields)
        self.assertEqual(output, {'foo': 'bar'})

    def test_marshal_with_envelope(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])
        marshal_dict = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal(marshal_dict, fields, envelope='hey')
        self.assertEqual(output, {'hey': {'foo': 'bar'}})

    def test_marshal_decorator(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        self.assertEqual(try_me(), {'foo': 'bar'})

    def test_marshal_decorator_with_envelope(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields, envelope='hey')
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')])

        self.assertEqual(try_me(), {'hey': {'foo': 'bar'}})

    def test_marshal_decorator_tuple(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields)
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, {'X-test': 123}
        self.assertEqual(try_me(), ({'foo': 'bar'}, 200, {'X-test': 123}))

    def test_marshal_decorator_tuple_with_envelope(self):
        fields = OrderedDict([('foo', restplus.fields.Raw)])

        @restplus.marshal_with(fields, envelope='hey')
        def try_me():
            return OrderedDict([('foo', 'bar'), ('bat', 'baz')]), 200, {'X-test': 123}

        self.assertEqual(try_me(), ({'hey': {'foo': 'bar'}}, 200, {'X-test': 123}))

    def test_marshal_field_decorator(self):
        field = restplus.fields.Raw

        @restplus.marshal_with_field(field)
        def try_me():
            return 'foo'
        self.assertEqual(try_me(), 'foo')

    def test_marshal_field_decorator_tuple(self):
        field = restplus.fields.Raw

        @restplus.marshal_with_field(field)
        def try_me():
            return 'foo', 200, {'X-test': 123}
        self.assertEqual(('foo', 200, {'X-test': 123}), try_me())

    def test_marshal_field(self):
        fields = OrderedDict({'foo': restplus.fields.Raw()})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal(marshal_fields, fields)
        self.assertEqual(output, {'foo': 'bar'})

    def test_marshal_tuple(self):
        fields = OrderedDict({'foo': restplus.fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal((marshal_fields,), fields)
        self.assertEqual(output, [{'foo': 'bar'}])

    def test_marshal_tuple_with_envelope(self):
        fields = OrderedDict({'foo': restplus.fields.Raw})
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz')])
        output = restplus.marshal((marshal_fields,), fields, envelope='hey')
        self.assertEqual(output, {'hey': [{'foo': 'bar'}]})

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
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

    def test_marshal_list(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.List(restplus.fields.String))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', ['fye', 'fum'])])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', (['fye', 'fum']))])
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

    def test_marshal_list_of_lists(self):
        fields = OrderedDict([
            ('foo', restplus.fields.Raw),
            ('fee', restplus.fields.List(restplus.fields.List(
                restplus.fields.String)))
        ])
        marshal_fields = OrderedDict([('foo', 'bar'), ('bat', 'baz'), ('fee', [['fye'], ['fum']])])
        output = restplus.marshal(marshal_fields, fields)
        expected = OrderedDict([('foo', 'bar'), ('fee', [['fye'], ['fum']])])
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

    def test_api_representation(self):
        api = restplus.Api(self.app)

        @api.representation('foo')
        def foo():
            pass

        self.assertEqual(api.representations['foo'], foo)

    def test_api_base(self):
        api = restplus.Api(self.app)
        self.assertEqual(api.urls, {})
        self.assertEqual(api.prefix, '')
        self.assertEqual(api.default_mediatype, 'application/json')

    def test_api_delayed_initialization(self):
        api = restplus.Api()
        api.add_resource(HelloWorld, '/', endpoint="hello")
        api.init_app(self.app)
        with self.app.test_client() as client:
            self.assertEqual(client.get('/').status_code, 200)

    def test_api_prefix(self):
        api = restplus.Api(self.app, prefix='/foo')
        self.assertEqual(api.prefix, '/foo')

    def test_handle_server_error(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            resp = api.handle_error(Exception())
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.data.decode(), dumps({
                "message": "Internal Server Error"
            }) + "\n")

    def test_handle_error_with_code(self):
        api = restplus.Api(self.app, serve_challenge_on_401=True)

        exception = Exception()
        exception.code = "Not an integer"
        exception.data = {'foo': 'bar'}

        with self.app.test_request_context("/foo"):
            resp = api.handle_error(exception)
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.data.decode(), dumps({"foo": "bar"}) + "\n")

    def test_handle_auth(self):
        api = restplus.Api(self.app, serve_challenge_on_401=True)

        with self.app.test_request_context("/foo"):
            resp = api.handle_error(Unauthorized())
            self.assertEqual(resp.status_code, 401)
            expected_data = dumps({'message': Unauthorized.description}) + "\n"
            self.assertEqual(resp.data.decode(), expected_data)

            self.assertTrue('WWW-Authenticate' in resp.headers)

    def test_handle_api_error(self):
        api = restplus.Api(self.app)

        class Test(restplus.Resource):
            def get(self):
                flask.abort(404)

        api.add_resource(Test(), '/api', endpoint='api')
        # app = self.app.test_client()

        resp = self.get("/api")
        assert_equals(resp.status_code, 404)
        assert_equals('application/json', resp.headers['Content-Type'])
        data = loads(resp.data.decode())
        assert_true('message' in data)

    def test_handle_non_api_error(self):
        restplus.Api(self.app)
        # app = self.app.test_client()

        resp = self.get("/foo")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual('text/html', resp.headers['Content-Type'])

    def test_non_api_error_404_catchall(self):
        api = restplus.Api(self.app, catch_all_404s=True)
        # app = self.app.test_client()

        resp = self.get("/foo")
        self.assertEqual(api.default_mediatype, resp.headers['Content-Type'])

    def test_handle_error_signal(self):
        if not signals_available:
            # This test requires the blinker lib to run.
            print("Can't test signals without signal support")
            return
        api = restplus.Api(self.app)

        exception = BadRequest()

        recorded = []

        def record(sender, exception):
            recorded.append(exception)

        got_request_exception.connect(record, self.app)
        try:
            with self.app.test_request_context("/foo"):
                api.handle_error(exception)
                self.assertEqual(len(recorded), 1)
                self.assertTrue(exception is recorded[0])
        finally:
            got_request_exception.disconnect(record, self.app)

    def test_handle_error(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            resp = api.handle_error(BadRequest())
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.data.decode(), dumps({
                'message': BadRequest.description,
            }) + "\n")

    def test_handle_smart_errors(self):
        api = restplus.Api(self.app)
        view = restplus.Resource

        api.add_resource(view, '/foo', endpoint='bor')
        api.add_resource(view, '/fee', endpoint='bir')
        api.add_resource(view, '/fii', endpoint='ber')

        with self.app.test_request_context("/faaaaa"):
            resp = api.handle_error(NotFound())
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(resp.data.decode(), dumps({
                "message": NotFound.description,
            }) + "\n")

        with self.app.test_request_context("/fOo"):
            resp = api.handle_error(NotFound())
            self.assertEqual(resp.status_code, 404)
            self.assertTrue('did you mean /foo ?' in resp.data.decode())

        self.app.config['ERROR_404_HELP'] = False

        with self.app.test_request_context("/fOo"):
            resp = api.handle_error(NotFound())
            self.assertEqual(resp.status_code, 404)
            self.assertEqual(resp.data.decode(), dumps({
                "message": NotFound.description
            }) + "\n")

    def test_error_router_falls_back_to_original(self):
        """Verify that if an exception occurs in the Flask-RESTPlus error handler,
        the error_router will call the original flask error handler instead.
        """
        api = restplus.Api(self.app)
        self.app.handle_exception = Mock()
        api.handle_error = Mock(side_effect=Exception())
        api._has_fr_route = Mock(return_value=True)
        exception = Mock(spec=HTTPException)

        with self.app.test_request_context('/foo'):
            api.error_router(exception, self.app.handle_exception)

        self.assertTrue(self.app.handle_exception.called_with(exception))

    def test_media_types(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo", headers={
            'Accept': 'application/json'
        }):
            self.assertEqual(api.mediatypes(), ['application/json'])

    def test_media_types_method(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo", headers={
            'Accept': 'application/xml; q=.5'
        }):
            self.assertEqual(api.mediatypes_method()(Mock()),
                             ['application/xml', 'application/json'])

    def test_media_types_q(self):
        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo", headers={
            'Accept': 'application/json; q=1, application/xml; q=.5'
        }):
            self.assertEqual(api.mediatypes(),
                             ['application/json', 'application/xml'])

    def test_decorator(self):
        def return_zero(func):
            return 0

        app = Mock(flask.Flask)
        app.view_functions = {}
        app.extensions = {}
        app.config = {}
        view = Mock()
        api = restplus.Api(app)
        api.decorators.append(return_zero)
        api.output = Mock()
        api.add_resource(view, '/foo', endpoint='bar')

        app.add_url_rule.assert_called_with('/foo', view_func=0)

    def test_add_resource_endpoint(self):
        view = Mock(**{'as_view.return_value.__name__': str('test_view')})

        api = restplus.Api(self.app)
        api.add_resource(view, '/foo', endpoint='bar')

        view.as_view.assert_called_with('bar', api)

    def test_add_two_conflicting_resources_on_same_endpoint(self):
        api = restplus.Api(self.app)

        class Foo1(restplus.Resource):
            def get(self):
                return 'foo1'

        class Foo2(restplus.Resource):
            def get(self):
                return 'foo2'

        api.add_resource(Foo1, '/foo', endpoint='bar')
        self.assertRaises(ValueError, api.add_resource, Foo2, '/foo/toto', endpoint='bar')

    def test_add_the_same_resource_on_same_endpoint(self):
        api = restplus.Api(self.app)

        class Foo1(restplus.Resource):
            def get(self):
                return 'foo1'

        api.add_resource(Foo1, '/foo', endpoint='bar')
        api.add_resource(Foo1, '/foo/toto', endpoint='blah')

        with self.app.test_client() as client:
            foo1 = client.get('/foo')
            self.assertEqual(foo1.data, b'"foo1"\n')
            foo2 = client.get('/foo/toto')
            self.assertEqual(foo2.data, b'"foo1"\n')

    def test_add_resource(self):
        app = Mock(flask.Flask)
        app.view_functions = {}
        app.extensions = {}
        app.config = {}
        api = restplus.Api(app)
        api.output = Mock()
        api.add_resource(views.MethodView, '/foo')

        app.add_url_rule.assert_called_with('/foo',
                                            view_func=api.output())

    def test_add_resource_kwargs(self):
        app = Mock(flask.Flask)
        app.view_functions = {}
        app.extensions = {}
        app.config = {}
        api = restplus.Api(app)
        api.output = Mock()
        api.add_resource(views.MethodView, '/foo', defaults={"bar": "baz"})

        app.add_url_rule.assert_called_with('/foo',
                                            view_func=api.output(),
                                            defaults={"bar": "baz"})

    def test_add_resource_forward_resource_class_parameters(self):
        api = restplus.Api(self.app)

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

        foo = self.get('/foo')
        self.assertEqual(foo.data, b'"wonderful slurm"\n')

    def test_output_unpack(self):

        def make_empty_response():
            return {'foo': 'bar'}

        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            wrapper = api.output(make_empty_response)
            resp = wrapper()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data.decode(), '{"foo": "bar"}\n')

    def test_output_func(self):

        def make_empty_resposne():
            return flask.make_response('')

        api = restplus.Api(self.app)

        with self.app.test_request_context("/foo"):
            wrapper = api.output(make_empty_resposne)
            resp = wrapper()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data.decode(), '')

    def test_resource(self):
        resource = restplus.Resource()
        resource.get = Mock()
        with self.app.test_request_context("/foo"):
            resource.dispatch_request()

    def test_resource_resp(self):
        resource = restplus.Resource()
        resource.get = Mock()
        with self.app.test_request_context("/foo"):
            resource.get.return_value = flask.make_response('')
            resource.dispatch_request()

    def test_resource_text_plain(self):
        def text(data, code, headers=None):
            return flask.make_response(six.text_type(data))

        class Foo(restplus.Resource):
            representations = {
                'text/plain': text,
            }

            def get(self):
                return 'hello'

        with self.app.test_request_context("/foo", headers={'Accept': 'text/plain'}):
            resource = Foo(None)
            resp = resource.dispatch_request()
            self.assertEqual(resp.data.decode(), 'hello')

    def test_resource_error(self):
        resource = restplus.Resource()
        with self.app.test_request_context("/foo"):
            self.assertRaises(AssertionError, lambda: resource.dispatch_request())

    def test_resource_head(self):
        resource = restplus.Resource()
        with self.app.test_request_context("/foo", method="HEAD"):
            self.assertRaises(AssertionError, lambda: resource.dispatch_request())

    def test_abort_data(self):
        try:
            restplus.abort(404, foo='bar')
            assert False  # We should never get here
        except Exception as e:
            self.assertEqual(e.data, {'foo': 'bar'})

    def test_abort_no_data(self):
        try:
            restplus.abort(404)
            assert False  # We should never get here
        except Exception as e:
            self.assertEqual(False, hasattr(e, "data"))

    def test_abort_custom_message(self):
        try:
            restplus.abort(404, message="no user")
            assert False  # We should never get here
        except Exception as e:
            assert_equals(e.data['message'], "no user")

    def test_abort_type(self):
        self.assertRaises(HTTPException, lambda: restplus.abort(404))

    def test_endpoints(self):
        api = restplus.Api(self.app)
        api.add_resource(HelloWorld, '/ids/<int:id>', endpoint="hello")
        with self.app.test_request_context('/foo'):
            self.assertFalse(api._has_fr_route())

        with self.app.test_request_context('/ids/3'):
            self.assertTrue(api._has_fr_route())

    def test_url_for(self):
        api = restplus.Api(self.app)
        api.add_resource(HelloWorld, '/ids/<int:id>')
        with self.app.test_request_context('/foo'):
            self.assertEqual(api.url_for(HelloWorld, id=123), '/ids/123')

    def test_url_for_with_blueprint(self):
        """Verify that url_for works when an Api object is mounted on a
        Blueprint.
        """
        api_bp = Blueprint('api', __name__)
        api = restplus.Api(api_bp)
        api.add_resource(HelloWorld, '/foo/<string:bar>')
        self.app.register_blueprint(api_bp)
        with self.app.test_request_context('/foo'):
            self.assertEqual(api.url_for(HelloWorld, bar='baz'), '/foo/baz')

    def test_fr_405(self):
        api = restplus.Api(self.app)
        api.add_resource(HelloWorld, '/ids/<int:id>', endpoint="hello")
        resp = self.post('/ids/3')
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.content_type, api.default_mediatype)
        # Allow can be of the form 'GET, PUT, POST'
        allow = ', '.join(set(resp.headers.get_all('Allow')))
        allow = set(method.strip() for method in allow.split(','))
        self.assertEqual(allow,
                         set(['HEAD', 'OPTIONS'] + HelloWorld.methods))

    def test_exception_header_forwarded(self):
        """Test that HTTPException's headers are extended properly"""
        self.app.config['DEBUG'] = True
        api = restplus.Api(self.app)

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

        with self.app.test_client() as client:
            foo = client.get('/foo')
            self.assertEqual(foo.get_etag(),
                             unquote_etag(quote_etag('myETag')))

    def test_exception_header_forwarding_doesnt_duplicate_headers(self):
        """Test that HTTPException's headers do not add a duplicate
        Content-Length header

        https://github.com/flask-restful/flask-restful/issues/534
        """
        api = restplus.Api(self.app)

        with self.app.test_request_context('/'):
            r = api.handle_error(BadRequest())

        self.assertEqual(len(r.headers.getlist('Content-Length')), 1)

    def test_will_prettyprint_json_in_debug_mode(self):
        self.app.config['DEBUG'] = True
        api = restplus.Api(self.app)

        class Foo1(restplus.Resource):
            def get(self):
                return {'foo': 'bar', 'baz': 'asdf'}

        api.add_resource(Foo1, '/foo', endpoint='bar')

        with self.app.test_client() as client:
            foo = client.get('/foo')

            # Python's dictionaries have random order (as of "new" Pythons,
            # anyway), so we can't verify the actual output here.  We just
            # assert that they're properly prettyprinted.
            lines = foo.data.splitlines()
            lines = [line.decode() for line in lines]
            self.assertEqual("{", lines[0])
            self.assertTrue(lines[1].startswith('    '))
            self.assertTrue(lines[2].startswith('    '))
            self.assertEqual("}", lines[3])

            # Assert our trailing newline.
            self.assertTrue(foo.data.endswith(b'\n'))

    def test_read_json_settings_from_config(self):
        class TestConfig(object):
            RESTPLUS_JSON = {'indent': 2,
                             'sort_keys': True,
                             'separators': (', ', ': ')}

        self.app.config.from_object(TestConfig)
        api = restplus.Api(self.app)

        class Foo(restplus.Resource):
            def get(self):
                return {'foo': 'bar', 'baz': 'qux'}

        api.add_resource(Foo, '/foo')

        with self.app.test_client() as client:
            data = client.get('/foo').data

        expected = b'{\n  "baz": "qux", \n  "foo": "bar"\n}\n'

        self.assertEqual(data, expected)

    def test_use_custom_jsonencoder(self):
        class CabageEncoder(JSONEncoder):
            def default(self, obj):
                return 'cabbage'

        class TestConfig(object):
            RESTPLUS_JSON = {'cls': CabageEncoder}

        self.app.config.from_object(TestConfig)
        api = restplus.Api(self.app)

        class Cabbage(restplus.Resource):
            def get(self):
                return {'frob': object()}

        api.add_resource(Cabbage, '/cabbage')

        with self.app.test_client() as client:
            data = client.get('/cabbage').data

        expected = b'{"frob": "cabbage"}\n'
        self.assertEqual(data, expected)

    def test_json_with_no_settings(self):
        api = restplus.Api(self.app)

        class Foo(restplus.Resource):
            def get(self):
                return {'foo': 'bar'}

        api.add_resource(Foo, '/foo')

        with self.app.test_client() as client:
            data = client.get('/foo').data

        expected = b'{"foo": "bar"}\n'
        self.assertEqual(data, expected)

    def test_redirect(self):
        api = restplus.Api(self.app)

        class FooResource(restplus.Resource):
            def get(self):
                return redirect('/')

        api.add_resource(FooResource, '/api')

        resp = self.get('/api')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers['Location'], 'http://localhost/')

    def test_json_float_marshalled(self):
        api = restplus.Api(self.app)

        class FooResource(restplus.Resource):
            fields = {'foo': restplus.fields.Float}

            def get(self):
                return restplus.marshal({"foo": 3.0}, self.fields)

        api.add_resource(FooResource, '/api')

        resp = self.get('/api')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode('utf-8'), '{"foo": 3.0}\n')

    def test_calling_owns_endpoint_before_api_init(self):
        api = restplus.Api()

        try:
            api.owns_endpoint('endpoint')
        except AttributeError as ae:
            self.fail(ae.message)
