# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus import fields


#: Maps Flask/Werkzeug rooting types to Swagger ones
PATH_TYPES = {
    'int': 'integer',
    'float': 'number',
    'string': 'string',
    None: 'string',
}


#: Maps Flask-Restful/plus fields types to Swagger ones
FIELDS = {
    fields.Raw: {'type': 'string'},
    fields.String: {'type': 'string'},
    fields.Integer: {'type': 'integer'},
    fields.Boolean: {'type': 'boolean'},
    fields.Float: {'type': 'number'},
    fields.Arbitrary: {'type': 'number'},
    fields.DateTime: {'type': 'string', 'format': 'date-time'},
    fields.Fixed: {'type': 'number'},
}


#: Maps Flask-Restful RequestParser locations to Swagger ones
LOCATIONS = {
    'args': 'query',
    'form': 'form',
    'headers': 'header',
    'json': 'body',
    'values': 'query',
}


#: Maps Pyton primitives types to Swagger ones
PY_TYPES = {
    int: 'integer',
    str: 'string',
    bool: 'boolean',
    None: 'void'
}
