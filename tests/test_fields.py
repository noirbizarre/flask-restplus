# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal
from functools import partial

import pytz
import pytest

from flask import Blueprint
from flask_restplus import fields, Api


class FieldTestCase(object):
    field_class = None

    @pytest.fixture
    def api(self, app):
        blueprint = Blueprint('api', __name__)
        api = Api(blueprint)
        app.register_blueprint(blueprint)
        yield api

    def assert_field(self, field, value, expected):
        assert field.output('foo', {'foo': value}) == expected

    def assert_field_raises(self, field, value):
        with pytest.raises(fields.MarshallingError):
            field.output('foo', {'foo': value})


class BaseFieldTestMixin(object):
    def test_description(self):
        field = self.field_class(description='A description')
        assert 'description' in field.__schema__
        assert field.__schema__['description'] == 'A description'

    def test_title(self):
        field = self.field_class(title='A title')
        assert 'title' in field.__schema__
        assert field.__schema__['title'] == 'A title'

    def test_required(self):
        field = self.field_class(required=True)
        assert field.required

    def test_readonly(self):
        field = self.field_class(readonly=True)
        assert 'readOnly' in field.__schema__
        assert field.__schema__['readOnly']


class NumberTestMixin(object):
    def test_min(self):
        field = self.field_class(min=0)
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == 0
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_as_callable(self):
        field = self.field_class(min=lambda: 0)
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == 0

    def test_min_exlusive(self):
        field = self.field_class(min=0, exclusiveMin=True)
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == 0
        assert 'exclusiveMinimum' in field.__schema__
        assert field.__schema__['exclusiveMinimum'] is True

    def test_max(self):
        field = self.field_class(max=42)
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == 42
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_as_callable(self):
        field = self.field_class(max=lambda: 42)
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == 42

    def test_max_exclusive(self):
        field = self.field_class(max=42, exclusiveMax=True)
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == 42
        assert 'exclusiveMaximum' in field.__schema__
        assert field.__schema__['exclusiveMaximum'] is True

    def test_mulitple_of(self):
        field = self.field_class(multiple=5)
        assert 'multipleOf' in field.__schema__
        assert field.__schema__['multipleOf'] == 5


class StringTestMixin(object):
    def test_min_length(self):
        field = self.field_class(min_length=1)
        assert 'minLength' in field.__schema__
        assert field.__schema__['minLength'] == 1

    def test_min_length_as_callable(self):
        field = self.field_class(min_length=lambda: 1)
        assert 'minLength' in field.__schema__
        assert field.__schema__['minLength'] == 1

    def test_max_length(self):
        field = self.field_class(max_length=42)
        assert 'maxLength' in field.__schema__
        assert field.__schema__['maxLength'] == 42

    def test_max_length_as_callable(self):
        field = self.field_class(max_length=lambda: 42)
        assert 'maxLength' in field.__schema__
        assert field.__schema__['maxLength'] == 42

    def test_pattern(self):
        field = self.field_class(pattern='[a-z]')
        assert 'pattern' in field.__schema__
        assert field.__schema__['pattern'] == '[a-z]'


class RawFieldTest(BaseFieldTestMixin, FieldTestCase):
    ''' Test Raw field AND some common behaviors'''
    field_class = fields.Raw

    def test_type(self):
        field = fields.Raw()
        assert field.__schema__['type'] == 'object'

    def test_default(self):
        field = fields.Raw(default='aaa')
        assert field.__schema__['default'] == 'aaa'
        self.assert_field(field, None, 'aaa')

    def test_default_as_callable(self):
        field = fields.Raw(default=lambda: 'aaa')
        assert field.__schema__['default'] == 'aaa'
        self.assert_field(field, None, 'aaa')

    def test_with_attribute(self):
        field = fields.Raw(attribute='bar')
        assert field.output('foo', {'bar': 42}) == 42

    def test_with_lambda_attribute(self, mocker):
        obj = mocker.Mock()
        obj.value = 42
        field = fields.Raw(attribute=lambda x: x.value)
        assert field.output('foo', obj) == 42

    def test_with_partial_attribute(self, mocker):
        def f(x, suffix):
            return '{0}-{1}'.format(x.value, suffix)

        obj = mocker.Mock()
        obj.value = 42

        p = partial(f, suffix='whatever')
        field = fields.Raw(attribute=p)
        assert field.output('foo', obj) == '42-whatever'

    def test_attribute_not_found(self):
        field = fields.Raw()
        assert field.output('foo', {'bar': 42}) is None

    def test_object(self, mocker):
        obj = mocker.Mock()
        obj.foo = 42
        field = fields.Raw()
        assert field.output('foo', obj) == 42

    def test_nested_object(self, mocker):
        foo = mocker.Mock()
        bar = mocker.Mock()
        bar.value = 42
        foo.bar = bar
        field = fields.Raw()
        assert field.output('bar.value', foo) == 42


class StringFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = fields.String

    def test_defaults(self):
        field = fields.String()
        assert not field.required
        assert not field.discriminator
        assert field.__schema__ == {'type': 'string'}

    def test_with_enum(self):
        enum = ['A', 'B', 'C']
        field = fields.String(enum=enum)
        assert not field.required
        assert field.__schema__ == {'type': 'string', 'enum': enum, 'example': enum[0]}

    def test_with_empty_enum(self):
        field = fields.String(enum=[])
        assert not field.required
        assert field.__schema__ == {'type': 'string'}

    def test_with_callable_enum(self):
        enum = lambda: ['A', 'B', 'C']  # noqa
        field = fields.String(enum=enum)
        assert not field.required
        assert field.__schema__ == {'type': 'string', 'enum': ['A', 'B', 'C'], 'example': 'A'}

    def test_with_empty_callable_enum(self):
        enum = lambda: []  # noqa
        field = fields.String(enum=enum)
        assert not field.required
        assert field.__schema__ == {'type': 'string'}

    def test_with_default(self):
        field = fields.String(default='aaa')
        assert field.__schema__ == {'type': 'string', 'default': 'aaa'}

    def test_string_field_with_discriminator(self):
        field = fields.String(discriminator=True)
        assert field.discriminator
        assert field.required
        assert field.__schema__ == {'type': 'string'}

    def test_string_field_with_discriminator_override_require(self):
        field = fields.String(discriminator=True, required=False)
        assert field.discriminator
        assert field.required
        assert field.__schema__ == {'type': 'string'}

    def test_discriminator_output(self, api):
        model = api.model('Test', {
            'name': fields.String(discriminator=True),
        })

        data = api.marshal({}, model)
        assert data == {'name': 'Test'}

    def test_multiple_discriminator_field(self, api):
        model = api.model('Test', {
            'name': fields.String(discriminator=True),
            'name2': fields.String(discriminator=True),
        })

        with pytest.raises(ValueError):
            api.marshal(object(), model)

    @pytest.mark.parametrize('value,expected', [
        ('string', 'string'),
        (42, '42'),
    ])
    def test_values(self, value, expected):
        self.assert_field(fields.String(), value, expected)


class IntegerFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Integer

    def test_defaults(self):
        field = fields.Integer()
        assert not field.required
        assert field.__schema__ == {'type': 'integer'}

    def test_with_default(self):
        field = fields.Integer(default=42)
        assert not field.required
        assert field.__schema__ == {'type': 'integer', 'default': 42}
        self.assert_field(field, None, 42)

    @pytest.mark.parametrize('value,expected', [
        (0, 0),
        (42, 42),
        ('42', 42),
        (None, None),
        (66.6, 66),
    ])
    def test_value(self, value, expected):
        self.assert_field(fields.Integer(), value, expected)

    def test_decode_error(self):
        field = fields.Integer()
        self.assert_field_raises(field, 'an int')


class BooleanFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = fields.Boolean

    def test_defaults(self):
        field = fields.Boolean()
        assert not field.required
        assert field.__schema__ == {'type': 'boolean'}

    def test_with_default(self):
        field = fields.Boolean(default=True)
        assert not field.required
        assert field.__schema__ == {'type': 'boolean', 'default': True}

    @pytest.mark.parametrize('value,expected', [
        (True, True),
        (False, False),
        ({}, False),
        ('false', False),  # These consistent with inputs.boolean
        ('0', False),
    ])
    def test_value(self, value, expected):
        self.assert_field(fields.Boolean(), value, expected)


class FloatFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Float

    def test_defaults(self):
        field = fields.Float()
        assert not field.required
        assert field.__schema__ == {'type': 'number'}

    def test_with_default(self):
        field = fields.Float(default=0.5)
        assert not field.required
        assert field.__schema__ == {'type': 'number', 'default': 0.5}

    @pytest.mark.parametrize('value,expected', [
        ('-3.13', -3.13),
        (str(-3.13), -3.13),
        (3, 3.0),
    ])
    def test_value(self, value, expected):
        self.assert_field(fields.Float(), value, expected)

    def test_raises(self):
        self.assert_field_raises(fields.Float(), 'bar')

    def test_decode_error(self):
        field = fields.Float()
        self.assert_field_raises(field, 'not a float')


PI_STR = ('3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117'
          '06798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493'
          '038196442881097566593344612847564823378678316527120190914564856692346034861')

PI = Decimal(PI_STR)


class FixedFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Fixed

    def test_defaults(self):
        field = fields.Fixed()
        assert not field.required
        assert field.__schema__ == {'type': 'number'}

    def test_with_default(self):
        field = fields.Fixed(default=0.5)
        assert not field.required
        assert field.__schema__ == {'type': 'number', 'default': 0.5}

    def test_fixed(self):
        field5 = fields.Fixed(5)
        field4 = fields.Fixed(4)

        self.assert_field(field5, PI, '3.14159')
        self.assert_field(field4, PI, '3.1416')
        self.assert_field(field4, 3, '3.0000')
        self.assert_field(field4, '03', '3.0000')
        self.assert_field(field4, '03.0', '3.0000')

    def test_zero(self):
        self.assert_field(fields.Fixed(), '0', '0.00000')

    def test_infinite(self):
        field = fields.Fixed()
        self.assert_field_raises(field, '+inf')
        self.assert_field_raises(field, '-inf')

    def test_nan(self):
        field = fields.Fixed()
        self.assert_field_raises(field, 'NaN')


class ArbitraryFieldTest(BaseFieldTestMixin, NumberTestMixin, FieldTestCase):
    field_class = fields.Arbitrary

    def test_defaults(self):
        field = fields.Arbitrary()
        assert not field.required
        assert field.__schema__ == {'type': 'number'}

    def test_with_default(self):
        field = fields.Arbitrary(default=0.5)
        assert field.__schema__ == {'type': 'number', 'default': 0.5}

    @pytest.mark.parametrize('value,expected', [
        (PI_STR, PI_STR),
        (PI, PI_STR),
    ])
    def test_value(self, value, expected):
        self.assert_field(fields.Arbitrary(), value, expected)


class DatetimeFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = fields.DateTime

    def test_defaults(self):
        field = fields.DateTime()
        assert not field.required
        assert field.__schema__ == {'type': 'string', 'format': 'date-time'}
        self.assert_field(field, None, None)

    def test_with_default(self):
        field = fields.DateTime(default='2014-08-25')
        assert field.__schema__ == {'type': 'string', 'format': 'date-time', 'default': '2014-08-25T00:00:00'}
        self.assert_field(field, None, '2014-08-25T00:00:00')

    def test_with_default_as_datetime(self):
        field = fields.DateTime(default=datetime(2014, 8, 25))
        assert field.__schema__ == {'type': 'string', 'format': 'date-time', 'default': '2014-08-25T00:00:00'}
        self.assert_field(field, None, '2014-08-25T00:00:00')

    def test_with_default_as_date(self):
        field = fields.DateTime(default=date(2014, 8, 25))
        assert field.__schema__ == {'type': 'string', 'format': 'date-time', 'default': '2014-08-25T00:00:00'}
        self.assert_field(field, None, '2014-08-25T00:00:00')

    def test_min(self):
        field = fields.DateTime(min='1984-06-07T00:00:00')
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07T00:00:00'
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_as_date(self):
        field = fields.DateTime(min=date(1984, 6, 7))
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07T00:00:00'
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_as_datetime(self):
        field = fields.DateTime(min=datetime(1984, 6, 7, 1, 2, 0))
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07T01:02:00'
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_exlusive(self):
        field = fields.DateTime(min='1984-06-07T00:00:00', exclusiveMin=True)
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07T00:00:00'
        assert 'exclusiveMinimum' in field.__schema__
        assert field.__schema__['exclusiveMinimum'] is True

    def test_max(self):
        field = fields.DateTime(max='1984-06-07T00:00:00')
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07T00:00:00'
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_as_date(self):
        field = fields.DateTime(max=date(1984, 6, 7))
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07T00:00:00'
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_as_datetime(self):
        field = fields.DateTime(max=datetime(1984, 6, 7, 1, 2, 0))
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07T01:02:00'
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_exclusive(self):
        field = fields.DateTime(max='1984-06-07T00:00:00', exclusiveMax=True)
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07T00:00:00'
        assert 'exclusiveMaximum' in field.__schema__
        assert field.__schema__['exclusiveMaximum'] is True

    @pytest.mark.parametrize('value,expected', [
        (date(2011, 1, 1), 'Sat, 01 Jan 2011 00:00:00 -0000'),
        (datetime(2011, 1, 1), 'Sat, 01 Jan 2011 00:00:00 -0000'),
        (datetime(2011, 1, 1, 23, 59, 59),
         'Sat, 01 Jan 2011 23:59:59 -0000'),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc),
         'Sat, 01 Jan 2011 23:59:59 -0000'),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.timezone('CET')),
         'Sat, 01 Jan 2011 22:59:59 -0000')
    ])
    def test_rfc822_value(self, value, expected):
        self.assert_field(fields.DateTime(dt_format='rfc822'), value, expected)

    @pytest.mark.parametrize('value,expected', [
        (date(2011, 1, 1), '2011-01-01T00:00:00'),
        (datetime(2011, 1, 1), '2011-01-01T00:00:00'),
        (datetime(2011, 1, 1, 23, 59, 59),
         '2011-01-01T23:59:59'),
        (datetime(2011, 1, 1, 23, 59, 59, 1000),
         '2011-01-01T23:59:59.001000'),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc),
         '2011-01-01T23:59:59+00:00'),
        (datetime(2011, 1, 1, 23, 59, 59, 1000, tzinfo=pytz.utc),
         '2011-01-01T23:59:59.001000+00:00'),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.timezone('CET')),
         '2011-01-01T23:59:59+01:00')
    ])
    def test_iso8601_value(self, value, expected):
        self.assert_field(fields.DateTime(dt_format='iso8601'), value, expected)

    def test_unsupported_format(self):
        field = fields.DateTime(dt_format='raw')
        self.assert_field_raises(field, datetime.now())

    def test_unsupported_value_format(self):
        field = fields.DateTime(dt_format='raw')
        self.assert_field_raises(field, 'xxx')


class DateFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = fields.Date

    def test_defaults(self):
        field = fields.Date()
        assert not field.required
        assert field.__schema__ == {'type': 'string', 'format': 'date'}

    def test_with_default(self):
        field = fields.Date(default='2014-08-25')
        assert field.__schema__ == {'type': 'string', 'format': 'date', 'default': '2014-08-25'}
        self.assert_field(field, None, '2014-08-25')

    def test_with_default_as_date(self):
        field = fields.Date(default=date(2014, 8, 25))
        assert field.__schema__ == {'type': 'string', 'format': 'date', 'default': '2014-08-25'}

    def test_with_default_as_datetime(self):
        field = fields.Date(default=datetime(2014, 8, 25))
        assert field.__schema__ == {'type': 'string', 'format': 'date', 'default': '2014-08-25'}

    def test_min(self):
        field = fields.Date(min='1984-06-07')
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07'
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_as_date(self):
        field = fields.Date(min=date(1984, 6, 7))
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07'
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_as_datetime(self):
        field = fields.Date(min=datetime(1984, 6, 7, 1, 2, 0))
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07'
        assert 'exclusiveMinimum' not in field.__schema__

    def test_min_exlusive(self):
        field = fields.Date(min='1984-06-07', exclusiveMin=True)
        assert 'minimum' in field.__schema__
        assert field.__schema__['minimum'] == '1984-06-07'
        assert 'exclusiveMinimum' in field.__schema__
        assert field.__schema__['exclusiveMinimum'] is True

    def test_max(self):
        field = fields.Date(max='1984-06-07')
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07'
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_as_date(self):
        field = fields.Date(max=date(1984, 6, 7))
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07'
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_as_datetime(self):
        field = fields.Date(max=datetime(1984, 6, 7, 1, 2, 0))
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07'
        assert 'exclusiveMaximum' not in field.__schema__

    def test_max_exclusive(self):
        field = fields.Date(max='1984-06-07', exclusiveMax=True)
        assert 'maximum' in field.__schema__
        assert field.__schema__['maximum'] == '1984-06-07'
        assert 'exclusiveMaximum' in field.__schema__
        assert field.__schema__['exclusiveMaximum'] is True

    @pytest.mark.parametrize('value,expected', [
        (date(2011, 1, 1), '2011-01-01'),
        (datetime(2011, 1, 1), '2011-01-01'),
        (datetime(2011, 1, 1, 23, 59, 59), '2011-01-01'),
        (datetime(2011, 1, 1, 23, 59, 59, 1000), '2011-01-01'),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc), '2011-01-01'),
        (datetime(2011, 1, 1, 23, 59, 59, 1000, tzinfo=pytz.utc), '2011-01-01'),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.timezone('CET')), '2011-01-01')
    ])
    def test_value(self, value, expected):
        self.assert_field(fields.Date(), value, expected)

    def test_unsupported_value_format(self):
        self.assert_field_raises(fields.Date(), 'xxx')


class FormatedStringFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.FormattedString, 'Hello {name}')

    def test_defaults(self):
        field = fields.FormattedString('Hello {name}')
        assert not field.required
        assert field.__schema__ == {'type': 'string'}

    def test_dict(self):
        data = {
            'sid': 3,
            'account_sid': 4,
        }
        field = fields.FormattedString('/foo/{account_sid}/{sid}/')
        assert field.output('foo', data) == '/foo/4/3/'

    def test_object(self, mocker):
        obj = mocker.Mock()
        obj.sid = 3
        obj.account_sid = 4
        field = fields.FormattedString('/foo/{account_sid}/{sid}/')
        assert field.output('foo', obj) == '/foo/4/3/'

    def test_none(self):
        field = fields.FormattedString('{foo}')
        # self.assert_field_raises(field, None)
        with pytest.raises(fields.MarshallingError):
            field.output('foo', None)

    def test_invalid_object(self):
        field = fields.FormattedString('/foo/{0[account_sid]}/{0[sid]}/')
        self.assert_field_raises(field, {})

    def test_tuple(self):
        field = fields.FormattedString('/foo/{0[account_sid]}/{0[sid]}/')
        self.assert_field_raises(field, (3, 4))


class UrlFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.Url, 'endpoint')

    def test_defaults(self):
        field = fields.Url('endpoint')
        assert not field.required
        assert field.__schema__ == {'type': 'string'}

    def test_invalid_object(self, app):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url('foobar')

        with app.test_request_context('/'):
            with pytest.raises(fields.MarshallingError):
                field.output('foo', None)

    def test_simple(self, app, mocker):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url('foobar')
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/'):
            assert '/42' == field.output('foo', obj)

    def test_absolute(self, app, mocker):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url('foobar', absolute=True)
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/'):
            assert 'http://localhost/42' == field.output('foo', obj)

    def test_absolute_scheme(self, app, mocker):
        '''Url.scheme should override current_request.scheme'''
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url('foobar', absolute=True, scheme='https')
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/', base_url='http://localhost'):
            assert 'https://localhost/42' == field.output('foo', obj)

    def test_without_endpoint_invalid_object(self, app):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url()

        with app.test_request_context('/foo'):
            with pytest.raises(fields.MarshallingError):
                field.output('foo', None)

    def test_without_endpoint(self, app, mocker):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url()
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/foo'):
            assert '/42' == field.output('foo', obj)

    def test_without_endpoint_absolute(self, app, mocker):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url(absolute=True)
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/foo'):
            assert 'http://localhost/42' == field.output('foo', obj)

    def test_without_endpoint_absolute_scheme(self, app, mocker):
        app.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        field = fields.Url(absolute=True, scheme='https')
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/foo', base_url='http://localhost'):
            assert 'https://localhost/42' == field.output('foo', obj)

    def test_with_blueprint_invalid_object(self, app):
        bp = Blueprint('foo', __name__, url_prefix='/foo')
        bp.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        app.register_blueprint(bp)
        field = fields.Url()

        with app.test_request_context('/foo/foo'):
            with pytest.raises(fields.MarshallingError):
                field.output('foo', None)

    def test_with_blueprint(self, app, mocker):
        bp = Blueprint('foo', __name__, url_prefix='/foo')
        bp.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        app.register_blueprint(bp)
        field = fields.Url()
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/foo/foo'):
            assert '/foo/42' == field.output('foo', obj)

    def test_with_blueprint_absolute(self, app, mocker):
        bp = Blueprint('foo', __name__, url_prefix='/foo')
        bp.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        app.register_blueprint(bp)
        field = fields.Url(absolute=True)
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/foo/foo'):
            assert 'http://localhost/foo/42' == field.output('foo', obj)

    def test_with_blueprint_absolute_scheme(self, app, mocker):
        bp = Blueprint('foo', __name__, url_prefix='/foo')
        bp.add_url_rule('/<foo>', 'foobar', view_func=lambda x: x)
        app.register_blueprint(bp)
        field = fields.Url(absolute=True, scheme='https')
        obj = mocker.Mock(foo=42)

        with app.test_request_context('/foo/foo', base_url='http://localhost'):
            assert 'https://localhost/foo/42' == field.output('foo', obj)


class NestedFieldTest(FieldTestCase):
    def test_defaults(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields)
        assert not field.required
        assert field.__schema__ == {'$ref': '#/definitions/NestedModel'}

    def test_with_required(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, required=True)
        assert field.required
        assert not field.allow_null
        assert field.__schema__ == {'$ref': '#/definitions/NestedModel'}

    def test_with_description(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, description='A description')
        assert field.__schema__ == {
            'description': 'A description',
            'allOf': [{'$ref': '#/definitions/NestedModel'}]
        }

    def test_with_title(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, title='A title')
        assert field.__schema__ == {
            'title': 'A title',
            'allOf': [{'$ref': '#/definitions/NestedModel'}]
        }

    def test_with_allow_null(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, allow_null=True)
        assert not field.required
        assert field.allow_null
        assert field.__schema__ == {'$ref': '#/definitions/NestedModel'}

    def test_with_skip_none(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, skip_none=True)
        assert not field.required
        assert field.skip_none
        assert field.__schema__ == {'$ref': '#/definitions/NestedModel'}

    def test_with_readonly(self, app):
        api = Api(app)
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, readonly=True)
        assert field.__schema__ == {
            'readOnly': True,
            'allOf': [{'$ref': '#/definitions/NestedModel'}]
        }

    def test_as_list(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.Nested(nested_fields, as_list=True)
        assert field.as_list
        assert field.__schema__ == {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}}

    def test_as_list_is_reusable(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})

        field = fields.Nested(nested_fields, as_list=True)
        assert field.__schema__ == {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}}

        field = fields.Nested(nested_fields)
        assert field.__schema__ == {'$ref': '#/definitions/NestedModel'}


class ListFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.List, fields.String)

    def test_defaults(self):
        field = fields.List(fields.String)
        assert not field.required
        assert field.__schema__ == {'type': 'array', 'items': {'type': 'string'}}

    def test_with_nested_field(self, api):
        nested_fields = api.model('NestedModel', {'name': fields.String})
        field = fields.List(fields.Nested(nested_fields))
        assert field.__schema__ == {'type': 'array', 'items': {'$ref': '#/definitions/NestedModel'}}

        data = [{'name': 'John Doe', 'age': 42}, {'name': 'Jane Doe', 'age': 66}]
        expected = [OrderedDict([('name', 'John Doe')]), OrderedDict([('name', 'Jane Doe')])]
        self.assert_field(field, data, expected)

    def test_min_items(self):
        field = fields.List(fields.String, min_items=5)
        assert 'minItems' in field.__schema__
        assert field.__schema__['minItems'] == 5

    def test_max_items(self):
        field = fields.List(fields.String, max_items=42)
        assert 'maxItems' in field.__schema__
        assert field.__schema__['maxItems'] == 42

    def test_unique(self):
        field = fields.List(fields.String, unique=True)
        assert 'uniqueItems' in field.__schema__
        assert field.__schema__['uniqueItems'] is True

    @pytest.mark.parametrize('value,expected', [
        (['a', 'b', 'c'], ['a', 'b', 'c']),
        (['c', 'b', 'a'], ['c', 'b', 'a']),
        (('a', 'b', 'c'), ['a', 'b', 'c']),
        (['a'], ['a']),
        (None, None),
    ])
    def test_value(self, value, expected):
        self.assert_field(fields.List(fields.String()), value, expected)

    def test_with_set(self):
        field = fields.List(fields.String)
        value = set(['a', 'b', 'c'])
        output = field.output('foo', {'foo': value})
        assert set(output) == value

    def test_with_scoped_attribute_on_dict_or_obj(self):
        class Test(object):
            def __init__(self, data):
                self.data = data

        class Nested(object):
            def __init__(self, value):
                self.value = value

        nesteds = [Nested(i) for i in ['a', 'b', 'c']]
        test_obj = Test(nesteds)
        test_dict = {'data': [{'value': 'a'}, {'value': 'b'}, {'value': 'c'}]}

        field = fields.List(fields.String(attribute='value'), attribute='data')
        assert ['a' == 'b', 'c'], field.output('whatever', test_obj)
        assert ['a' == 'b', 'c'], field.output('whatever', test_dict)

    def test_with_attribute(self):
        data = [{'a': 1, 'b': 1}, {'a': 2, 'b': 1}, {'a': 3, 'b': 1}]
        field = fields.List(fields.Integer(attribute='a'))
        self.assert_field(field, data, [1, 2, 3])

    def test_list_of_raw(self):
        field = fields.List(fields.Raw)

        data = [{'a': 1, 'b': 1}, {'a': 2, 'b': 1}, {'a': 3, 'b': 1}]
        expected = [OrderedDict([('a', 1), ('b', 1)]),
                    OrderedDict([('a', 2), ('b', 1)]),
                    OrderedDict([('a', 3), ('b', 1)])]
        self.assert_field(field, data, expected)

        data = [1, 2, 'a']
        self.assert_field(field, data, data)


