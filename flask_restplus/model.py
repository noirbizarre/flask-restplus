# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy

from collections import MutableMapping
from six import iteritems, itervalues
from werkzeug import cached_property

from flask.ext.restful import abort

from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError

from .utils import not_none


def instance(cls):
    if isinstance(cls, type):
        return cls()
    return cls


class ApiModel(dict, MutableMapping):
    '''A thin wrapper on dict to store API doc metadata'''
    def __init__(self, *args, **kwargs):
        self.__apidoc__ = {}
        self.__parent__ = None
        super(ApiModel, self).__init__(*args, **kwargs)

    @cached_property
    def resolved(self):
        '''
        Resolve real fields before submitting them to upstream restful marshal
        '''
        # Duplicate fields
        resolved = copy.deepcopy(self)

        # Recursively copy parent fields if necessary
        if self.__parent__:
            resolved.update(self.__parent__.resolved)

        # Handle discriminator
        candidates = [f for f in itervalues(resolved) if getattr(f, 'discriminator', None)]
        # Ensure the is only one discriminator
        if len(candidates) > 1:
            raise ValueError('There can only be one discriminator by schema')
        # Ensure discriminator always output the model name
        elif len(candidates) == 1:
            candidates[0].default = self.__apidoc__['name']

        return resolved

    @property
    def ancestors(self):
        '''
        Return the ancestors tree
        '''
        return self.__parent__.tree

    @cached_property
    def tree(self):
        '''
        Return the inheritance tree
        '''
        tree = [self.__apidoc__['name']]
        return self.ancestors + tree if self.__parent__ else tree

    @property
    def name(self):
        return self.__apidoc__['name']

    def get_parent(self, name):
        if self.name == name:
            return self
        elif self.__parent__:
            return self.__parent__.get_parent(name)
        else:
            raise ValueError('Parent ' + name + ' not found')

    @cached_property
    def __schema__(self):
        properties = {}
        required = set()
        discriminator = None
        for name, field in iteritems(self):
            field = instance(field)
            properties[name] = field.__schema__
            if field.required:
                required.add(name)
            if getattr(field, 'discriminator', False):
                discriminator = name

        schema = not_none({
            'required': sorted(list(required)) or None,
            'properties': properties,
            'discriminator': discriminator,
        })

        if self.__parent__:
            return {
                'allOf': [
                    {'$ref': '#/definitions/{0}'.format(self.__parent__.name)},
                    schema
                ]
            }
        else:
            return schema

    def validate(self, data, resolver=None):
        validator = Draft4Validator(self.__schema__, resolver=resolver)
        try:
            validator.validate(data)
        except ValidationError:
            abort(400, message='Input payload validation failed',
                  errors=dict(self.format_error(e) for e in validator.iter_errors(data)))

    def format_error(self, error):
        path = list(error.path)
        if error.validator == 'required':
            path.append(error.validator_value[0])
        key = '.'.join(path)
        return key, error.message
