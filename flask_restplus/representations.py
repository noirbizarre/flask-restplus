# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import importlib

from json import dumps

from flask import make_response, current_app

DEFAULT_SERIALIZER = 'dumps'
serializer = None


def _importer(mod_name, func_name=DEFAULT_SERIALIZER, default=dumps):
    imported = importlib.import_module(mod_name)
    return getattr(imported, func_name, default)


def output_json(data, code, headers=None):
    '''Makes a Flask response with a JSON encoded body'''

    global serializer

    settings = current_app.config.get('RESTPLUS_JSON', {})
    custom_serializer = current_app.config.get('RESTPLUS_JSON_SERIALIZER', None)

    # If the user wants to use a custom serializer, let it be
    if serializer is None and custom_serializer:
        try:
            serializer = _importer(custom_serializer)
        except ImportError:
            if '.' in custom_serializer:
                mod, func = custom_serializer.rsplit('.', 1)
                try:
                    serializer = _importer(mod, func)
                except ImportError:
                    pass

    # fallback, no serializer found so far, use the default one
    if serializer is None:
        serializer = dumps

    # If we're in debug mode, and the indent is not set, we set it to a
    # reasonable value here.  Note that this won't override any existing value
    # that was set.
    if current_app.debug:
        settings.setdefault('indent', 4)

    # always end the json dumps with a new line
    # see https://github.com/mitsuhiko/flask/pull/1262
    dumped = serializer(data, **settings) + "\n"

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp
