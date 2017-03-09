# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import pytz
import pytest

from datetime import date, datetime
from six import text_type

from flask_restplus import inputs


class Iso8601DateTest(object):
    @pytest.mark.parametrize('value,expected', [
        ('2011-01-01', date(2011, 1, 1)),
        ('2011-01-01T00:00:00+00:00', date(2011, 1, 1)),
        ('2011-01-01T23:59:59+00:00', date(2011, 1, 1)),
        ('2011-01-01T23:59:59.001000+00:00', date(2011, 1, 1)),
        ('2011-01-01T23:59:59+02:00', date(2011, 1, 1)),
    ])
    def test_valid_values(self, value, expected):
        assert inputs.date_from_iso8601(value) == expected

    def test_error(self):
        with pytest.raises(ValueError):
            inputs.date_from_iso8601('2008-13-13')

    def test_schema(self):
        assert inputs.date_from_iso8601.__schema__ == {'type': 'string', 'format': 'date'}


class Iso8601DatetimeTest(object):
    @pytest.mark.parametrize('value,expected', [
        ('2011-01-01', datetime(2011, 1, 1)),
        ('2011-01-01T00:00:00+00:00', datetime(2011, 1, 1, tzinfo=pytz.utc)),
        ('2011-01-01T23:59:59+00:00', datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc)),
        ('2011-01-01T23:59:59.001000+00:00', datetime(2011, 1, 1, 23, 59, 59, 1000, tzinfo=pytz.utc)),
        ('2011-01-01T23:59:59+02:00', datetime(2011, 1, 1, 21, 59, 59, tzinfo=pytz.utc)),
    ])
    def test_valid_values(self, value, expected):
        assert inputs.datetime_from_iso8601(value) == expected

    def test_error(self):
        with pytest.raises(ValueError):
            inputs.datetime_from_iso8601('2008-13-13')

    def test_schema(self):
        assert inputs.datetime_from_iso8601.__schema__ == {'type': 'string', 'format': 'date-time'}


