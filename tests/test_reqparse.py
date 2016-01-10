# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import decimal
import json
import six

from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Request
from werkzeug.datastructures import FileStorage, MultiDict

from flask_restplus import Api, Model, fields
from flask_restplus.errors import SpecsError
from flask_restplus.reqparse import Argument, RequestParser, ParseResult

from . import TestCase, Mock, patch


class ReqParseTestCase(TestCase):
    def test_api_shortcut(self):
        api = Api(self.app)
        parser = api.parser()
        self.assertIsInstance(parser, RequestParser)

    def test_parse_model(self):
        model = Model('Todo', {
            'task': fields.String(required=True)
        })

        parser = RequestParser()
        parser.add_argument('todo', type=model, required=True)

        data = {'todo': {'task': 'aaa'}}

        with self.app.test_request_context('/', method='post',
                                           data=json.dumps(data),
                                           content_type='application/json'):
            args = parser.parse_args()
            self.assertEqual(args['todo'], {'task': 'aaa'})

    @patch('flask_restplus.reqparse.abort')
    def test_help_with_error_msg(self, abort):
        parser = RequestParser()
        parser.add_argument('foo', choices=('one', 'two'), help='Bad choice: {error_msg}')
        req = Mock(['values'])
        req.values = MultiDict([('foo', 'three')])
        with self.app.app_context():
            parser.parse_args(req)
        expected = {'foo': 'Bad choice: three is not a valid choice'}
        abort.assert_called_with(400, 'Input payload validation failed', errors=expected)

    @patch('flask_restplus.reqparse.abort')
    def test_help_no_error_msg(self, abort):
        parser = RequestParser()
        parser.add_argument('foo', choices=['one', 'two'], help='Please select a valid choice')
        req = Mock(['values'])
        req.values = MultiDict([('foo', 'three')])
        with self.app.app_context():
            parser.parse_args(req)
        expected = {'foo': 'Please select a valid choice'}
        abort.assert_called_with(400, 'Input payload validation failed', errors=expected)

    @patch('flask_restplus.reqparse.abort', side_effect=BadRequest('Bad Request'))
    def test_no_help(self, abort):
        parser = RequestParser()
        parser.add_argument('foo', choices=['one', 'two'])
        req = Mock(['values'])
        req.values = MultiDict([('foo', 'three')])
        with self.app.app_context():
            with self.assertRaises(BadRequest):
                parser.parse_args(req)
        expected = {'foo': 'three is not a valid choice'}
        abort.assert_called_with(400, 'Input payload validation failed', errors=expected)

    def test_viewargs(self):
        req = Request.from_values()
        req.view_args = {'foo': 'bar'}
        parser = RequestParser()
        parser.add_argument('foo', location=['view_args'])
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

        req = Mock()
        req.values = ()
        req.json = None
        req.view_args = {'foo': 'bar'}
        parser = RequestParser()
        parser.add_argument('foo', store_missing=True)
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], None)

    def test_parse_unicode(self):
        req = Request.from_values('/bubble?foo=barß')
        parser = RequestParser()
        parser.add_argument('foo')

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'barß')

    def test_parse_unicode_app(self):
        parser = RequestParser()
        parser.add_argument('foo')

        with self.app.test_request_context('/bubble?foo=barß'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], 'barß')

    def test_json_location(self):
        parser = RequestParser()
        parser.add_argument('foo', location='json', store_missing=True)

        with self.app.test_request_context('/bubble', method='post'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], None)

    def test_get_json_location(self):
        parser = RequestParser()
        parser.add_argument('foo', location='json')

        with self.app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': 'bar'}),
                                      content_type='application/json'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], 'bar')

    def test_parse_append_ignore(self):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo', ignore=True, type=int, action='append',
                            store_missing=True),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], None)

    def test_parse_append_default(self):
        req = Request.from_values('/bubble?')

        parser = RequestParser()
        parser.add_argument('foo', action='append', store_missing=True),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], None)

    def test_parse_append(self):
        req = Request.from_values('/bubble?foo=bar&foo=bat')

        parser = RequestParser()
        parser.add_argument('foo', action='append'),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], ['bar', 'bat'])

    def test_parse_append_single(self):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo', action='append'),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], ['bar'])

    def test_parse_dest(self):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo', dest='bat')

        args = parser.parse_args(req)
        self.assertEqual(args['bat'], 'bar')

    def test_parse_gte_lte_eq(self):
        req = Request.from_values('/bubble?foo>=bar&foo<=bat&foo=foo')

        parser = RequestParser()
        parser.add_argument('foo', operators=['>=', '<=', '='], action='append'),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], ['bar', 'bat', 'foo'])

    def test_parse_gte(self):
        req = Request.from_values('/bubble?foo>=bar')

        parser = RequestParser()
        parser.add_argument('foo', operators=['>='])

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_parse_foo_operators_four_hunderd(self):
        parser = RequestParser()
        parser.add_argument('foo', type=int),
        with self.app.app_context():
            with self.assertRaises(BadRequest):
                parser.parse_args(Request.from_values('/bubble?foo=bar'))

    def test_parse_foo_operators_ignore(self):
        parser = RequestParser()
        parser.add_argument('foo', ignore=True, store_missing=True)

        args = parser.parse_args(Request.from_values('/bubble'))
        self.assertEqual(args['foo'], None)

    def test_parse_lte_gte_mock(self):
        mock_type = Mock()
        req = Request.from_values('/bubble?foo<=bar')

        parser = RequestParser()
        parser.add_argument('foo', type=mock_type, operators=['<='])

        parser.parse_args(req)
        mock_type.assert_called_with('bar', 'foo', '<=')

    def test_parse_lte_gte_append(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['<=', '='], action='append')

        args = parser.parse_args(Request.from_values('/bubble?foo<=bar'))
        self.assertEqual(args['foo'], ['bar'])

    def test_parse_lte_gte_missing(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['<=', '='])
        args = parser.parse_args(Request.from_values('/bubble?foo<=bar'))
        self.assertEqual(args['foo'], 'bar')

    def test_parse_eq_other(self):
        parser = RequestParser()
        parser.add_argument('foo'),
        args = parser.parse_args(Request.from_values('/bubble?foo=bar&foo=bat'))
        self.assertEqual(args['foo'], 'bar')

    def test_parse_eq(self):
        req = Request.from_values('/bubble?foo=bar')
        parser = RequestParser()
        parser.add_argument('foo'),
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_parse_lte(self):
        req = Request.from_values('/bubble?foo<=bar')
        parser = RequestParser()
        parser.add_argument('foo', operators=['<='])

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_parse_required(self):
        with self.app.app_context():
            req = Request.from_values('/bubble')

            parser = RequestParser()
            parser.add_argument('foo', required=True, location='values')

            expected = {
                'foo': 'Missing required parameter in the post body or the query string'
            }
            try:
                parser.parse_args(req)
            except BadRequest as e:
                self.assertEqual(e.data['message'], 'Input payload validation failed')
                self.assertEqual(e.data['errors'], expected)

            parser = RequestParser()
            parser.add_argument('bar', required=True, location=['values', 'cookies'])

            expected = {
                'bar': ("Missing required parameter in the post body or the query "
                "string or the request's cookies")
            }
            try:
                parser.parse_args(req)
            except BadRequest as e:
                self.assertEqual(e.data['message'], 'Input payload validation failed')
                self.assertEqual(e.data['errors'], expected)

    def test_parse_error_bundling(self):
        self.app.config['BUNDLE_ERRORS'] = True
        req = Request.from_values('/bubble')

        parser = RequestParser()
        parser.add_argument('foo', required=True, location='values')
        parser.add_argument('bar', required=True, location=['values', 'cookies'])

        with self.app.app_context():
            try:
                parser.parse_args(req)
            except BadRequest as e:
                self.assertEqual(e.data['message'], 'Input payload validation failed')
                self.assertEqual(e.data['errors'], {
                    'foo': 'Missing required parameter in the post body or the query string',
                    'bar': ("Missing required parameter in the post body or the query string "
                            "or the request's cookies")
                })

    def test_parse_error_bundling_w_parser_arg(self):
        self.app.config['BUNDLE_ERRORS'] = False
        req = Request.from_values('/bubble')

        parser = RequestParser(bundle_errors=True)
        parser.add_argument('foo', required=True, location='values')
        parser.add_argument('bar', required=True, location=['values', 'cookies'])
        with self.app.app_context():
            try:
                parser.parse_args(req)
            except BadRequest as e:
                self.assertEqual(e.data['message'], 'Input payload validation failed')
                self.assertEqual(e.data['errors'], {
                    'foo': 'Missing required parameter in the post body or the query string',
                    'bar': ("Missing required parameter in the post body or the query string "
                            "or the request's cookies")
                })

    def test_parse_default_append(self):
        req = Request.from_values('/bubble')
        parser = RequestParser()
        parser.add_argument('foo', default='bar', action='append',
                            store_missing=True)

        args = parser.parse_args(req)

        self.assertEqual(args['foo'], 'bar')

    def test_parse_default(self):
        req = Request.from_values('/bubble')

        parser = RequestParser()
        parser.add_argument('foo', default='bar', store_missing=True)

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_parse_callable_default(self):
        req = Request.from_values('/bubble')

        parser = RequestParser()
        parser.add_argument('foo', default=lambda: 'bar', store_missing=True)

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_parse(self):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo'),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_parse_none(self):
        req = Request.from_values('/bubble')

        parser = RequestParser()
        parser.add_argument('foo')

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], None)

    def test_parse_store_missing(self):
        req = Request.from_values('/bubble')

        parser = RequestParser()
        parser.add_argument('foo', store_missing=False)

        args = parser.parse_args(req)
        self.assertFalse('foo' in args)

    def test_parse_choices_correct(self):
        req = Request.from_values('/bubble?foo=bat')

        parser = RequestParser()
        parser.add_argument('foo', choices=['bat']),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bat')

    def test_parse_choices(self):
        with self.app.app_context():
            req = Request.from_values('/bubble?foo=bar')

            parser = RequestParser()
            parser.add_argument('foo', choices=['bat']),

            self.assertRaises(BadRequest, lambda: parser.parse_args(req))

    def test_parse_choices_sensitive(self):
        with self.app.app_context():
            req = Request.from_values('/bubble?foo=BAT')

            parser = RequestParser()
            parser.add_argument('foo', choices=['bat'], case_sensitive=True),

            self.assertRaises(BadRequest, lambda: parser.parse_args(req))

    def test_parse_choices_insensitive(self):
        req = Request.from_values('/bubble?foo=BAT')

        parser = RequestParser()
        parser.add_argument('foo', choices=['bat'], case_sensitive=False),

        args = parser.parse_args(req)
        self.assertEqual('bat', args.get('foo'))

        # both choices and args are case_insensitive
        req = Request.from_values('/bubble?foo=bat')

        parser = RequestParser()
        parser.add_argument('foo', choices=['BAT'], case_sensitive=False),

        args = parser.parse_args(req)
        self.assertEqual('bat', args.get('foo'))

    def test_parse_ignore(self):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo', type=int, ignore=True, store_missing=True),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], None)

    def test_chaining(self):
        parser = RequestParser()
        self.assertTrue(parser is parser.add_argument('foo'))

    def test_result_existence(self):
        result = ParseResult()
        result.foo = 'bar'
        result['bar'] = 'baz'
        self.assertEqual(result['foo'], 'bar')
        self.assertEqual(result.bar, 'baz')

    def test_result_missing(self):
        result = ParseResult()
        self.assertRaises(AttributeError, lambda: result.spam)
        self.assertRaises(KeyError, lambda: result['eggs'])

    def test_result_configurability(self):
        req = Request.from_values()
        self.assertTrue(isinstance(RequestParser().parse_args(req), ParseResult))
        self.assertTrue(type(RequestParser(result_class=dict).parse_args(req)) is dict)

    def test_none_argument(self):
        parser = RequestParser()
        parser.add_argument('foo', location='json')
        with self.app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': None}),
                                      content_type='application/json'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], None)

    def test_type_callable(self):
        req = Request.from_values('/bubble?foo=1')

        parser = RequestParser()
        parser.add_argument('foo', type=lambda x: x, required=False),

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], '1')

    def test_type_callable_none(self):
        parser = RequestParser()
        parser.add_argument('foo', type=lambda x: x, location='json', required=False),

        with self.app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': None}),
                                      content_type='application/json'):
            try:
                args = parser.parse_args()
                self.assertEqual(args['foo'], None)
            except BadRequest:
                self.fail()

    def test_type_decimal(self):
        parser = RequestParser()
        parser.add_argument('foo', type=decimal.Decimal, location='json')

        with self.app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': '1.0025'}),
                                      content_type='application/json'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], decimal.Decimal('1.0025'))

    def test_type_filestorage(self):
        parser = RequestParser()
        parser.add_argument('foo', type=FileStorage, location='files')

        fdata = 'foo bar baz qux'.encode('utf-8')
        with self.app.test_request_context('/bubble', method='POST',
                                      data={'foo': (six.BytesIO(fdata), 'baz.txt')}):
            args = parser.parse_args()

            self.assertEqual(args['foo'].name, 'foo')
            self.assertEqual(args['foo'].filename, 'baz.txt')
            self.assertEqual(args['foo'].read(), fdata)

    def test_filestorage_custom_type(self):
        def _custom_type(f):
            return FileStorage(stream=f.stream,
                               filename='{0}aaaa'.format(f.filename),
                               name='{0}aaaa'.format(f.name))

        parser = RequestParser()
        parser.add_argument('foo', type=_custom_type, location='files')

        fdata = 'foo bar baz qux'.encode('utf-8')
        with self.app.test_request_context('/bubble', method='POST',
                                      data={'foo': (six.BytesIO(fdata), 'baz.txt')}):
            args = parser.parse_args()

            self.assertEqual(args['foo'].name, 'fooaaaa')
            self.assertEqual(args['foo'].filename, 'baz.txtaaaa')
            self.assertEqual(args['foo'].read(), fdata)

    def test_passing_arguments_object(self):
        req = Request.from_values('/bubble?foo=bar')
        parser = RequestParser()
        parser.add_argument(Argument('foo'))

        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 'bar')

    def test_int_choice_types(self):
        parser = RequestParser()
        parser.add_argument('foo', type=int, choices=[1, 2, 3], location='json')

        with self.app.test_request_context(
                '/bubble', method='post',
                data=json.dumps({'foo': 5}),
                content_type='application/json'
        ):
            try:
                parser.parse_args()
                self.fail()
            except BadRequest:
                pass

    def test_int_range_choice_types(self):
        parser = RequestParser()
        parser.add_argument('foo', type=int, choices=range(100), location='json')

        with self.app.test_request_context(
                '/bubble', method='post',
                data=json.dumps({'foo': 101}),
                content_type='application/json'
        ):
            try:
                parser.parse_args()
                self.fail()
            except BadRequest:
                pass

    def test_request_parser_copy(self):
        req = Request.from_values('/bubble?foo=101&bar=baz')
        parser = RequestParser()
        foo_arg = Argument('foo', type=int)
        parser.args.append(foo_arg)
        parser_copy = parser.copy()

        # Deepcopy should create a clone of the argument object instead of
        # copying a reference to the new args list
        self.assertFalse(foo_arg in parser_copy.args)

        # Args added to new parser should not be added to the original
        bar_arg = Argument('bar')
        parser_copy.args.append(bar_arg)
        self.assertFalse(bar_arg in parser.args)

        args = parser_copy.parse_args(req)
        self.assertEqual(args['foo'], 101)
        self.assertEqual(args['bar'], 'baz')

    def test_request_parse_copy_including_settings(self):
        parser = RequestParser(trim=True, bundle_errors=True)
        parser_copy = parser.copy()

        self.assertEqual(parser.trim, parser_copy.trim)
        self.assertEqual(parser.bundle_errors, parser_copy.bundle_errors)

    def test_request_parser_replace_argument(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        parser_copy = parser.copy()
        parser_copy.replace_argument('foo')

        args = parser_copy.parse_args(req)
        self.assertEqual(args['foo'], 'baz')

    def test_both_json_and_values_location(self):
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        parser.add_argument('baz', type=int)
        with self.app.test_request_context('/bubble?foo=1', method='post',
                                      data=json.dumps({'baz': 2}),
                                      content_type='application/json'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], 1)
            self.assertEqual(args['baz'], 2)

    def test_not_json_location_and_content_type_json(self):
        parser = RequestParser()
        parser.add_argument('foo', location='args')

        with self.app.test_request_context('/bubble', method='get',
                                      content_type='application/json'):
            parser.parse_args()  # Should not raise a 400: BadRequest

    def test_request_parser_remove_argument(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        parser_copy = parser.copy()
        parser_copy.remove_argument('foo')

        args = parser_copy.parse_args(req)
        self.assertEqual(args, {})

    def test_strict_parsing_off(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        args = parser.parse_args(req)
        self.assertEqual(args, {})

    def test_strict_parsing_on(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        self.assertRaises(BadRequest, parser.parse_args, req, strict=True)

    def test_strict_parsing_off_partial_hit(self):
        req = Request.from_values('/bubble?foo=1&bar=bees&n=22')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 1)

    def test_strict_parsing_on_partial_hit(self):
        req = Request.from_values('/bubble?foo=1&bar=bees&n=22')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        self.assertRaises(BadRequest, parser.parse_args, req, strict=True)

    def test_trim_argument(self):
        req = Request.from_values('/bubble?foo= 1 &bar=bees&n=22')
        parser = RequestParser()
        parser.add_argument('foo')
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], ' 1 ')

        parser = RequestParser()
        parser.add_argument('foo', trim=True)
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], '1')

        parser = RequestParser()
        parser.add_argument('foo', trim=True, type=int)
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 1)

    def test_trim_request_parser(self):
        req = Request.from_values('/bubble?foo= 1 &bar=bees&n=22')
        parser = RequestParser(trim=False)
        parser.add_argument('foo')
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], ' 1 ')

        parser = RequestParser(trim=True)
        parser.add_argument('foo')
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], '1')

        parser = RequestParser(trim=True)
        parser.add_argument('foo', type=int)
        args = parser.parse_args(req)
        self.assertEqual(args['foo'], 1)

    def test_trim_request_parser_override_by_argument(self):
        parser = RequestParser(trim=True)
        parser.add_argument('foo', trim=False)

        self.assertFalse(parser.args[0].trim)

    def test_trim_request_parser_json(self):
        parser = RequestParser(trim=True)
        parser.add_argument('foo', location='json')
        parser.add_argument('int1', location='json', type=int)
        parser.add_argument('int2', location='json', type=int)

        with self.app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': ' bar ', 'int1': 1, 'int2': ' 2 '}),
                                      content_type='application/json'):
            args = parser.parse_args()
            self.assertEqual(args['foo'], 'bar')
            self.assertEqual(args['int1'], 1)
            self.assertEqual(args['int2'], 2)


class ArgumentTest(TestCase):
    def test_name(self):
        arg = Argument('foo')
        self.assertEqual(arg.name, 'foo')

    def test_dest(self):
        arg = Argument('foo', dest='foobar')
        self.assertEqual(arg.dest, 'foobar')

    def test_location_url(self):
        arg = Argument('foo', location='url')
        self.assertEqual(arg.location, 'url')

    def test_location_url_list(self):
        arg = Argument('foo', location=['url'])
        self.assertEqual(arg.location, ['url'])

    def test_location_header(self):
        arg = Argument('foo', location='headers')
        self.assertEqual(arg.location, 'headers')

    def test_location_json(self):
        arg = Argument('foo', location='json')
        self.assertEqual(arg.location, 'json')

    def test_location_get_json(self):
        arg = Argument('foo', location='get_json')
        self.assertEqual(arg.location, 'get_json')

    def test_location_header_list(self):
        arg = Argument('foo', location=['headers'])
        self.assertEqual(arg.location, ['headers'])

    def test_type(self):
        arg = Argument('foo', type=int)
        self.assertEqual(arg.type, int)

    def test_default(self):
        arg = Argument('foo', default=True)
        self.assertEqual(arg.default, True)

    def test_default_help(self):
        arg = Argument('foo')
        self.assertEqual(arg.help, None)

    def test_required(self):
        arg = Argument('foo', required=True)
        self.assertEqual(arg.required, True)

    def test_ignore(self):
        arg = Argument('foo', ignore=True)
        self.assertEqual(arg.ignore, True)

    def test_operator(self):
        arg = Argument('foo', operators=['>=', '<=', '='])
        self.assertEqual(arg.operators, ['>=', '<=', '='])

    def test_action_filter(self):
        arg = Argument('foo', action='filter')
        self.assertEqual(arg.action, 'filter')

    def test_action(self):
        arg = Argument('foo', action='append')
        self.assertEqual(arg.action, 'append')

    def test_choices(self):
        arg = Argument('foo', choices=[1, 2])
        self.assertEqual(arg.choices, [1, 2])

    def test_default_dest(self):
        arg = Argument('foo')
        self.assertEqual(arg.dest, None)

    def test_default_operators(self):
        arg = Argument('foo')
        self.assertEqual(arg.operators[0], '=')
        self.assertEqual(len(arg.operators), 1)

    @patch('flask_restplus.reqparse.six')
    def test_default_type(self, mock_six):
        arg = Argument('foo')
        sentinel = object()
        arg.type(sentinel)
        mock_six.text_type.assert_called_with(sentinel)

    def test_default_default(self):
        arg = Argument('foo')
        self.assertEqual(arg.default, None)

    def test_required_default(self):
        arg = Argument('foo')
        self.assertEqual(arg.required, False)

    def test_ignore_default(self):
        arg = Argument('foo')
        self.assertEqual(arg.ignore, False)

    def test_action_default(self):
        arg = Argument('foo')
        self.assertEqual(arg.action, 'store')

    def test_choices_default(self):
        arg = Argument('foo')
        self.assertEqual(len(arg.choices), 0)

    def test_source(self):
        req = Mock(['args', 'headers', 'values'])
        req.args = {'foo': 'bar'}
        req.headers = {'baz': 'bat'}
        arg = Argument('foo', location=['args'])
        self.assertEqual(arg.source(req), MultiDict(req.args))

        arg = Argument('foo', location=['headers'])
        self.assertEqual(arg.source(req), MultiDict(req.headers))

    def test_convert_default_type_with_null_input(self):
        arg = Argument('foo')
        self.assertEqual(arg.convert(None, None), None)

    def test_convert_with_null_input_when_not_nullable(self):
        arg = Argument('foo', nullable=False)
        self.assertRaises(ValueError, lambda: arg.convert(None, None))

    def test_source_bad_location(self):
        req = Mock(['values'])
        arg = Argument('foo', location=['foo'])
        self.assertTrue(len(arg.source(req)) == 0)  # yes, basically you don't find it

    def test_source_default_location(self):
        req = Mock(['values'])
        req._get_child_mock = lambda **kwargs: MultiDict()
        arg = Argument('foo')
        self.assertEqual(arg.source(req), req.values)

    def test_option_case_sensitive(self):
        arg = Argument('foo', choices=['bar', 'baz'], case_sensitive=True)
        self.assertEqual(True, arg.case_sensitive)

        # Insensitive
        arg = Argument('foo', choices=['bar', 'baz'], case_sensitive=False)
        self.assertEqual(False, arg.case_sensitive)

        # Default
        arg = Argument('foo', choices=['bar', 'baz'])
        self.assertEqual(True, arg.case_sensitive)


