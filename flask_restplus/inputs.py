# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import socket

from datetime import datetime, time, timedelta
from email.utils import parsedate_tz, mktime_tz

import aniso8601
import pytz

# Constants for upgrading date-based intervals to full datetimes.
START_OF_DAY = time(0, 0, 0, tzinfo=pytz.UTC)
END_OF_DAY = time(23, 59, 59, 999999, tzinfo=pytz.UTC)

url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:[^:@]+?:[^:@]*?@|)'  # basic auth
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
    r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


email_regex = re.compile(
    r'^'
    '(?P<local>[^@]*[^@.])'
    r'@'
    r'(?P<server>[^@]+(?:\.[^@]+)*)'
    r'$', re.IGNORECASE)

time_regex = re.compile(r'\d{2}:\d{2}')


def ipv4(value):
    '''Validate an IPv4 address'''
    try:
        socket.inet_aton(value)
        if value.count('.') == 3:
            return value
    except socket.error:
        pass
    raise ValueError('{0} is not a valid ipv4 address'.format(value))

ipv4.__schema__ = {'type': 'string', 'format': 'ipv4'}


def ipv6(value):
    '''Validate an IPv6 address'''
    try:
        socket.inet_pton(socket.AF_INET6, value)
        return value
    except socket.error:
        raise ValueError('{0} is not a valid ipv4 address'.format(value))

ipv6.__schema__ = {'type': 'string', 'format': 'ipv6'}


def ip(value):
    '''Validate an IP address (both IPv4 and IPv6)'''
    try:
        return ipv4(value)
    except ValueError:
        pass
    try:
        return ipv6(value)
    except ValueError:
        raise ValueError('{0} is not a valid ip'.format(value))

ip.__schema__ = {'type': 'string', 'format': 'ip'}


def url(value):
    '''
    Validate a URL.

    :param value: The URL to validate
    :type value: str
    :returns: The URL if valid.
    :raises: ValueError
    '''
    if not url_regex.search(value):
        message = '{0} is not a valid URL'
        if url_regex.search('http://' + value):
            message += '. Did you mean: http://{0}'
        raise ValueError(message.format(value))
    return value

url.__schema__ = {'type': 'string', 'format': 'url'}


class email(object):
    '''
    Validate an email.

    Example::

        parser = reqparse.RequestParser()
        parser.add_argument('email', type=inputs.email(dns=True))

    Input to the ``email`` argument will be rejected if it does not match an email
    and if domain does not exists.

    :param bool check: Check the domain exists (perform a DNS resolution)
    :param bool ip: Allow IP (both ipv4/ipv6) as domain
    :param bool local: Allow localhost (both string or ip) as domain
    :param list|tuple domains: Restrict valid domains to this list
    :param list|tuple exclude: Exclude some domains
    '''
    def __init__(self, check=False, ip=False, local=False, domains=None, exclude=None):
        self.check = check
        self.ip = ip
        self.local = local
        self.domains = domains
        self.exclude = exclude

    def error(self, value, msg=None):
        msg = msg or '{0} is not a valid email'
        raise ValueError(msg.format(value))

    def is_ip(self, value):
        try:
            ip(value)
            return True
        except ValueError:
            return False

    def __call__(self, value):
        match = email_regex.match(value)
        if not match or '..' in value:
            self.error(value)
        server = match.group('server')
        if self.check:
            try:
                socket.getaddrinfo(server, None)
            except socket.error:
                self.error(value)
        if self.domains and server not in self.domains:
            self.error(value, '{0} does not belong to the authorized domains')
        if self.exclude and server in self.exclude:
            self.error(value, '{0} belongs to a forbidden domain')
        if not self.local and (server in ('localhost', '::1') or server.startswith('127.')):
            self.error(value)
        if self.is_ip(server) and not self.ip:
            self.error(value)
        return value

    @property
    def __schema__(self):
        return {
            'type': 'string',
            'format': 'email',
        }


class regex(object):
    '''
    Validate a string based on a regular expression.

    Example::

        parser = reqparse.RequestParser()
        parser.add_argument('example', type=inputs.regex('^[0-9]+$'))

    Input to the ``example`` argument will be rejected if it contains anything
    but numbers.

    :param str pattern: The regular expression the input must match
    '''

    def __init__(self, pattern):
        self.pattern = pattern
        self.re = re.compile(pattern)

    def __call__(self, value):
        if not self.re.search(value):
            message = 'Value does not match pattern: "{0}"'.format(self.pattern)
            raise ValueError(message)
        return value

    def __deepcopy__(self, memo):
        return regex(self.pattern)

    @property
    def __schema__(self):
        return {
            'type': 'string',
            'pattern': self.pattern,
        }