class Rfc822DatetimeTest(object):
    @pytest.mark.parametrize('value,expected', [
        ('Sat, 01 Jan 2011', datetime(2011, 1, 1, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 00:00', datetime(2011, 1, 1, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 00:00:00', datetime(2011, 1, 1, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 00:00:00 +0000', datetime(2011, 1, 1, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 00:00:00 -0000', datetime(2011, 1, 1, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 23:59:59 -0000', datetime(2011, 1, 1, 23, 59, 59, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 21:00:00 +0200', datetime(2011, 1, 1, 19, 0, 0, tzinfo=pytz.utc)),
        ('Sat, 01 Jan 2011 21:00:00 -0200', datetime(2011, 1, 1, 23, 0, 0, tzinfo=pytz.utc)),
    ])
    def test_valid_values(self, value, expected):
        assert inputs.datetime_from_rfc822(value) == expected

    def test_error(self):
        with pytest.raises(ValueError):
            inputs.datetime_from_rfc822('Fake, 01 XXX 2011')


class NetlocRegexpTest(object):
    @pytest.mark.parametrize('netloc,kwargs', [
        ('localhost', {'localhost': 'localhost'}),
        ('example.com', {'domain': 'example.com'}),
        ('www.example.com', {'domain': 'www.example.com'}),
        ('www.example.com:8000', {'domain': 'www.example.com', 'port': '8000'}),
        ('valid-with-hyphens.com', {'domain': 'valid-with-hyphens.com'}),
        ('subdomain.example.com', {'domain': 'subdomain.example.com'}),
        ('200.8.9.10', {'ipv4': '200.8.9.10'}),
        ('200.8.9.10:8000', {'ipv4': '200.8.9.10', 'port': '8000'}),
        ('valid-----hyphens.com', {'domain': 'valid-----hyphens.com'}),
        ('foo:bar@example.com', {'auth': 'foo:bar', 'domain': 'example.com'}),
        ('foo:@example.com', {'auth': 'foo:', 'domain': 'example.com'}),
        ('foo@example.com', {'auth': 'foo', 'domain': 'example.com'}),
        ('foo:@2001:db8:85a3::8a2e:370:7334', {'auth': 'foo:', 'ipv6': '2001:db8:85a3::8a2e:370:7334'}),
        ('[1fff:0:a88:85a3::ac1f]:8001', {'ipv6': '1fff:0:a88:85a3::ac1f', 'port': '8001'}),
        ('foo2:qd1%r@example.com', {'auth': 'foo2:qd1%r', 'domain': 'example.com'}),
    ])
    def test_match(self, netloc, kwargs):
        match = inputs.netloc_regex.match(netloc)
        assert match, 'Should match {0}'.format(netloc)
        expected = {'auth': None, 'domain': None, 'ipv4': None, 'ipv6': None, 'localhost': None, 'port': None}
        expected.update(kwargs)
        assert match.groupdict() == expected


class URLTest(object):
    def assert_bad_url(self, validator, value, details=None):
        msg = '{0} is not a valid URL'
        with pytest.raises(ValueError) as cm:
            validator(value)
        if details:
            assert text_type(cm.value) == '. '.join((msg, details)).format(value)
        else:
            assert text_type(cm.value).startswith(msg.format(value))

    @pytest.mark.parametrize('url', [
        'http://www.djangoproject.com/',
        'http://example.com/',
        'http://www.example.com/',
        'http://www.example.com/test',
        'http://valid-with-hyphens.com/',
        'http://subdomain.example.com/',
        'http://valid-----hyphens.com/',
        'http://example.com?something=value',
        'http://example.com/index.php?something=value&another=value2',
    ])
    def test_valid_values_default(self, url):
        validator = inputs.URL()
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
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
        'http://300:300:300:300',
        'http://example.com:70000',
        'http://example.com:0000',
    ])
    def test_bad_urls(self, url):
        # Test with everything enabled to ensure bad URL are really detected
        validator = inputs.URL(ip=True, auth=True, port=True)
        self.assert_bad_url(validator, url)
        # msg = '{0} is not a valid URL'.format(url)
        # with pytest.raises(ValueError) as cm:
        #     validator(url)
        # assert text_type(cm.exception).startswith(msg)

    @pytest.mark.parametrize('url', [
        'google.com',
        'domain.google.com',
        'kevin:pass@google.com/path?query',
        'google.com/path?\u2713',
    ])
    def test_bad_urls_with_suggestion(self, url):
        validator = inputs.URL()
        self.assert_bad_url(validator, url, 'Did you mean: http://{0}')

    @pytest.mark.parametrize('url', [
        'http://200.8.9.10/',
        'http://foo:bar@200.8.9.10/',
        'http://200.8.9.10:8000/test',
        'http://2001:db8:85a3::8a2e:370:7334',
        'http://[1fff:0:a88:85a3::ac1f]:8001'
    ])
    def test_reject_ip(self, url):
        validator = inputs.URL()
        self.assert_bad_url(validator, url, 'IP is not allowed')

    @pytest.mark.parametrize('url', [
        'http://200.8.9.10/',
        'http://200.8.9.10/test',
        'http://2001:db8:85a3::8a2e:370:7334',
        'http://[1fff:0:a88:85a3::ac1f]',
    ])
    def test_allow_ip(self, url):
        validator = inputs.URL(ip=True)
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'http://foo:bar@200.8.9.10/',
        'http://foo:@2001:db8:85a3::8a2e:370:7334',
        'http://foo:bar@[1fff:0:a88:85a3::ac1f]:8001',
        'http://foo:@2001:db8:85a3::8a2e:370:7334',
        'http://foo2:qd1%r@example.com',
    ])
    def test_reject_auth(self, url):
        # Test with IP and port to ensure only auth is rejected
        validator = inputs.URL(ip=True, port=True)
        self.assert_bad_url(validator, url, 'Authentication is not allowed')

    @pytest.mark.parametrize('url', [
        'http://foo:bar@example.com',
        'http://foo:@example.com',
        'http://foo@example.com',
    ])
    def test_allow_auth(self, url):
        validator = inputs.URL(auth=True)
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'http://localhost',
        'http://127.0.0.1',
        'http://127.0.1.1',
        'http://::1',
    ])
    def test_reject_local(self, url):
        # Test with IP and port to ensure only auth is rejected
        validator = inputs.URL(ip=True)
        self.assert_bad_url(validator, url, 'Localhost is not allowed')

    @pytest.mark.parametrize('url', [
        'http://localhost',
        'http://127.0.0.1',
        'http://127.0.1.1',
        'http://::1',
    ])
    def test_allow_local(self, url):
        validator = inputs.URL(ip=True, local=True)
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'http://200.8.9.10:8080/',
        'http://foo:bar@200.8.9.10:8080/',
        'http://foo:bar@[1fff:0:a88:85a3::ac1f]:8001'
    ])
    def test_reject_port(self, url):
        # Test with auth and port to ensure only port is rejected
        validator = inputs.URL(ip=True, auth=True)
        self.assert_bad_url(validator, url, 'Custom port is not allowed')

    @pytest.mark.parametrize('url', [
        'http://example.com:80',
        'http://example.com:8080',
        'http://www.example.com:8000/test',
    ])
    def test_allow_port(self, url):
        validator = inputs.URL(port=True)
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'sip://somewhere.com',
        'irc://somewhere.com',
    ])
    def test_valid_restricted_schemes(self, url):
        validator = inputs.URL(schemes=('sip', 'irc'))
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'http://somewhere.com',
        'https://somewhere.com',
    ])
    def test_invalid_restricted_schemes(self, url):
        validator = inputs.URL(schemes=('sip', 'irc'))
        self.assert_bad_url(validator, url, 'Protocol is not allowed')

    @pytest.mark.parametrize('url', [
        'http://example.com',
        'http://example.com/test/',
        'http://www.example.com/',
        'http://www.example.com/test',
    ])
    def test_valid_restricted_domains(self, url):
        validator = inputs.URL(domains=['example.com', 'www.example.com'])
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'http://somewhere.com',
        'https://somewhere.com',
    ])
    def test_invalid_restricted_domains(self, url):
        validator = inputs.URL(domains=['example.com', 'www.example.com'])
        self.assert_bad_url(validator, url, 'Domain is not allowed')

    @pytest.mark.parametrize('url', [
        'http://somewhere.com',
        'https://somewhere.com',
    ])
    def test_valid_excluded_domains(self, url):
        validator = inputs.URL(exclude=['example.com', 'www.example.com'])
        assert validator(url) == url

    @pytest.mark.parametrize('url', [
        'http://example.com',
        'http://example.com/test/',
        'http://www.example.com/',
        'http://www.example.com/test',
    ])
    def test_excluded_domains(self, url):
        validator = inputs.URL(exclude=['example.com', 'www.example.com'])
        self.assert_bad_url(validator, url, 'Domain is not allowed')

    def test_check(self):
        validator = inputs.URL(check=True, ip=True)
        assert validator('http://www.google.com') == 'http://www.google.com', 'Should check domain'

        # This test will fail on a network where this address is defined
        self.assert_bad_url(validator, 'http://this-domain-should-not-exist.com', 'Domain does not exists')

    def test_schema(self):
        assert inputs.URL().__schema__ == {'type': 'string', 'format': 'url'}