class RequestParserSchemaTest(TestCase):
    def test_empty_parser(self):
        parser = RequestParser()
        self.assertEqual(parser.__schema__, [])

    def test_primitive_types(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, help='Some integer')
        parser.add_argument('str', type=str, help='Some string')
        self.assertEqual(parser.__schema__, [{
            'name': 'int',
            'type': 'integer',
            'in': 'query',
            'description': 'Some integer',
        }, {
            'name': 'str',
            'type': 'string',
            'in': 'query',
            'description': 'Some string',
        }])

    def test_unknown_type(self):
        parser = RequestParser()
        unknown = lambda v: v
        parser.add_argument('unknown', type=unknown)
        self.assertEqual(parser.__schema__, [{
            'name': 'unknown',
            'type': 'string',
            'in': 'query',
        }])

    def test_required(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, required=True)
        self.assertEqual(parser.__schema__, [{
            'name': 'int',
            'type': 'integer',
            'in': 'query',
            'required': True,
        }])

    def test_default(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, default=5)
        self.assertEqual(parser.__schema__, [{
            'name': 'int',
            'type': 'integer',
            'in': 'query',
            'default': 5,
        }])

    def test_choices(self):
        parser = RequestParser()
        parser.add_argument('string', type=str, choices=['a', 'b'])
        self.assertEqual(parser.__schema__, [{
            'name': 'string',
            'type': 'string',
            'in': 'query',
            'enum': ['a', 'b'],
            'collectionFormat': 'multi',
        }])

    def test_location(self):
        parser = RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_values', type=int, location='values')
        parser.add_argument('in_query', type=int, location='args')
        parser.add_argument('in_headers', type=int, location='headers')
        parser.add_argument('in_cookie', type=int, location='cookie')
        self.assertEqual(parser.__schema__, [{
            'name': 'default',
            'type': 'integer',
            'in': 'query',
        }, {
            'name': 'in_values',
            'type': 'integer',
            'in': 'query',
        }, {
            'name': 'in_query',
            'type': 'integer',
            'in': 'query',
        }, {
            'name': 'in_headers',
            'type': 'integer',
            'in': 'header',
        }])

    def test_location_json(self):
        parser = RequestParser()
        parser.add_argument('in_json', type=str, location='json')
        self.assertEqual(parser.__schema__, [{
            'name': 'in_json',
            'type': 'string',
            'in': 'body',
        }])

    def test_location_form(self):
        parser = RequestParser()
        parser.add_argument('in_form', type=int, location='form')
        self.assertEqual(parser.__schema__, [{
            'name': 'in_form',
            'type': 'integer',
            'in': 'formData',
        }])

    def test_location_files(self):
        parser = RequestParser()
        parser.add_argument('in_files', type=FileStorage, location='files')
        self.assertEqual(parser.__schema__, [{
            'name': 'in_files',
            'type': 'file',
            'in': 'formData',
        }])

    def test_form_and_body_location(self):
        parser = RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_form', type=int, location='form')
        parser.add_argument('in_json', type=str, location='json')
        with self.assertRaises(SpecsError) as cm:
            parser.__schema__

        self.assertEqual(cm.exception.msg, "Can't use formData and body at the same time")

    def test_files_and_body_location(self):
        parser = RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_files', type=FileStorage, location='files')
        parser.add_argument('in_json', type=str, location='json')
        with self.assertRaises(SpecsError) as cm:
            parser.__schema__

        self.assertEqual(cm.exception.msg, "Can't use formData and body at the same time")

    def test_models(self):
        # app = Flask(__name__)
        # api = Api(app)
        todo_fields = Model('Todo', {
            'task': fields.String(required=True, description='The task details')
        })
        parser = RequestParser()
        parser.add_argument('todo', type=todo_fields)
        self.assertEqual(parser.__schema__, [{
            'name': 'todo',
            'type': 'Todo',
            'in': 'body',
        }])

    def test_lists(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, action='append')
        self.assertEqual(parser.__schema__, [{
            'name': 'int',
            'in': 'query',
            'items': True,
            'type': 'array',
            'collectionFormat': 'multi',
            'items': {'type': 'integer'}
        }])

    def test_schema_interface(self):
        def custom(value):
            pass

        custom.__schema__ = {
            'type': 'string',
            'format': 'custom-format',
        }

        parser = RequestParser()
        parser.add_argument('custom', type=custom)

        self.assertDataEqual(parser.__schema__, [{
            'name': 'custom',
            'in': 'query',
            'type': 'string',
            'format': 'custom-format',
        }])
