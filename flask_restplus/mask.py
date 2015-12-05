# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
import re
import six

from collections import namedtuple
from inspect import isclass

from ._compat import OrderedDict
from .errors import RestError
from . import fields

log = logging.getLogger(__name__)

LEXER = re.compile(r'\{|\}|\,|[\w_:\-\*]+')


class MaskError(RestError):
    '''Raised when an error occurs on mask'''
    pass


class ParseError(MaskError):
    '''Raised when the mask parsing failed'''
    pass


#: An Internal representation for mask nesting
Nested = namedtuple('Nested', ['name', 'fields'])


def parse(mask):
    '''Parse a fields mask.
    Expect something in the form::

        {field,nested{nested_field,another},last}

    External brackets are optionals so it can also be written::

        field,nested{nested_field,another},last

    All extras characters will be ignored.

    :param str mask: the mask string to parse
    :raises ParseError: when a mask is unparseable/invalid

    '''
    if not mask:
        return []

    # External brackets are optional in syntax but required for parsing
    mask = mask.strip()
    if mask[0] != '{':
        mask = '{%s}' % mask

    root = fields = previous = None
    stack = []

    for token in LEXER.findall(mask):
        if token == '{':
            new_fields = []
            if stack:
                if not fields or previous != fields[-1]:
                    raise ParseError('Unexpected opening bracket')
                fields.append(Nested(fields.pop(), new_fields))

            stack.append(new_fields)
            fields = new_fields

            root = root or fields

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

    :param data: The data or model to apply mask on
    :param str|list mask: the mask (parsed or not) to apply on data
    :param bool skip: If rue, missing field won't appear in result
    :raises MaskError: when unable to apply the mask

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
    elif isinstance(data, fields.Raw) or isclass(data) and issubclass(data, fields.Raw):
        # Not possible to apply a mask on these remaining fields types
        raise MaskError('Mask is inconsistent with model')
    # Should handle objects
    elif (not isinstance(data, (dict, OrderedDict))
            and hasattr(data, '__dict__')):
        data = data.__dict__

    return filter_data(data, parsed_fields, skip)


def filter_data(data, parsed_fields, skip):
    '''
    Handle the data filtering given a parsed mask

    :param dict data: the raw data to filter
    :param list mask: a parsed mask tofilter against
    :param bool skip: whether or not to skip missing fields

    '''
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