class UrlTest(object):
    @pytest.mark.parametrize('url', [
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
        'http://foo@example.com',
        'http://foo:@2001:db8:85a3::8a2e:370:7334',
        'http://foo2:qd1%r@example.com',
    ])
    def test_valid_url(self, url):
        assert inputs.url(url) == url

    @pytest.mark.parametrize('url', [
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
        'http://300:300:300:300',
        'http://example.com:70000',
    ])
    def test_bad_url(self, url):
        with pytest.raises(ValueError) as cm:
            inputs.url(url)
        assert text_type(cm.value).startswith('{0} is not a valid URL'.format(url))

    @pytest.mark.parametrize('url', [
        'google.com',
        'domain.google.com',
        'kevin:pass@google.com/path?query',
        'google.com/path?\u2713',
    ])
    def test_bad_url_with_suggestion(self, url):
        with pytest.raises(ValueError) as cm:
            inputs.url(url)
        assert text_type(cm.value) == '{0} is not a valid URL. Did you mean: http://{0}'.format(url)

    def test_schema(self):
        assert inputs.url.__schema__ == {'type': 'string', 'format': 'url'}


class IPTest(object):
    @pytest.mark.parametrize('value', [
        '200.8.9.10',
        '127.0.0.1',
        '2001:db8:85a3::8a2e:370:7334',
        '::1',
    ])
    def test_valid_value(self, value):
        assert inputs.ip(value) == value

    @pytest.mark.parametrize('value', [
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
        '127.0'
    ])
    def test_bad_value(self, value):
        with pytest.raises(ValueError):
            inputs.ip(value)

    def test_schema(self):
        assert inputs.ip.__schema__ == {'type': 'string', 'format': 'ip'}


