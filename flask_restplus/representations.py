# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from flask import make_response, current_app

from .utils import preload_serializer


def output_json(data, code, headers=None):
    '''Makes a Flask response with a JSON encoded body'''
    settings = current_app.config.get('RESTPLUS_JSON', {})
    serializer = current_app.config.get('RESTPLUS_CACHED_SERIALIZER')
    if serializer is None:
        preload_serializer(current_app)
        serializer = current_app.config.get('RESTPLUS_CACHED_SERIALIZER')

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
