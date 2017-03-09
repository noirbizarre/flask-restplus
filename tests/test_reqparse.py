# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import decimal
import json
import six
import pytest

from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Request
from werkzeug.datastructures import FileStorage, MultiDict

from flask_restplus import Api, Model, fields, inputs
from flask_restplus.errors import SpecsError
from flask_restplus.reqparse import Argument, RequestParser, ParseResult


class ReqParseTest(object):
    def test_api_shortcut(self, app):
        api = Api(app)
        parser = api.parser()
        assert isinstance(parser, RequestParser)

    def test_parse_model(self, app):
        model = Model('Todo', {
            'task': fields.String(required=True)
        })

        parser = RequestParser()
        parser.add_argument('todo', type=model, required=True)

        data = {'todo': {'task': 'aaa'}}

        with app.test_request_context('/', method='post',
                                      data=json.dumps(data),
                                      content_type='application/json'):
            args = parser.parse_args()
            assert args['todo'] == {'task': 'aaa'}

    def test_help(self, app, mocker):
        abort = mocker.patch('flask_restplus.reqparse.abort',
                           side_effect=BadRequest('Bad Request'))
        parser = RequestParser()
        parser.add_argument('foo', choices=('one', 'two'), help='Bad choice.')
        req = mocker.Mock(['values'])
        req.values = MultiDict([('foo', 'three')])
        with pytest.raises(BadRequest):
            parser.parse_args(req)
        expected = {'foo': 'Bad choice. The value \'three\' is not a valid choice for \'foo\'.'}
        abort.assert_called_with(400, 'Input payload validation failed', errors=expected)

    def test_no_help(self, app, mocker):
        abort = mocker.patch('flask_restplus.reqparse.abort',
                             side_effect=BadRequest('Bad Request'))
        parser = RequestParser()
        parser.add_argument('foo', choices=['one', 'two'])
        req = mocker.Mock(['values'])
        req.values = MultiDict([('foo', 'three')])
        with pytest.raises(BadRequest):
            parser.parse_args(req)
        expected = {'foo': 'The value \'three\' is not a valid choice for \'foo\'.'}
        abort.assert_called_with(400, 'Input payload validation failed', errors=expected)

    @pytest.mark.request_context()
    def test_viewargs(self, mocker):
        req = Request.from_values()
        req.view_args = {'foo': 'bar'}
        parser = RequestParser()
        parser.add_argument('foo', location=['view_args'])
        args = parser.parse_args(req)
        assert args['foo'] == 'bar'

        req = mocker.Mock()
        req.values = ()
        req.json = None
        req.view_args = {'foo': 'bar'}
        parser = RequestParser()
        parser.add_argument('foo', store_missing=True)
        args = parser.parse_args(req)
        assert args['foo'] is None

    def test_parse_unicode(self, app):
        req = Request.from_values('/bubble?foo=barß')
        parser = RequestParser()
        parser.add_argument('foo')

        args = parser.parse_args(req)
        assert args['foo'] == 'barß'

    def test_parse_unicode_app(self, app):
        parser = RequestParser()
        parser.add_argument('foo')

        with app.test_request_context('/bubble?foo=barß'):
            args = parser.parse_args()
            assert args['foo'] == 'barß'

    @pytest.mark.request_context('/bubble', method='post')
    def test_json_location(self):
        parser = RequestParser()
        parser.add_argument('foo', location='json', store_missing=True)

        args = parser.parse_args()
        assert args['foo'] is None

    @pytest.mark.request_context('/bubble', method='post',
                                 data=json.dumps({'foo': 'bar'}),
                                 content_type='application/json')
    def test_get_json_location(self):
        parser = RequestParser()
        parser.add_argument('foo', location='json')
        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_parse_append_ignore(self, app):
        parser = RequestParser()
        parser.add_argument('foo', ignore=True, type=int, action='append',
                            store_missing=True),

        args = parser.parse_args()
        assert args['foo'] is None

    @pytest.mark.request_context('/bubble?')
    def test_parse_append_default(self):
        parser = RequestParser()
        parser.add_argument('foo', action='append', store_missing=True),

        args = parser.parse_args()
        assert args['foo'] is None

    @pytest.mark.request_context('/bubble?foo=bar&foo=bat')
    def test_parse_append(self):
        parser = RequestParser()
        parser.add_argument('foo', action='append'),

        args = parser.parse_args()
        assert args['foo'] == ['bar', 'bat']

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_parse_append_single(self):
        parser = RequestParser()
        parser.add_argument('foo', action='append'),

        args = parser.parse_args()
        assert args['foo'] == ['bar']

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_split_single(self):
        parser = RequestParser()
        parser.add_argument('foo', action='split'),

        args = parser.parse_args()
        assert args['foo'] == ['bar']

    @pytest.mark.request_context('/bubble?foo=bar,bat')
    def test_split_multiple(self):
        parser = RequestParser()
        parser.add_argument('foo', action='split'),

        args = parser.parse_args()
        assert args['foo'] == ['bar', 'bat']

    @pytest.mark.request_context('/bubble?foo=1,2,3')
    def test_split_multiple_cast(self):
        parser = RequestParser()
        parser.add_argument('foo', type=int, action='split')

        args = parser.parse_args()
        assert args['foo'] == [1, 2, 3]

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_parse_dest(self):
        parser = RequestParser()
        parser.add_argument('foo', dest='bat')

        args = parser.parse_args()
        assert args['bat'] == 'bar'

    @pytest.mark.request_context('/bubble?foo>=bar&foo<=bat&foo=foo')
    def test_parse_gte_lte_eq(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['>=', '<=', '='], action='append'),

        args = parser.parse_args()
        assert args['foo'] == ['bar', 'bat', 'foo']

    @pytest.mark.request_context('/bubble?foo>=bar')
    def test_parse_gte(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['>='])

        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_parse_foo_operators_four_hunderd(self):
        parser = RequestParser()
        parser.add_argument('foo', type=int),
        with pytest.raises(BadRequest):
            parser.parse_args()

    @pytest.mark.request_context('/bubble')
    def test_parse_foo_operators_ignore(self):
        parser = RequestParser()
        parser.add_argument('foo', ignore=True, store_missing=True)

        args = parser.parse_args()
        assert args['foo'] is None

    @pytest.mark.request_context('/bubble?foo<=bar')
    def test_parse_lte_gte_mock(self, mocker):
        mock_type = mocker.Mock()

        parser = RequestParser()
        parser.add_argument('foo', type=mock_type, operators=['<='])

        parser.parse_args()
        mock_type.assert_called_with('bar', 'foo', '<=')

    @pytest.mark.request_context('/bubble?foo<=bar')
    def test_parse_lte_gte_append(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['<=', '='], action='append')

        args = parser.parse_args()
        assert args['foo'] == ['bar']

    @pytest.mark.request_context('/bubble?foo<=bar')
    def test_parse_lte_gte_missing(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['<=', '='])
        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble?foo=bar&foo=bat')
    def test_parse_eq_other(self):
        parser = RequestParser()
        parser.add_argument('foo'),
        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_parse_eq(self):
        parser = RequestParser()
        parser.add_argument('foo'),
        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble?foo<=bar')
    def test_parse_lte(self):
        parser = RequestParser()
        parser.add_argument('foo', operators=['<='])

        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble')
    def test_parse_required(self, app):
        parser = RequestParser()
        parser.add_argument('foo', required=True, location='values')

        expected = {
            'foo': 'Missing required parameter in the post body or the query string'
        }
        with pytest.raises(BadRequest) as cm:
            parser.parse_args()

        assert cm.value.data['message'] == 'Input payload validation failed'
        assert cm.value.data['errors'] == expected

        parser = RequestParser()
        parser.add_argument('bar', required=True, location=['values', 'cookies'])

        expected = {
            'bar': ("Missing required parameter in the post body or the query "
            "string or the request's cookies")
        }

        with pytest.raises(BadRequest) as cm:
            parser.parse_args()
        assert cm.value.data['message'] == 'Input payload validation failed'
        assert cm.value.data['errors'] == expected

    @pytest.mark.request_context('/bubble')
    @pytest.mark.options(bundle_errors=True)
    def test_parse_error_bundling(self, app):
        parser = RequestParser()
        parser.add_argument('foo', required=True, location='values')
        parser.add_argument('bar', required=True, location=['values', 'cookies'])

        with pytest.raises(BadRequest) as cm:
            parser.parse_args()

        assert cm.value.data['message'] == 'Input payload validation failed'
        assert cm.value.data['errors'] == {
            'foo': 'Missing required parameter in the post body or the query string',
            'bar': ("Missing required parameter in the post body or the query string "
                    "or the request's cookies")
        }

    @pytest.mark.request_context('/bubble')
    @pytest.mark.options(bundle_errors=False)
    def test_parse_error_bundling_w_parser_arg(self, app):
        parser = RequestParser(bundle_errors=True)
        parser.add_argument('foo', required=True, location='values')
        parser.add_argument('bar', required=True, location=['values', 'cookies'])

        with pytest.raises(BadRequest) as cm:
            parser.parse_args()

        assert cm.value.data['message'] == 'Input payload validation failed'
        assert cm.value.data['errors'] == {
            'foo': 'Missing required parameter in the post body or the query string',
            'bar': ("Missing required parameter in the post body or the query string "
                    "or the request's cookies")
        }

    @pytest.mark.request_context('/bubble')
    def test_parse_default_append(self):
        parser = RequestParser()
        parser.add_argument('foo', default='bar', action='append',
                            store_missing=True)

        args = parser.parse_args()

        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble')
    def test_parse_default(self):
        parser = RequestParser()
        parser.add_argument('foo', default='bar', store_missing=True)

        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble')
    def test_parse_callable_default(self):
        parser = RequestParser()
        parser.add_argument('foo', default=lambda: 'bar', store_missing=True)

        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble?foo=bar')
    def test_parse(self):
        parser = RequestParser()
        parser.add_argument('foo'),

        args = parser.parse_args()
        assert args['foo'] == 'bar'

    @pytest.mark.request_context('/bubble')
    def test_parse_none(self):
        parser = RequestParser()
        parser.add_argument('foo')

        args = parser.parse_args()
        assert args['foo'] is None

    def test_parse_store_missing(self, app):
        req = Request.from_values('/bubble')

        parser = RequestParser()
        parser.add_argument('foo', store_missing=False)

        args = parser.parse_args(req)
        assert 'foo' not in args

    def test_parse_choices_correct(self, app):
        req = Request.from_values('/bubble?foo=bat')

        parser = RequestParser()
        parser.add_argument('foo', choices=['bat']),

        args = parser.parse_args(req)
        assert args['foo'] == 'bat'

    def test_parse_choices(self, app):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo', choices=['bat']),

        with pytest.raises(BadRequest):
            parser.parse_args(req)

    def test_parse_choices_sensitive(self, app):
        req = Request.from_values('/bubble?foo=BAT')

        parser = RequestParser()
        parser.add_argument('foo', choices=['bat'], case_sensitive=True),

        with pytest.raises(BadRequest):
            parser.parse_args(req)

    def test_parse_choices_insensitive(self, app):
        req = Request.from_values('/bubble?foo=BAT')

        parser = RequestParser()
        parser.add_argument('foo', choices=['bat'], case_sensitive=False),

        args = parser.parse_args(req)
        assert 'bat' == args.get('foo')

        # both choices and args are case_insensitive
        req = Request.from_values('/bubble?foo=bat')

        parser = RequestParser()
        parser.add_argument('foo', choices=['BAT'], case_sensitive=False),

        args = parser.parse_args(req)
        assert 'bat' == args.get('foo')

    def test_parse_ignore(self, app):
        req = Request.from_values('/bubble?foo=bar')

        parser = RequestParser()
        parser.add_argument('foo', type=int, ignore=True, store_missing=True),

        args = parser.parse_args(req)
        assert args['foo'] is None

    def test_chaining(self):
        parser = RequestParser()
        assert parser is parser.add_argument('foo')

    def test_result_existence(self):
        result = ParseResult()
        result.foo = 'bar'
        result['bar'] = 'baz'
        assert result['foo'] == 'bar'
        assert result.bar == 'baz'

    def test_result_missing(self):
        result = ParseResult()
        pytest.raises(AttributeError, lambda: result.spam)
        pytest.raises(KeyError, lambda: result['eggs'])

    def test_result_configurability(self):
        req = Request.from_values()
        assert isinstance(RequestParser().parse_args(req), ParseResult)
        assert type(RequestParser(result_class=dict).parse_args(req)) is dict

    def test_none_argument(self, app):
        parser = RequestParser()
        parser.add_argument('foo', location='json')
        with app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': None}),
                                      content_type='application/json'):
            args = parser.parse_args()
        assert args['foo'] is None

    def test_type_callable(self, app):
        req = Request.from_values('/bubble?foo=1')

        parser = RequestParser()
        parser.add_argument('foo', type=lambda x: x, required=False),

        args = parser.parse_args(req)
        assert args['foo'] == '1'

    def test_type_callable_none(self, app):
        parser = RequestParser()
        parser.add_argument('foo', type=lambda x: x, location='json', required=False),

        with app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': None}),
                                      content_type='application/json'):
            args = parser.parse_args()
            assert args['foo'] is None

    def test_type_decimal(self, app):
        parser = RequestParser()
        parser.add_argument('foo', type=decimal.Decimal, location='json')

        with app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': '1.0025'}),
                                      content_type='application/json'):
            args = parser.parse_args()
            assert args['foo'] == decimal.Decimal('1.0025')

    def test_type_filestorage(self, app):
        parser = RequestParser()
        parser.add_argument('foo', type=FileStorage, location='files')

        fdata = 'foo bar baz qux'.encode('utf-8')
        with app.test_request_context('/bubble', method='POST',
                                      data={'foo': (six.BytesIO(fdata), 'baz.txt')}):
            args = parser.parse_args()

            assert args['foo'].name == 'foo'
            assert args['foo'].filename == 'baz.txt'
            assert args['foo'].read() == fdata

    def test_filestorage_custom_type(self, app):
        def _custom_type(f):
            return FileStorage(stream=f.stream,
                               filename='{0}aaaa'.format(f.filename),
                               name='{0}aaaa'.format(f.name))

        parser = RequestParser()
        parser.add_argument('foo', type=_custom_type, location='files')

        fdata = 'foo bar baz qux'.encode('utf-8')
        with app.test_request_context('/bubble', method='POST',
                                      data={'foo': (six.BytesIO(fdata), 'baz.txt')}):
            args = parser.parse_args()

            assert args['foo'].name == 'fooaaaa'
            assert args['foo'].filename == 'baz.txtaaaa'
            assert args['foo'].read() == fdata

    def test_passing_arguments_object(self, app):
        req = Request.from_values('/bubble?foo=bar')
        parser = RequestParser()
        parser.add_argument(Argument('foo'))

        args = parser.parse_args(req)
        assert args['foo'] == 'bar'

    def test_int_choice_types(self, app):
        parser = RequestParser()
        parser.add_argument('foo', type=int, choices=[1, 2, 3], location='json')

        with app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': 5}),
                                      content_type='application/json'):
            with pytest.raises(BadRequest):
                parser.parse_args()

    def test_int_range_choice_types(self, app):
        parser = RequestParser()
        parser.add_argument('foo', type=int, choices=range(100), location='json')

        with app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': 101}),
                                      content_type='application/json'):
            with pytest.raises(BadRequest):
                parser.parse_args()

    def test_request_parser_copy(self, app):
        req = Request.from_values('/bubble?foo=101&bar=baz')
        parser = RequestParser()
        foo_arg = Argument('foo', type=int)
        parser.args.append(foo_arg)
        parser_copy = parser.copy()

        # Deepcopy should create a clone of the argument object instead of
        # copying a reference to the new args list
        assert foo_arg not in parser_copy.args

        # Args added to new parser should not be added to the original
        bar_arg = Argument('bar')
        parser_copy.args.append(bar_arg)
        assert bar_arg not in parser.args

        args = parser_copy.parse_args(req)
        assert args['foo'] == 101
        assert args['bar'] == 'baz'

    def test_request_parse_copy_including_settings(self):
        parser = RequestParser(trim=True, bundle_errors=True)
        parser_copy = parser.copy()

        assert parser.trim == parser_copy.trim
        assert parser.bundle_errors == parser_copy.bundle_errors

    def test_request_parser_replace_argument(self, app):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        parser_copy = parser.copy()
        parser_copy.replace_argument('foo')

        args = parser_copy.parse_args(req)
        assert args['foo'] == 'baz'

    def test_both_json_and_values_location(self, app):
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        parser.add_argument('baz', type=int)
        with app.test_request_context('/bubble?foo=1', method='post',
                                      data=json.dumps({'baz': 2}),
                                      content_type='application/json'):
            args = parser.parse_args()
            assert args['foo'] == 1
            assert args['baz'] == 2

    def test_not_json_location_and_content_type_json(self, app):
        parser = RequestParser()
        parser.add_argument('foo', location='args')

        with app.test_request_context('/bubble', method='get',
                                      content_type='application/json'):
            parser.parse_args()  # Should not raise a 400: BadRequest

    def test_request_parser_remove_argument(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        parser_copy = parser.copy()
        parser_copy.remove_argument('foo')

        args = parser_copy.parse_args(req)
        assert args == {}

    def test_strict_parsing_off(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        args = parser.parse_args(req)
        assert args == {}

    def test_strict_parsing_on(self):
        req = Request.from_values('/bubble?foo=baz')
        parser = RequestParser()
        with pytest.raises(BadRequest):
            parser.parse_args(req, strict=True)

    def test_strict_parsing_off_partial_hit(self, app):
        req = Request.from_values('/bubble?foo=1&bar=bees&n=22')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        args = parser.parse_args(req)
        assert args['foo'] == 1

    def test_strict_parsing_on_partial_hit(self, app):
        req = Request.from_values('/bubble?foo=1&bar=bees&n=22')
        parser = RequestParser()
        parser.add_argument('foo', type=int)
        with pytest.raises(BadRequest):
            parser.parse_args(req, strict=True)

    def test_trim_argument(self, app):
        req = Request.from_values('/bubble?foo= 1 &bar=bees&n=22')
        parser = RequestParser()
        parser.add_argument('foo')
        args = parser.parse_args(req)
        assert args['foo'] == ' 1 '

        parser = RequestParser()
        parser.add_argument('foo', trim=True)
        args = parser.parse_args(req)
        assert args['foo'] == '1'

        parser = RequestParser()
        parser.add_argument('foo', trim=True, type=int)
        args = parser.parse_args(req)
        assert args['foo'] == 1

    def test_trim_request_parser(self, app):
        req = Request.from_values('/bubble?foo= 1 &bar=bees&n=22')
        parser = RequestParser(trim=False)
        parser.add_argument('foo')
        args = parser.parse_args(req)
        assert args['foo'] == ' 1 '

        parser = RequestParser(trim=True)
        parser.add_argument('foo')
        args = parser.parse_args(req)
        assert args['foo'] == '1'

        parser = RequestParser(trim=True)
        parser.add_argument('foo', type=int)
        args = parser.parse_args(req)
        assert args['foo'] == 1

    def test_trim_request_parser_override_by_argument(self):
        parser = RequestParser(trim=True)
        parser.add_argument('foo', trim=False)

        assert parser.args[0].trim is False

    def test_trim_request_parser_json(self, app):
        parser = RequestParser(trim=True)
        parser.add_argument('foo', location='json')
        parser.add_argument('int1', location='json', type=int)
        parser.add_argument('int2', location='json', type=int)

        with app.test_request_context('/bubble', method='post',
                                      data=json.dumps({'foo': ' bar ', 'int1': 1, 'int2': ' 2 '}),
                                      content_type='application/json'):
            args = parser.parse_args()
        assert args['foo'] == 'bar'
        assert args['int1'] == 1
        assert args['int2'] == 2


class ArgumentTest(object):
    def test_name(self):
        arg = Argument('foo')
        assert arg.name == 'foo'

    def test_dest(self):
        arg = Argument('foo', dest='foobar')
        assert arg.dest == 'foobar'

    def test_location_url(self):
        arg = Argument('foo', location='url')
        assert arg.location == 'url'

    def test_location_url_list(self):
        arg = Argument('foo', location=['url'])
        assert arg.location == ['url']

    def test_location_header(self):
        arg = Argument('foo', location='headers')
        assert arg.location == 'headers'

    def test_location_json(self):
        arg = Argument('foo', location='json')
        assert arg.location == 'json'

    def test_location_get_json(self):
        arg = Argument('foo', location='get_json')
        assert arg.location == 'get_json'

    def test_location_header_list(self):
        arg = Argument('foo', location=['headers'])
        assert arg.location == ['headers']

    def test_type(self):
        arg = Argument('foo', type=int)
        assert arg.type == int

    def test_default(self):
        arg = Argument('foo', default=True)
        assert arg.default is True

    def test_default_help(self):
        arg = Argument('foo')
        assert arg.help is None

    def test_required(self):
        arg = Argument('foo', required=True)
        assert arg.required is True

    def test_ignore(self):
        arg = Argument('foo', ignore=True)
        assert arg.ignore is True

    def test_operator(self):
        arg = Argument('foo', operators=['>=', '<=', '='])
        assert arg.operators == ['>=', '<=', '=']

    def test_action_filter(self):
        arg = Argument('foo', action='filter')
        assert arg.action == 'filter'

    def test_action(self):
        arg = Argument('foo', action='append')
        assert arg.action == 'append'

    def test_choices(self):
        arg = Argument('foo', choices=[1, 2])
        assert arg.choices == [1, 2]

    def test_default_dest(self):
        arg = Argument('foo')
        assert arg.dest is None

    def test_default_operators(self):
        arg = Argument('foo')
        assert arg.operators[0] == '='
        assert len(arg.operators) == 1

    def test_default_type(self, mocker):
        mock_six = mocker.patch('flask_restplus.reqparse.six')
        arg = Argument('foo')
        sentinel = object()
        arg.type(sentinel)
        mock_six.text_type.assert_called_with(sentinel)

    def test_default_default(self):
        arg = Argument('foo')
        assert arg.default is None

    def test_required_default(self):
        arg = Argument('foo')
        assert arg.required is False

    def test_ignore_default(self):
        arg = Argument('foo')
        assert arg.ignore is False

    def test_action_default(self):
        arg = Argument('foo')
        assert arg.action == 'store'

    def test_choices_default(self):
        arg = Argument('foo')
        assert len(arg.choices) == 0

    def test_source(self, mocker):
        req = mocker.Mock(['args', 'headers', 'values'])
        req.args = {'foo': 'bar'}
        req.headers = {'baz': 'bat'}
        arg = Argument('foo', location=['args'])
        assert arg.source(req) == MultiDict(req.args)

        arg = Argument('foo', location=['headers'])
        assert arg.source(req) == MultiDict(req.headers)

    def test_convert_default_type_with_null_input(self):
        arg = Argument('foo')
        assert arg.convert(None, None) is None

    def test_convert_with_null_input_when_not_nullable(self):
        arg = Argument('foo', nullable=False)
        pytest.raises(ValueError, lambda: arg.convert(None, None))

    def test_source_bad_location(self, mocker):
        req = mocker.Mock(['values'])
        arg = Argument('foo', location=['foo'])
        assert len(arg.source(req)) == 0  # yes, basically you don't find it

    def test_source_default_location(self, mocker):
        req = mocker.Mock(['values'])
        req._get_child_mock = lambda **kwargs: MultiDict()
        arg = Argument('foo')
        assert arg.source(req) == req.values

    def test_option_case_sensitive(self):
        arg = Argument('foo', choices=['bar', 'baz'], case_sensitive=True)
        assert arg.case_sensitive is True

        # Insensitive
        arg = Argument('foo', choices=['bar', 'baz'], case_sensitive=False)
        assert arg.case_sensitive is False

        # Default
        arg = Argument('foo', choices=['bar', 'baz'])
        assert arg.case_sensitive is True


class RequestParserSchemaTest(object):
    def test_empty_parser(self):
        parser = RequestParser()
        assert parser.__schema__ == []

    def test_primitive_types(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, help='Some integer')
        parser.add_argument('str', type=str, help='Some string')
        parser.add_argument('float', type=float, help='Some float')

        assert parser.__schema__ == [
            {
                "description": "Some integer",
                "type": "integer",
                "name": "int",
                "in": "query"
            }, {
                "description": "Some string",
                "type": "string",
                "name": "str",
                "in": "query"
            }, {
                "description": "Some float",
                "type": "number",
                "name": "float",
                "in": "query"
            }
        ]

    def test_unknown_type(self):
        parser = RequestParser()
        parser.add_argument('unknown', type=lambda v: v)
        assert parser.__schema__ == [{
            'name': 'unknown',
            'type': 'string',
            'in': 'query',
        }]

    def test_required(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, required=True)
        assert parser.__schema__ == [{
            'name': 'int',
            'type': 'integer',
            'in': 'query',
            'required': True,
        }]

    def test_default(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, default=5)
        assert parser.__schema__ == [{
            'name': 'int',
            'type': 'integer',
            'in': 'query',
            'default': 5,
        }]

    def test_default_as_false(self):
        parser = RequestParser()
        parser.add_argument('bool', type=inputs.boolean, default=False)
        assert parser.__schema__ == [{
            'name': 'bool',
            'type': 'boolean',
            'in': 'query',
            'default': False,
        }]

    def test_choices(self):
        parser = RequestParser()
        parser.add_argument('string', type=str, choices=['a', 'b'])
        assert parser.__schema__ == [{
            'name': 'string',
            'type': 'string',
            'in': 'query',
            'enum': ['a', 'b'],
            'collectionFormat': 'multi',
        }]

    def test_location(self):
        parser = RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_values', type=int, location='values')
        parser.add_argument('in_query', type=int, location='args')
        parser.add_argument('in_headers', type=int, location='headers')
        parser.add_argument('in_cookie', type=int, location='cookie')
        assert parser.__schema__ == [{
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
        }]

    def test_location_json(self):
        parser = RequestParser()
        parser.add_argument('in_json', type=str, location='json')
        assert parser.__schema__ == [{
            'name': 'in_json',
            'type': 'string',
            'in': 'body',
        }]

    def test_location_form(self):
        parser = RequestParser()
        parser.add_argument('in_form', type=int, location='form')
        assert parser.__schema__ == [{
            'name': 'in_form',
            'type': 'integer',
            'in': 'formData',
        }]

    def test_location_files(self):
        parser = RequestParser()
        parser.add_argument('in_files', type=FileStorage, location='files')
        assert parser.__schema__ == [{
            'name': 'in_files',
            'type': 'file',
            'in': 'formData',
        }]

    def test_form_and_body_location(self):
        parser = RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_form', type=int, location='form')
        parser.add_argument('in_json', type=str, location='json')
        with pytest.raises(SpecsError) as cm:
            parser.__schema__

        assert cm.value.msg == "Can't use formData and body at the same time"

    def test_files_and_body_location(self):
        parser = RequestParser()
        parser.add_argument('default', type=int)
        parser.add_argument('in_files', type=FileStorage, location='files')
        parser.add_argument('in_json', type=str, location='json')
        with pytest.raises(SpecsError) as cm:
            parser.__schema__

        assert cm.value.msg == "Can't use formData and body at the same time"

    def test_models(self):
        todo_fields = Model('Todo', {
            'task': fields.String(required=True, description='The task details')
        })
        parser = RequestParser()
        parser.add_argument('todo', type=todo_fields)
        assert parser.__schema__ == [{
            'name': 'todo',
            'type': 'Todo',
            'in': 'body',
        }]

    def test_lists(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, action='append')
        assert parser.__schema__ == [{
            'name': 'int',
            'in': 'query',
            'type': 'array',
            'collectionFormat': 'multi',
            'items': {'type': 'integer'}
        }]

    def test_split_lists(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, action='split')
        assert parser.__schema__ == [{
            'name': 'int',
            'in': 'query',
            'type': 'array',
            'collectionFormat': 'csv',
            'items': {'type': 'integer'}
        }]

    def test_schema_interface(self):
        def custom(value):
            pass

        custom.__schema__ = {
            'type': 'string',
            'format': 'custom-format',
        }

        parser = RequestParser()
        parser.add_argument('custom', type=custom)

        assert parser.__schema__ == [{
            'name': 'custom',
            'in': 'query',
            'type': 'string',
            'format': 'custom-format',
        }]

    def test_callable_default(self):
        parser = RequestParser()
        parser.add_argument('int', type=int, default=lambda: 5)
        assert parser.__schema__ == [{
            'name': 'int',
            'type': 'integer',
            'in': 'query',
            'default': 5,
        }]