class IPv4Test(object):
    @pytest.mark.parametrize('value', [
        '200.8.9.10',
        '127.0.0.1',
    ])
    def test_valid_value(self, value):
        assert inputs.ipv4(value) == value

    @pytest.mark.parametrize('value', [
        '2001:db8:85a3::8a2e:370:7334',
        '::1',
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
        '127.0'
    ])
    def test_bad_value(self, value):
        with pytest.raises(ValueError):
            inputs.ipv4(value)

    def test_schema(self):
        assert inputs.ipv4.__schema__ == {'type': 'string', 'format': 'ipv4'}


class IPv6Test(object):
    @pytest.mark.parametrize('value', [
        '2001:db8:85a3::8a2e:370:7334',
        '::1',
    ])
    def test_valid_value(self, value):
        assert inputs.ipv6(value) == value

    @pytest.mark.parametrize('value', [
        '200.8.9.10',
        '127.0.0.1',
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
        '127.0'
    ])
    def test_bad_value(self, value):
        with pytest.raises(ValueError):
            inputs.ipv6(value)

    def test_schema(self):
        assert inputs.ipv6.__schema__ == {'type': 'string', 'format': 'ipv6'}


class EmailTest(object):

    def assert_bad_email(self, validator, value, msg=None):
        msg = msg or '{0} is not a valid email'
        with pytest.raises(ValueError) as cm:
            validator(value)
        assert str(cm.value) == msg.format(value)

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'coucou@cmoi.fr',
        'coucou+another@cmoi.fr',
        'Coucou@cmoi.fr',
        'me@valid-with-hyphens.com',
        'me@subdomain.example.com',
        'me@sub.subdomain.example.com',
        'Loïc.Accentué@voilà.fr',
    ])
    def test_valid_value_default(self, value):
        validator = inputs.email()
        assert validator(value) == value

    @pytest.mark.parametrize('value', [
        'me@localhost',
        'me@127.0.0.1',
        'me@127.1.2.3',
        'me@::1',
        'me@200.8.9.10',
        'me@2001:db8:85a3::8a2e:370:7334',
    ])
    def test_invalid_value_default(self, value):
        self.assert_bad_email(inputs.email(), value)

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'test@live.com',
    ])
    def test_valid_value_check(self, value):
        email = inputs.email(check=True)
        assert email(value) == value

    @pytest.mark.parametrize('value', [
        'coucou@not-found.fr',
        'me@localhost',
        'me@127.0.0.1',
        'me@127.1.2.3',
        'me@::1',
        'me@200.8.9.10',
        'me@2001:db8:85a3::8a2e:370:7334',
    ])
    def test_invalid_values_check(self, value):
        email = inputs.email(check=True)
        self.assert_bad_email(email, value)

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'coucou@cmoi.fr',
        'coucou+another@cmoi.fr',
        'Coucou@cmoi.fr',
        'me@valid-with-hyphens.com',
        'me@subdomain.example.com',
        'me@200.8.9.10',
        'me@2001:db8:85a3::8a2e:370:7334',
    ])
    def test_valid_value_ip(self, value):
        email = inputs.email(ip=True)
        assert email(value) == value

    @pytest.mark.parametrize('value', [
        'me@localhost',
        'me@127.0.0.1',
        'me@127.1.2.3',
        'me@::1',
    ])
    def test_invalid_value_ip(self, value):
        email = inputs.email(ip=True)
        self.assert_bad_email(email, value)

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'coucou@cmoi.fr',
        'coucou+another@cmoi.fr',
        'Coucou@cmoi.fr',
        'coucou@localhost',
        'me@valid-with-hyphens.com',
        'me@subdomain.example.com',
        'me@localhost',
    ])
    def test_valid_value_local(self, value):
        email = inputs.email(local=True)
        assert email(value) == value

    @pytest.mark.parametrize('value', [
        'me@127.0.0.1',
        'me@127.1.2.3',
        'me@::1',
        'me@200.8.9.10',
        'me@2001:db8:85a3::8a2e:370:7334',
    ])
    def test_invalid_value_local(self, value):
        email = inputs.email(local=True)
        self.assert_bad_email(email, value)

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'coucou@cmoi.fr',
        'coucou+another@cmoi.fr',
        'Coucou@cmoi.fr',
        'coucou@localhost',
        'me@valid-with-hyphens.com',
        'me@subdomain.example.com',
        'me@200.8.9.10',
        'me@2001:db8:85a3::8a2e:370:7334',
        'me@localhost',
        'me@127.0.0.1',
        'me@127.1.2.3',
        'me@::1',
    ])
    def test_valid_value_ip_and_local(self, value):
        email = inputs.email(ip=True, local=True)
        assert email(value) == value

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'coucou@cmoi.fr',
        'coucou+another@cmoi.fr',
        'Coucou@cmoi.fr',
    ])
    def test_valid_value_domains(self, value):
        email = inputs.email(domains=('gmail.com', 'cmoi.fr'))
        assert email(value) == value

    @pytest.mark.parametrize('value', [
        'me@valid-with-hyphens.com',
        'me@subdomain.example.com',
        'me@localhost',
        'me@127.0.0.1',
        'me@127.1.2.3',
        'me@::1',
        'me@200.8.9.10',
        'me@2001:db8:85a3::8a2e:370:7334',
    ])
    def test_invalid_value_domains(self, value):
        email = inputs.email(domains=('gmail.com', 'cmoi.fr'))
        self.assert_bad_email(email, value, '{0} does not belong to the authorized domains')

    @pytest.mark.parametrize('value', [
        'test@gmail.com',
        'coucou@cmoi.fr',
        'coucou+another@cmoi.fr',
        'Coucou@cmoi.fr',
    ])
    def test_valid_value_exclude(self, value):
        email = inputs.email(exclude=('somewhere.com', 'foo.bar'))
        assert email(value) == value

    @pytest.mark.parametrize('value', [
        'me@somewhere.com',
        'me@foo.bar',
    ])
    def test_invalid_value_exclude(self, value):
        email = inputs.email(exclude=('somewhere.com', 'foo.bar'))
        self.assert_bad_email(email, value, '{0} belongs to a forbidden domain')

    @pytest.mark.parametrize('value', [
        'someone@',
        '@somewhere',
        'email.somewhere.com',
        '[invalid!email]',
        'me.@somewhere',
        'me..something@somewhere',
    ])
    def test_bad_email(self, value):
        email = inputs.email()
        self.assert_bad_email(email, value)

    def test_schema(self):
        assert inputs.email().__schema__ == {'type': 'string', 'format': 'email'}


