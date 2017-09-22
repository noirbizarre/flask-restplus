# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None, expose_headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True, credentials=False):
    """
    http://flask.pocoo.org/snippets/56/
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if expose_headers is not None and not isinstance(expose_headers, str):
        expose_headers = ', '.join(x.upper() for x in expose_headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def set_headers(h):
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if credentials:
                h['Access-Control-Allow-Credentials'] = 'true'
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            if expose_headers is not None:
                h['Access-Control-Expose-Headers'] = expose_headers

        def wrapped_function(*args, **kwargs):
            is_rest_specific_response = False
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
                h = resp.headers
            else:
                resp = f(*args, **kwargs)
                if not (isinstance(resp, dict) or isinstance(resp, list)):
                    resp = make_response(resp)
                    h = resp.headers
                else:
                    is_rest_specific_response = True
                    h = {}

            if not attach_to_all and request.method != 'OPTIONS':
                if not is_rest_specific_response:
                    return resp
                else:
                    return (resp, )

            set_headers(h)

            if not is_rest_specific_response:
                return resp
            else:
                return (resp, h, )

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