def _normalize_interval(start, end, value):
    '''
    Normalize datetime intervals.

    Given a pair of datetime.date or datetime.datetime objects,
    returns a 2-tuple of tz-aware UTC datetimes spanning the same interval.

    For datetime.date objects, the returned interval starts at 00:00:00.0
    on the first date and ends at 00:00:00.0 on the second.

    Naive datetimes are upgraded to UTC.

    Timezone-aware datetimes are normalized to the UTC tzdata.

    Params:
        - start: A date or datetime
        - end: A date or datetime
    '''
    if not isinstance(start, datetime):
        start = datetime.combine(start, START_OF_DAY)
        end = datetime.combine(end, START_OF_DAY)

    if start.tzinfo is None:
        start = pytz.UTC.localize(start)
        end = pytz.UTC.localize(end)
    else:
        start = start.astimezone(pytz.UTC)
        end = end.astimezone(pytz.UTC)

    return start, end


def _expand_datetime(start, value):
    if not isinstance(start, datetime):
        # Expand a single date object to be the interval spanning
        # that entire day.
        end = start + timedelta(days=1)
    else:
        # Expand a datetime based on the finest resolution provided
        # in the original input string.
        time = value.split('T')[1]
        time_without_offset = re.sub('[+-].+', '', time)
        num_separators = time_without_offset.count(':')
        if num_separators == 0:
            # Hour resolution
            end = start + timedelta(hours=1)
        elif num_separators == 1:
            # Minute resolution:
            end = start + timedelta(minutes=1)
        else:
            # Second resolution
            end = start + timedelta(seconds=1)

    return end


def _parse_interval(value):
    '''
    Do some nasty try/except voodoo to get some sort of datetime
    object(s) out of the string.
    '''
    try:
        return sorted(aniso8601.parse_interval(value))
    except ValueError:
        try:
            return aniso8601.parse_datetime(value), None
        except ValueError:
            return aniso8601.parse_date(value), None


def iso8601interval(value, argument='argument'):
    '''
    Parses ISO 8601-formatted datetime intervals into tuples of datetimes.

    Accepts both a single date(time) or a full interval using either start/end
    or start/duration notation, with the following behavior:

    - Intervals are defined as inclusive start, exclusive end
    - Single datetimes are translated into the interval spanning the
      largest resolution not specified in the input value, up to the day.
    - The smallest accepted resolution is 1 second.
    - All timezones are accepted as values; returned datetimes are
      localized to UTC. Naive inputs and date inputs will are assumed UTC.

    Examples::

        "2013-01-01" -> datetime(2013, 1, 1), datetime(2013, 1, 2)
        "2013-01-01T12" -> datetime(2013, 1, 1, 12), datetime(2013, 1, 1, 13)
        "2013-01-01/2013-02-28" -> datetime(2013, 1, 1), datetime(2013, 2, 28)
        "2013-01-01/P3D" -> datetime(2013, 1, 1), datetime(2013, 1, 4)
        "2013-01-01T12:00/PT30M" -> datetime(2013, 1, 1, 12), datetime(2013, 1, 1, 12, 30)
        "2013-01-01T06:00/2013-01-01T12:00" -> datetime(2013, 1, 1, 6), datetime(2013, 1, 1, 12)

    :param str value: The ISO8601 date time as a string
    :return: Two UTC datetimes, the start and the end of the specified interval
    :rtype: A tuple (datetime, datetime)
    :raises ValueError: if the interval is invalid.
    '''

    try:
        start, end = _parse_interval(value)

        if end is None:
            end = _expand_datetime(start, value)

        start, end = _normalize_interval(start, end, value)

    except ValueError:
        msg = 'Invalid {arg}: {value}. {arg} must be a valid ISO8601 date/time interval.'
        raise ValueError(msg.format(arg=argument, value=value),)

    return start, end

iso8601interval.__schema__ = {'type': 'string', 'format': 'iso8601-interval'}


def date(value):
    '''Parse a valid looking date in the format YYYY-mm-dd'''
    date = datetime.strptime(value, "%Y-%m-%d")
    return date