class RegexTest(object):
    @pytest.mark.parametrize('value', [
        '123',
        '1234567890',
        '00000',
    ])
    def test_valid_input(self, value):
        num_only = inputs.regex(r'^[0-9]+$')
        assert num_only(value) == value

    @pytest.mark.parametrize('value', [
        'abc',
        '123abc',
        'abc123',
        '',
    ])
    def test_bad_input(self, value):
        num_only = inputs.regex(r'^[0-9]+$')
        with pytest.raises(ValueError):
            num_only(value)

    def test_bad_pattern(self):
        with pytest.raises(re.error):
            inputs.regex('[')

    def test_schema(self):
        assert inputs.regex(r'^[0-9]+$').__schema__ == {'type': 'string', 'pattern': '^[0-9]+$'}


class BooleanTest(object):
    def test_false(self):
        assert inputs.boolean('False') is False

    def test_0(self):
        assert inputs.boolean('0') is False

    def test_true(self):
        assert inputs.boolean('true') is True

    def test_1(self):
        assert inputs.boolean('1') is True

    def test_case(self):
        assert inputs.boolean('FaLSE') is False
        assert inputs.boolean('FaLSE') is False

    def test_python_bool(self):
        assert inputs.boolean(True) is True
        assert inputs.boolean(False) is False

    def test_bad_boolean(self):
        with pytest.raises(ValueError):
            inputs.boolean('blah')

    def test_schema(self):
        assert inputs.boolean.__schema__ == {'type': 'boolean'}


