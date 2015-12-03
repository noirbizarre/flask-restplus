# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
import re
import six

from collections import namedtuple

from ._compat import OrderedDict
from . import fields

log = logging.getLogger(__name__)

LEXER = re.compile(r'\{|\}|\,|[\w_\*]+')


class ParseError(ValueError):
    '''Raise when the mask parsing failed'''
    pass


Nested = namedtuple('Nested', ['name', 'fields'])


def parse(mask):
    '''Parse a fields mask.
    Expect something in the form::

        {field,nested{nested_field,another},last}

    External brackets are optionals so it can also be written::

        field,nested{nested_field,another},last

    All extras characters will be ignored.
    '''
    if not mask:
        return []

    # External brackets are optional in syntax but required for parsing
    mask = mask.strip()
    if mask[0] != '{':
        mask = '{%s}' % mask

    root = None
    fields = None
    stack = []
    previous = None

    for token in LEXER.findall(mask):
        if token == '{':
            new_fields = []
            if stack:
                if not fields or previous != fields[-1]:
                    raise ParseError('Unexpected opening bracket')
                fields.append(Nested(fields.pop(), new_fields))

            stack.append(new_fields)
            fields = new_fields

            if not root:
                root = fields

        elif token == '}':
            if not stack:
                raise ParseError('Unexpected closing bracket')
            stack.pop()
            fields = stack[-1] if stack else None

        elif token == ',':
            if not previous or previous in ', {'.split():
                raise ParseError('Unexpected coma')

        else:
            fields.append(token)

        previous = token

    if stack:
        raise ParseError('Missing closing bracket')

    return root


def apply(data, mask, skip=False):
    '''
    Apply a fields mask to the data.

    If skip is True, missing field won't appear in result
    '''
    parsed_fields = parse(mask) if isinstance(mask, six.text_type) else mask

    # Should handle lists
    if isinstance(data, (list, tuple, set)):
        return [apply(d, parsed_fields, skip=skip) for d in data]
    # Should handle fields.Nested
    elif isinstance(data, fields.Nested):
        data = data.clone()
        data.model = apply(data.model, parsed_fields, skip=skip)
        return data
    # Should handle fields.List
    elif isinstance(data, fields.List):
        data = data.clone()
        data.container = apply(data.container, parsed_fields, skip=skip)
        return data
    elif type(data) == fields.Raw:
        return fields.Raw(default=data.default, attribute=data.attribute, mask=lambda d: apply(d, parsed_fields, skip))
    elif data == fields.Raw:
        return fields.Raw(mask=lambda d: apply(d, parsed_fields, skip))
    # Should handle objects
    elif (not isinstance(data, (dict, OrderedDict))
            and hasattr(data, '__dict__')):
        data = data.__dict__

    out = {}
    star = False
    for field in parsed_fields:
        if field == '*':
            star = True
            continue
        elif isinstance(field, Nested):
            nested = data.get(field.name, None)
            if skip and nested is None:
                continue
            elif nested is None:
                out[field.name] = None
            else:
                out[field.name] = apply(nested, field.fields, skip=skip)
        elif skip and field not in data:
            continue
        else:
            out[field] = data.get(field, None)

    if star:
        for key, value in data.items():
            if key not in out:
                out[key] = value
    return out
