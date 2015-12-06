# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from datetime import date, datetime

import pytz

from six import text_type

from flask_restplus import inputs

from . import assert_equal, assert_raises


class InputTest(object):
    def assert_values(self, input, values):
        for value, expected in values:
            yield assert_equal, input(value), expected

    def assert_values_raises(self, input, values, error):
        for value in values:
            yield assert_raises, error, lambda: input(value)


class Rfc822DatetimeTest(InputTest):
    def test_valid_values(self):
        values = [
            ('Sat, 01 Jan 2011', datetime(2011, 1, 1, tzinfo=pytz.utc)),
            ('Sat, 01 Jan 2011 00:00:00 -0000', datetime(2011, 1, 1, tzinfo=pytz.utc)),
            ('Sat, 01 Jan 2011 23:59:59 -0000', datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc)),
            ('Sat, 01 Jan 2011 21:59:59 -0200', datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc)),
        ]
        self.assert_values(inputs.datetime_from_rfc822, values)

    def test_error(self):
        with assert_raises(ValueError):
            inputs.datetime_from_rfc822('Fake, 01 Jan 2011')


class Iso8601DatetimeTest(InputTest):
    def test_valid_values(self):
        values = [
            ('2011-01-01', datetime(2011, 1, 1, tzinfo=pytz.utc)),
            ('2011-01-01T00:00:00+00:00', datetime(2011, 1, 1, tzinfo=pytz.utc)),
            ('2011-01-01T23:59:59+00:00', datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc)),
            ('2011-01-01T23:59:59.001000+00:00', datetime(2011, 1, 1, 23, 59, 59, 1000, tzinfo=pytz.utc)),
            ('2011-01-01T23:59:59+02:00', datetime(2011, 1, 1, 21, 59, 59, tzinfo=pytz.utc)),
        ]
        self.assert_values(inputs.datetime_from_iso8601, values)

    def test_error(self):
        with assert_raises(ValueError):
            inputs.datetime_from_iso8601('2008-13-13')


class Rfc822DateTest(InputTest):
    def test_valid_values(self):
        values = [
            ('Sat, 01 Jan 2011', date(2011, 1, 1)),
            ('Sat, 01 Jan 2011 00:00:00 -0000', date(2011, 1, 1)),
            ('Sat, 01 Jan 2011 23:59:59 -0000', date(2011, 1, 1)),
            ('Sat, 01 Jan 2011 21:59:59 -0200', date(2011, 1, 1)),
        ]
        self.assert_values(inputs.date_from_rfc822, values)

    def test_error(self):
        with assert_raises(ValueError):
            inputs.date_from_rfc822('Fake, 01 Jan 2011')


class Iso8601DateTest(InputTest):
    def test_valid_values(self):
        values = [
            ('2011-01-01', date(2011, 1, 1)),
            ('2011-01-01T00:00:00+00:00', date(2011, 1, 1)),
            ('2011-01-01T23:59:59+00:00', date(2011, 1, 1)),
            ('2011-01-01T23:59:59.001000+00:00', date(2011, 1, 1)),
            ('2011-01-01T23:59:59+02:00', date(2011, 1, 1)),
        ]
        self.assert_values(inputs.date_from_iso8601, values)

    def test_error(self):
        with assert_raises(ValueError):
            inputs.date_from_iso8601('2008-13-13')


class UrlTest(InputTest):
    def test_valid_values(self):
        urls = [
            'http://www.djangoproject.com/',
            'http://localhost/',
            'http://example.com/',
            'http://www.example.com/',
            'http://www.example.com:8000/test',
            'http://valid-with-hyphens.com/',
            'http://subdomain.example.com/',
            'http://200.8.9.10/',
            'http://200.8.9.10:8000/test',
            'http://valid-----hyphens.com/',
            'http://example.com?something=value',
            'http://example.com/index.php?something=value&another=value2',
            'http://foo:bar@example.com',
            'http://foo:@example.com',
            'http://foo:@2001:db8:85a3::8a2e:370:7334',
            'http://foo2:qd1%r@example.com',
        ]
        self.assert_values(inputs.url, zip(urls, urls))

    def assert_bad_url(self, value):
        with assert_raises(ValueError) as cm:
            inputs.url(value)
        assert_equal(text_type(cm.exception), '{0} is not a valid URL'.format(value))

    def test_bad_urls(self):
        urls = [
            'foo',
            'http://',
            'http://example',
            'http://example.',
            'http://.com',
            'http://invalid-.com',
            'http://-invalid.com',
            'http://inv-.alid-.com',
            'http://inv-.-alid.com',
            'foo bar baz',
            'foo \u2713',
            'http://@foo:bar@example.com',
            'http://:bar@example.com',
            'http://bar:bar:bar@example.com',
        ]

        for url in urls:
            yield self.assert_bad_url, url

    def assert_bad_url_with_suggestion(self, value):
        with assert_raises(ValueError) as cm:
            inputs.url(value)
        assert_equal(text_type(cm.exception),
                     '{0} is not a valid URL. Did you mean: http://{0}'.format(value))

    def test_bad_urls_with_suggestion(self):
        urls = [
            'google.com',
            'domain.google.com',
            'kevin:pass@google.com/path?query',
            'google.com/path?\u2713',
        ]
        for url in urls:
            yield self.assert_bad_url_with_suggestion, url