class WildcardFieldTest(BaseFieldTestMixin, FieldTestCase):
    field_class = partial(fields.Wildcard, fields.String)

    def test_types(self):
        with pytest.raises(fields.MarshallingError):
            class WrongType:
                pass
            x = WrongType()
            field1 = fields.Wildcard(WrongType)  # noqa
            field2 = fields.Wildcard(x)  # noqa

    def test_defaults(self):
        field = fields.Wildcard(fields.String)
        assert not field.required
        assert field.__schema__ == {'type': 'object', 'additionalProperties': {'type': 'string'}}

    def test_with_scoped_attribute_on_dict_or_obj(self):
        class Test(object):
            def __init__(self, data):
                self.data = data

        class Nested(object):
            def __init__(self, value):
                self.value = value

        nesteds = [Nested(i) for i in ['a', 'b', 'c']]
        test_obj = Test(nesteds)
        test_dict = {'data': [{'value': 'a'}, {'value': 'b'}, {'value': 'c'}]}

        field = fields.Wildcard(fields.String(attribute='value'), attribute='data')
        assert ['a' == 'b', 'c'], field.output('whatever', test_obj)
        assert ['a' == 'b', 'c'], field.output('whatever', test_dict)

    def test_list_of_raw(self):
        field = fields.Wildcard(fields.Raw)

        data = [{'a': 1, 'b': 1}, {'a': 2, 'b': 1}, {'a': 3, 'b': 1}]
        expected = [OrderedDict([('a', 1), ('b', 1)]),
                    OrderedDict([('a', 2), ('b', 1)]),
                    OrderedDict([('a', 3), ('b', 1)])]
        self.assert_field(field, data, expected)

        data = [1, 2, 'a']
        self.assert_field(field, data, data)

    def test_wildcard(self, api):
        wild1 = fields.Wildcard(fields.String)
        wild2 = fields.Wildcard(fields.Integer)
        wild3 = fields.Wildcard(fields.String)
        wild4 = fields.Wildcard(fields.String, default='x')
        wild5 = fields.Wildcard(fields.String)
        wild6 = fields.Wildcard(fields.Integer)
        wild7 = fields.Wildcard(fields.String)
        wild8 = fields.Wildcard(fields.String)

        mod5 = OrderedDict()
        mod5['toto'] = fields.Integer
        mod5['bob'] = fields.Integer
        mod5['*'] = wild5

        wild_fields1 = api.model('WildcardModel1', {'*': wild1})
        wild_fields2 = api.model('WildcardModel2', {'j*': wild2})
        wild_fields3 = api.model('WildcardModel3', {'*': wild3})
        wild_fields4 = api.model('WildcardModel4', {'*': wild4})
        wild_fields5 = api.model('WildcardModel5', mod5)
        wild_fields6 = api.model('WildcardModel6', {
            'nested': {'f1': fields.String(default='12'), 'f2': fields.Integer(default=13)},
            'a*': wild6
        })
        wild_fields7 = api.model('WildcardModel7', {'*': wild7})
        wild_fields8 = api.model('WildcardModel8', {'*': wild8})

        class Dummy(object):
            john = 12
            bob = '42'
            alice = None

        class Dummy2(object):
            pass

        class Dummy3(object):
            a = None
            b = None

        data = {'John': 12, 'bob': 42, 'Jane': '68'}
        data3 = Dummy()
        data4 = Dummy2()
        data5 = {'John': 12, 'bob': 42, 'Jane': '68', 'toto': '72'}
        data6 = {'nested': {'f1': 12, 'f2': 13}, 'alice': '14'}
        data7 = Dummy3()
        data8 = None
        expected1 = {'John': '12', 'bob': '42', 'Jane': '68'}
        expected2 = {'John': 12, 'Jane': 68}
        expected3 = {'john': '12', 'bob': '42'}
        expected4 = {'*': 'x'}
        expected5 = {'John': '12', 'bob': 42, 'Jane': '68', 'toto': 72}
        expected6 = {'nested': {'f1': '12', 'f2': 13}, 'alice': 14}
        expected7 = {}
        expected8 = {}

        result1 = api.marshal(data, wild_fields1)
        result2 = api.marshal(data, wild_fields2)
        result3 = api.marshal(data3, wild_fields3, skip_none=True)
        result4 = api.marshal(data4, wild_fields4)
        result5 = api.marshal(data5, wild_fields5)
        result6 = api.marshal(data6, wild_fields6)
        result7 = api.marshal(data7, wild_fields7, skip_none=True)
        result8 = api.marshal(data8, wild_fields8, skip_none=True)

        assert expected1 == result1
        assert expected2 == result2
        assert expected3 == result3
        assert expected4 == result4
        assert expected5 == result5
        assert expected6 == result6
        assert expected7 == result7
        assert expected8 == result8

    def test_clone(self, api):
        wild1 = fields.Wildcard(fields.String)
        wild2 = wild1.clone()

        wild_fields1 = api.model('cloneWildcard1', {'*': wild1})
        wild_fields2 = api.model('cloneWildcard2', {'*': wild2})

        data = {'John': 12, 'bob': 42, 'Jane': '68'}
        expected1 = {'John': '12', 'bob': '42', 'Jane': '68'}

        result1 = api.marshal(data, wild_fields1)
        result2 = api.marshal(data, wild_fields2)

        assert expected1 == result1
        assert result2 == result1


class ClassNameFieldTest(StringTestMixin, BaseFieldTestMixin, FieldTestCase):
    field_class = fields.ClassName

    def test_simple_string_field(self):
        field = fields.ClassName()
        assert not field.required
        assert not field.discriminator
        assert field.__schema__ == {'type': 'string'}

    def test_default_output_classname(self, api):
        model = api.model('Test', {
            'name': fields.ClassName(),
        })

        class FakeClass(object):
            pass

        data = api.marshal(FakeClass(), model)
        assert data == {'name': 'FakeClass'}

    def test_output_dash(self, api):
        model = api.model('Test', {
            'name': fields.ClassName(dash=True),
        })

        class FakeClass(object):
            pass

        data = api.marshal(FakeClass(), model)
        assert data == {'name': 'fake_class'}

    def test_with_dict(self, api):
        model = api.model('Test', {
            'name': fields.ClassName(),
        })

        data = api.marshal({}, model)
        assert data == {'name': 'object'}