class DateTest(object):
    def test_later_than_1900(self):
        assert inputs.date('1900-01-01') == datetime(1900, 1, 1)

    def test_error(self):
        with pytest.raises(ValueError):
            inputs.date('2008-13-13')

    def test_default(self):
        assert inputs.date('2008-08-01') == datetime(2008, 8, 1)

    def test_schema(self):
        assert inputs.date.__schema__ == {'type': 'string', 'format': 'date'}


class NaturalTest(object):
    def test_negative(self):
        with pytest.raises(ValueError):
            inputs.natural(-1)

    def test_default(self):
        assert inputs.natural(3) == 3

    def test_string(self):
        with pytest.raises(ValueError):
            inputs.natural('foo')

    def test_schema(self):
        assert inputs.natural.__schema__ == {'type': 'integer', 'minimum': 0}


class PositiveTest(object):
    def test_positive(self):
        assert inputs.positive(1) == 1
        assert inputs.positive(10000) == 10000

    def test_zero(self):
        with pytest.raises(ValueError):
            inputs.positive(0)

    def test_negative(self):
        with pytest.raises(ValueError):
            inputs.positive(-1)

    def test_schema(self):
        assert inputs.positive.__schema__ == {'type': 'integer', 'minimum': 0, 'exclusiveMinimum': True}


class IntRangeTest(object):
    def test_valid_range(self):
        int_range = inputs.int_range(1, 5)
        assert int_range(3) == 3

    def test_inclusive_range(self):
        int_range = inputs.int_range(1, 5)
        assert int_range(5) == 5

    def test_lower(self):
        int_range = inputs.int_range(0, 5)
        with pytest.raises(ValueError):
            int_range(-1)

    def test_higher(self):
        int_range = inputs.int_range(0, 5)
        with pytest.raises(ValueError):
            int_range(6)

    def test_schema(self):
        assert inputs.int_range(1, 5).__schema__ == {'type': 'integer', 'minimum': 1, 'maximum': 5}


interval_test_values = [(
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
), (  # Resolution expansion for single date(time)
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


class IsoIntervalTest(object):
    @pytest.mark.parametrize('value,expected', interval_test_values)
    def test_valid_value(self, value, expected):
        assert inputs.iso8601interval(value) == expected

    def test_error_message(self):
        with pytest.raises(ValueError) as cm:
            inputs.iso8601interval('2013-01-01/blah')
        expected = 'Invalid argument: 2013-01-01/blah. argument must be a valid ISO8601 date/time interval.'
        assert str(cm.value) == expected

    @pytest.mark.parametrize('value', [
        '2013-01T14:',
        '',
        'asdf',
        '01/01/2013',
    ])
    def test_bad_values(self, value):
        with pytest.raises(ValueError):
            inputs.iso8601interval(value)

    def test_schema(self):
        assert inputs.iso8601interval.__schema__ == {'type': 'string', 'format': 'iso8601-interval'}
