# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import importlib
import warnings

from collections import OrderedDict
from copy import deepcopy
from json import dumps
from six import iteritems

from ._http import HTTPStatus


FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


__all__ = ('preload_serializer', 'importer', 'merge', 'camel_to_dash', 'default_id',
           'not_none', 'not_none_sorted', 'unpack')


def preload_serializer(app):
    '''
    Preload the json serializer for the given ``app``.

    :param flask.Flask app: The flask application object
    '''
    custom_serializer = app.config.get('RESTPLUS_JSON_SERIALIZER', None)
    serializer = None

    # If the user wants to use a custom serializer, let it be
    if custom_serializer:
        try:
            serializer = importer(custom_serializer, 'dumps')
        except ImportError:
            if '.' in custom_serializer:
                mod, func = custom_serializer.rsplit('.', 1)
                try:
                    serializer = importer(mod, func)
                except ImportError:
                    warnings.warn("Unable to load custom serializer '{}', falling back to "
                                  "'json.dumps'".format(custom_serializer),
                                  UserWarning)

    # fallback, no serializer found so far, use the default one
    if serializer is None:
        serializer = dumps
    app.config['RESTPLUS_CACHED_SERIALIZER'] = serializer


def importer(mod_name, obj_name, default=None):
    '''
    Import the given ``obj_name`` from the given ``mod_name``.

    :param str mod_name: Module from which to import the ``obj_name``
    :param str obj_name: Object to import from ``mod_name``
    :param object default: Default object to return

    :return: Imported object
    '''
    imported = importlib.import_module(mod_name)
    return getattr(imported, obj_name, default)


def merge(first, second):
    '''
    Recursively merges two dictionnaries.

    Second dictionnary values will take precedance over those from the first one.
    Nested dictionnaries are merged too.

    :param dict first: The first dictionnary
    :param dict second: The second dictionnary
    :return: the resulting merged dictionnary
    :rtype: dict
    '''
    if not isinstance(second, dict):
        return second
    result = deepcopy(first)
    for key, value in iteritems(second):
        if key in result and isinstance(result[key], dict):
                result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def camel_to_dash(value):
    '''
    Transform a CamelCase string into a low_dashed one

    :param str value: a CamelCase string to transform
    :return: the low_dashed string
    :rtype: str
    '''
    first_cap = FIRST_CAP_RE.sub(r'\1_\2', value)
    return ALL_CAP_RE.sub(r'\1_\2', first_cap).lower()


def default_id(resource, method):
    '''Default operation ID generator'''
    return '{0}_{1}'.format(method, camel_to_dash(resource))


def not_none(data):
    '''
    Remove all keys where value is None

    :param dict data: A dictionnary with potentialy some values set to None
    :return: The same dictionnary without the keys with values to ``None``
    :rtype: dict
    '''
    return dict((k, v) for k, v in iteritems(data) if v is not None)


def not_none_sorted(data):
    '''
    Remove all keys where value is None

    :param OrderedDict data: A dictionnary with potentialy some values set to None
    :return: The same dictionnary without the keys with values to ``None``
    :rtype: OrderedDict
    '''
    return OrderedDict((k, v) for k, v in sorted(iteritems(data)) if v is not None)


def unpack(response, default_code=HTTPStatus.OK):
    '''
    Unpack a Flask standard response.

    Flask response can be:
    - a single value
    - a 2-tuple ``(value, code)``
    - a 3-tuple ``(value, code, headers)``

    .. warning::

        When using this function, you must ensure that the tuple is not the reponse data.
        To do so, prefer returning list instead of tuple for listings.

    :param response: A Flask style response
    :param int default_code: The HTTP code to use as default if none is provided
    :return: a 3-tuple ``(data, code, headers)``
    :rtype: tuple
    :raise ValueError: if the response does not have one of the expected format
    '''
    if not isinstance(response, tuple):
        # data only
        return response, default_code, {}
    elif len(response) == 1:
        # data only as tuple
        return response[0], default_code, {}
    elif len(response) == 2:
        # data and code
        data, code = response
        return data, code, {}
    elif len(response) == 3:
        # data, code and headers
        data, code, headers = response
        return data, code or default_code, headers
    else:
        raise ValueError('Too many response values')