class PolymorphTest(FieldTestCase):
    def test_polymorph_field(self, api):
        parent = api.model('Person', {
            'name': fields.String,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        class Child1(object):
            name = 'child1'
            extra1 = 'extra1'

        class Child2(object):
            name = 'child2'
            extra2 = 'extra2'

        mapping = {
            Child1: child1,
            Child2: child2
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        def data(cls):
            return api.marshal({'owner': cls()}, thing)

        assert data(Child1) == {'owner': {
            'name': 'child1',
            'extra1': 'extra1'
        }}

        assert data(Child2) == {'owner': {
            'name': 'child2',
            'extra2': 'extra2'
        }}

    def test_polymorph_field_no_common_ancestor(self, api):
        child1 = api.model('Child1', {
            'extra1': fields.String,
        })

        child2 = api.model('Child2', {
            'extra2': fields.String,
        })

        class Child1(object):
            pass

        class Child2(object):
            pass

        mapping = {
            Child1: child1,
            Child2: child2
        }

        with pytest.raises(ValueError):
            fields.Polymorph(mapping)

    def test_polymorph_field_unknown_class(self, api):
        parent = api.model('Person', {
            'name': fields.String,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        class Child1(object):
            name = 'child1'
            extra1 = 'extra1'

        class Child2(object):
            name = 'child2'
            extra2 = 'extra2'

        mapping = {
            Child1: child1,
            Child2: child2
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        with pytest.raises(ValueError):
            api.marshal({'owner': object()}, thing)

    def test_polymorph_field_does_not_have_ambiguous_mappings(self, api):
        """
        Regression test for https://github.com/noirbizarre/flask-restplus/pull/691
        """
        parent = api.model('Parent', {
            'name': fields.String,
        })

        child = api.inherit('Child', parent, {
            'extra': fields.String,
        })

        class Parent(object):
            name = 'parent'

        class Child(Parent):
            extra = 'extra'

        mapping = {
            Parent: parent,
            Child: child
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        api.marshal({'owner': Child()}, thing)

    def test_polymorph_field_required_default(self, api):
        parent = api.model('Person', {
            'name': fields.String,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        class Child1(object):
            name = 'child1'
            extra1 = 'extra1'

        class Child2(object):
            name = 'child2'
            extra2 = 'extra2'

        mapping = {
            Child1: child1,
            Child2: child2
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping, required=True, default={'name': 'default'}),
        })

        data = api.marshal({}, thing)

        assert data == {'owner': {
            'name': 'default'
        }}

    def test_polymorph_field_not_required(self, api):
        parent = api.model('Person', {
            'name': fields.String,
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        class Child1(object):
            name = 'child1'
            extra1 = 'extra1'

        class Child2(object):
            name = 'child2'
            extra2 = 'extra2'

        mapping = {
            Child1: child1,
            Child2: child2
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        data = api.marshal({}, thing)

        assert data == {'owner': None}

    def test_polymorph_with_discriminator(self, api):
        parent = api.model('Person', {
            'name': fields.String,
            'model': fields.String(discriminator=True),
        })

        child1 = api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        class Child1(object):
            name = 'child1'
            extra1 = 'extra1'

        class Child2(object):
            name = 'child2'
            extra2 = 'extra2'

        mapping = {
            Child1: child1,
            Child2: child2
        }

        thing = api.model('Thing', {
            'owner': fields.Polymorph(mapping),
        })

        def data(cls):
            return api.marshal({'owner': cls()}, thing)

        assert data(Child1) == {'owner': {
            'name': 'child1',
            'model': 'Child1',
            'extra1': 'extra1'
        }}

        assert data(Child2) == {'owner': {
            'name': 'child2',
            'model': 'Child2',
            'extra2': 'extra2'
        }}


class CustomFieldTest(FieldTestCase):
    def test_custom_field(self):
        class CustomField(fields.Integer):
            __schema_format__ = 'int64'

        field = CustomField()

        assert field.__schema__ == {'type': 'integer', 'format': 'int64'}


class FieldsHelpersTest(object):
    def test_to_dict(self):
        expected = data = {'foo': 42}
        assert fields.to_marshallable_type(data) == expected

    def test_to_dict_obj(self):
        class Foo(object):
            def __init__(self):
                self.foo = 42
        expected = {'foo': 42}
        assert fields.to_marshallable_type(Foo()) == expected

    def test_to_dict_custom_marshal(self):
        class Foo(object):
            def __marshallable__(self):
                return {'foo': 42}
        expected = {'foo': 42}
        assert fields.to_marshallable_type(Foo()) == expected

    def test_get_value(self):
        assert fields.get_value('foo', {'foo': 42}) == 42

    def test_get_value_no_value(self):
        assert fields.get_value("foo", {'foo': 42}) == 42

    def test_get_value_obj(self, mocker):
        assert fields.get_value('foo', mocker.Mock(foo=42)) == 42

    def test_get_value_indexable_object(self):
        class Test(object):
            def __init__(self, value):
                self.value = value

            def __getitem__(self, n):
                if type(n) is int:
                    if n < 3:
                        return n
                    raise IndexError
                raise TypeError

        obj = Test('hi')
        assert fields.get_value('value', obj) == 'hi'
