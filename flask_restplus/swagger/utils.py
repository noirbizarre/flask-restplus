# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from collections import Hashable

from flask import current_app

from . import mappings
from .. import fields

RE_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')
RE_PARAMS = re.compile(r'<((?:[^:<>]+:)?[^<>]+)>')


def extract_path(path):
    '''
    Transform a Flask/Werkzeug URL pattern in a Swagger one.
    '''
    return RE_URL.sub(r'{\1}', path)


def extract_path_params(path):
    '''
    Extract Flask-style parameters from an URL pattern as Swagger ones.
    '''
    params = []
    for match in RE_PARAMS.findall(path):
        descriptor, name = match.split(':') if ':' in match else (None, match)
        param = {
            'name': name,
            'paramType': 'path',
            'required': True
        }

        if descriptor in mappings.PATH_TYPES:
            param['type'] = mappings.PATH_TYPES[descriptor]
        elif descriptor in current_app.url_map.converters:
            param['type'] = 'string'
        else:
            raise ValueError('Unsupported type converter')
        params.append(param)
    return params


def field_to_property(field):
    '''Convert a restful.Field into a Swagger property declaration'''
    if isinstance(field, fields.List):
        nested_field = field.container
        prop = {'type': 'array', 'items': {}}
        if nested_field in mappings.FIELDS:
            prop['items'] = mappings.FIELDS[nested_field]
        else:
            prop['items']['type'] = 'string'
        return prop
    elif isinstance(field, fields.Nested):
        nested_field = field.nested
        prop = {'$ref': nested_field.__apidoc__['name']}
        if getattr(field, '__apidoc__', {}).get('as_list'):
            prop = {'type': 'array', 'items': prop}
        elif not field.allow_null:
            prop['required'] = True
    elif field in mappings.FIELDS:
        prop = mappings.FIELDS[field].copy()
    elif field.__class__ in mappings.FIELDS:
        prop = mappings.FIELDS[field.__class__].copy()
    else:
        prop = {'type': 'string'}

    if getattr(field, 'description', None):
        prop['description'] = field.description
    if getattr(field, 'minimum', None) is not None:
        prop['minimum'] = field.minimum
    if getattr(field, 'maximum', None):
        prop['maximum'] = field.maximum
    if getattr(field, 'enum', None):
        prop['enum'] = field.enum
    if getattr(field, 'required', None):
        prop['required'] = field.required
    if getattr(field, 'default', None):
        prop['defaultValue'] = field.default

    return prop


def parser_to_params(parser):
    '''Extract Swagger parameters from a RequestParser'''
    params = {}
    for arg in parser.args:
        if arg.location == 'cookie':
            continue
        param = {'paramType': mappings.LOCATIONS.get(arg.location, 'query')}
        _handle_arg_type(arg, param)
        if arg.required:
            param['required'] = True
        if arg.help:
            param['description'] = arg.help
        if arg.default:
            param['defaultValue'] = arg.default
        if arg.action == 'append':
            param['allowMultiple'] = True
        # if param['paramType'] == 'body':
        #     params['body'] = param
        # else:
        params[arg.name] = param
    return params


def _handle_arg_type(arg, param):
    if isinstance(arg.type, Hashable) and arg.type in mappings.PY_TYPES:
        param['type'] = mappings.PY_TYPES[arg.type]
    elif hasattr(arg.type, '__apidoc__'):
        param['type'] = arg.type.__apidoc__['name']
        param['paramType'] = 'body'
    else:
        param['type'] = 'string'