date.__schema__ = {'type': 'string', 'format': 'date'}


def _get_integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError('{0} is not a valid integer'.format(value))


def natural(value, argument='argument'):
    '''Restrict input type to the natural numbers (0, 1, 2, 3...)'''
    value = _get_integer(value)
    if value < 0:
        msg = 'Invalid {arg}: {value}. {arg} must be a non-negative integer'
        raise ValueError(msg.format(arg=argument, value=value))
    return value

natural.__schema__ = {'type': 'integer', 'minimum': 0}


def positive(value, argument='argument'):
    '''Restrict input type to the positive integers (1, 2, 3...)'''
    value = _get_integer(value)
    if value < 1:
        msg = 'Invalid {arg}: {value}. {arg} must be a positive integer'
        raise ValueError(msg.format(arg=argument, value=value))
    return value

positive.__schema__ = {'type': 'integer', 'minimum': 0, 'exclusiveMinimum': True}


class int_range(object):
    '''Restrict input to an integer in a range (inclusive)'''
    def __init__(self, low, high, argument='argument'):
        self.low = low
        self.high = high
        self.argument = argument

    def __call__(self, value):
        value = _get_integer(value)
        if value < self.low or value > self.high:
            msg = 'Invalid {arg}: {val}. {arg} must be within the range {lo} - {hi}'
            raise ValueError(msg.format(arg=self.argument, val=value, lo=self.low, hi=self.high))
        return value

    @property
    def __schema__(self):
        return {
            'type': 'integer',
            'minimum': self.low,
            'maximum': self.high,
        }


def boolean(value):
    '''
    Parse the string ``"true"`` or ``"false"`` as a boolean (case insensitive).

    Also accepts ``"1"`` and ``"0"`` as ``True``/``False`` (respectively).

    If the input is from the request JSON body, the type is already a native python boolean,
    and will be passed through without further parsing.

    :raises ValueError: if the boolean value is invalid
    '''
    if isinstance(value, bool):
        return value

    if not value:
        raise ValueError('boolean type must be non-null')
    value = value.lower()
    if value in ('true', '1',):
        return True
    if value in ('false', '0',):
        return False
    raise ValueError('Invalid literal for boolean(): {0}'.format(value))

boolean.__schema__ = {'type': 'boolean'}


def datetime_from_rfc822(value):
    '''
    Turns an RFC822 formatted date into a datetime object.

    Example::

        inputs.datetime_from_rfc822('Wed, 02 Oct 2002 08:00:00 EST')

    :param str value: The RFC822-complying string to transform
    :return: The parsed datetime
    :rtype: datetime
    :raises ValueError: if value is an invalid date literal

    '''
    raw = value
    if not time_regex.search(value):
        value = ' '.join((value, '00:00:00'))
    try:
        timetuple = parsedate_tz(value)
        timestamp = mktime_tz(timetuple)
        if timetuple[-1] is None:
            return datetime.fromtimestamp(timestamp).replace(tzinfo=pytz.utc)
        else:
            return datetime.fromtimestamp(timestamp, pytz.utc)
    except Exception:
        raise ValueError('Invalid date literal "{0}"'.format(raw))


def datetime_from_iso8601(value):
    '''
    Turns an ISO8601 formatted date into a datetime object.

    Example::

        inputs.datetime_from_iso8601("2012-01-01T23:30:00+02:00")

    :param str value: The ISO8601-complying string to transform
    :return: A datetime
    :rtype: datetime
    :raises ValueError: if value is an invalid date literal

    '''
    try:
        try:
            return aniso8601.parse_datetime(value)
        except ValueError:
            date = aniso8601.parse_date(value)
            return datetime(date.year, date.month, date.day)
    except:
        raise ValueError('Invalid date literal "{0}"'.format(value))

datetime_from_iso8601.__schema__ = {'type': 'string', 'format': 'date-time'}


def date_from_iso8601(value):
    '''
    Turns an ISO8601 formatted date into a date object.

    Example::

        inputs.date_from_iso8601("2012-01-01")



    :param str value: The ISO8601-complying string to transform
    :return: A date
    :rtype: date
    :raises ValueError: if value is an invalid date literal

    '''
    return datetime_from_iso8601(value).date()

date_from_iso8601.__schema__ = {'type': 'string', 'format': 'date'}