class RegexTest(InputTest):
    def test_valid_input(self):
        values = (
            '123',
            '1234567890',
            '00000',
        )

        num_only = inputs.regex(r'^[0-9]+$')

        self.assert_values(num_only, values)

    def test_bad_input(self):
        values = (
            'abc',
            '123abc',
            'abc123',
            '',
        )

        num_only = inputs.regex(r'^[0-9]+$')

        self.assert_values_raises(num_only, values, ValueError)

    def test_bad_pattern(self):
        assert_raises(re.error, inputs.regex, '[')


class BooleanTest(InputTest):
    def test_false(self):
        assert_equal(inputs.boolean('False'), False)

    def test_0(self):
        assert_equal(inputs.boolean('0'), False)

    def test_true(self):
        assert_equal(inputs.boolean('true'), True)

    def test_1(self):
        assert_equal(inputs.boolean('1'), True)

    def test_case(self):
        assert_equal(inputs.boolean('FaLSE'), False)
        assert_equal(inputs.boolean('FaLSE'), False)

    def test_python_bool(self):
        assert_equal(inputs.boolean(True), True)
        assert_equal(inputs.boolean(False), False)

    def test_bad_boolean(self):
        with assert_raises(ValueError):
            inputs.boolean('blah')


class DateTest(InputTest):
    def test_later_than_1900(self):
        assert_equal(inputs.date('1900-01-01'), datetime(1900, 1, 1))

    def test_error(self):
        with assert_raises(ValueError):
            inputs.date('2008-13-13')

    def test_default(self):
        assert_equal(inputs.date('2008-08-01'), datetime(2008, 8, 1))


class Natural(InputTest):
    def test_negative(self):
        with assert_raises(ValueError):
            inputs.natural(-1)

    def test_default(self):
        assert_equal(3, inputs.natural(3))

    def test_string(self):
        with assert_raises(ValueError):
            inputs.natural('foo')


class PositiveTest(InputTest):
    def test_positive(self):
        assert_equal(1, inputs.positive(1))
        assert_equal(10000, inputs.positive(10000))

    def test_zero(self):
        with assert_raises(ValueError):
            inputs.positive(0)

    def test_negative(self):
        with assert_raises(ValueError):
            inputs.positive(-1)


class IntRangeTest(InputTest):
    def test_valid_range(self):
        int_range = inputs.int_range(1, 5)
        assert_equal(3, int_range(3))

    def test_inclusive_range(self):
        int_range = inputs.int_range(1, 5)
        assert_equal(5, int_range(5))

    def test_lower(self):
        int_range = inputs.int_range(0, 5)
        with assert_raises(ValueError):
            int_range(-1)

    def test_higher(self):
        int_range = inputs.int_range(0, 5)
        with assert_raises(ValueError):
            int_range(6)


class IsoIntervalTest(InputTest):
    def test_valid_values(self):
        values = [(
            # Full precision with explicit UTC.
            '2013-01-01T12:30:00Z/P1Y2M3DT4H5M6S',
            (
                datetime(2013, 1, 1, 12, 30, 0, tzinfo=pytz.utc),
                datetime(2014, 3, 5, 16, 35, 6, tzinfo=pytz.utc),
            ),
        ), (
            # Full precision with alternate UTC indication
            '2013-01-01T12:30+00:00/P2D',
            (
                datetime(2013, 1, 1, 12, 30, 0, tzinfo=pytz.utc),
                datetime(2013, 1, 3, 12, 30, 0, tzinfo=pytz.utc),
            ),
        ), (
            # Implicit UTC with time
            '2013-01-01T15:00/P1M',
            (
                datetime(2013, 1, 1, 15, 0, 0, tzinfo=pytz.utc),
                datetime(2013, 1, 31, 15, 0, 0, tzinfo=pytz.utc),
            ),
        ), (
            # TZ conversion
            '2013-01-01T17:00-05:00/P2W',
            (
                datetime(2013, 1, 1, 22, 0, 0, tzinfo=pytz.utc),
                datetime(2013, 1, 15, 22, 0, 0, tzinfo=pytz.utc),
            ),
        ), (
            # Date upgrade to midnight-midnight period
            '2013-01-01/P3D',
            (
                datetime(2013, 1, 1, 0, 0, 0, tzinfo=pytz.utc),
                datetime(2013, 1, 4, 0, 0, 0, 0, tzinfo=pytz.utc),
            ),
        ), (
            # Start/end with UTC
            '2013-01-01T12:00:00Z/2013-02-01T12:00:00Z',
            (
                datetime(2013, 1, 1, 12, 0, 0, tzinfo=pytz.utc),
                datetime(2013, 2, 1, 12, 0, 0, tzinfo=pytz.utc),
            ),
        ), (
            # Start/end with time upgrade
            '2013-01-01/2013-06-30',
            (
                datetime(2013, 1, 1, tzinfo=pytz.utc),
                datetime(2013, 6, 30, tzinfo=pytz.utc),
            ),
        ), (
            # Start/end with TZ conversion
            '2013-02-17T12:00:00-07:00/2013-02-28T15:00:00-07:00',
            (
                datetime(2013, 2, 17, 19, 0, 0, tzinfo=pytz.utc),
                datetime(2013, 2, 28, 22, 0, 0, tzinfo=pytz.utc),
            ),
        ),
        # Resolution expansion for single date(time)
        (
            # Second with UTC
            '2013-01-01T12:30:45Z',
            (
                datetime(2013, 1, 1, 12, 30, 45, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 12, 30, 46, tzinfo=pytz.utc),
            ),
        ), (
            # Second with tz conversion
            '2013-01-01T12:30:45+02:00',
            (
                datetime(2013, 1, 1, 10, 30, 45, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 10, 30, 46, tzinfo=pytz.utc),
            ),
        ), (
            # Second with implicit UTC
            '2013-01-01T12:30:45',
            (
                datetime(2013, 1, 1, 12, 30, 45, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 12, 30, 46, tzinfo=pytz.utc),
            ),
        ), (
            # Minute with UTC
            '2013-01-01T12:30+00:00',
            (
                datetime(2013, 1, 1, 12, 30, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 12, 31, tzinfo=pytz.utc),
            ),
        ), (
            # Minute with conversion
            '2013-01-01T12:30+04:00',
            (
                datetime(2013, 1, 1, 8, 30, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 8, 31, tzinfo=pytz.utc),
            ),
        ), (
            # Minute with implicit UTC
            '2013-01-01T12:30',
            (
                datetime(2013, 1, 1, 12, 30, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 12, 31, tzinfo=pytz.utc),
            ),
        ), (
            # Hour, explicit UTC
            '2013-01-01T12Z',
            (
                datetime(2013, 1, 1, 12, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 13, tzinfo=pytz.utc),
            ),
        ), (
            # Hour with offset
            '2013-01-01T12-07:00',
            (
                datetime(2013, 1, 1, 19, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 20, tzinfo=pytz.utc),
            ),
        ), (
            # Hour with implicit UTC
            '2013-01-01T12',
            (
                datetime(2013, 1, 1, 12, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 13, tzinfo=pytz.utc),
            ),
        ), (
            # Interval with trailing zero fractional seconds should
            # be accepted.
            '2013-01-01T12:00:00.0/2013-01-01T12:30:00.000000',
            (
                datetime(2013, 1, 1, 12, tzinfo=pytz.utc),
                datetime(2013, 1, 1, 12, 30, tzinfo=pytz.utc),
            ),
        )]

        self.assert_values(inputs.iso8601interval, values)

    def test_error_message(self):
        with assert_raises(ValueError) as cm:
            inputs.iso8601interval('2013-01-01/blah')
        expected = 'Invalid argument: 2013-01-01/blah. argument must be a valid ISO8601 date/time interval.'
        assert_equal(str(cm.exception), expected)

    def test_bad_values(self):
        values = [
            '2013-01T14:',
            '',
            'asdf',
            '01/01/2013',
        ]
        self.assert_values_raises(inputs.iso8601interval, values, ValueError)
