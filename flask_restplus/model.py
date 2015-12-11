# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import re

from collections import MutableMapping
from six import iteritems, itervalues
from werkzeug import cached_property

from .mask import Mask
from .errors import abort

from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError

from .utils import not_none


RE_REQUIRED = re.compile(r'u?\'(?P<name>.*)\' is a required property', re.I | re.U)


def instance(cls):
    if isinstance(cls, type):
        return cls()
    return cls


class Model(dict, MutableMapping):
    '''
    A thin wrapper on dict to store API doc metadata.

    :param str name: The model public name
    :param str mask: an optionnal default model mask
    '''
    def __init__(self, name, *args, **kwargs):
        self.__apidoc__ = {
            'name': name
        }
        self.name = name
        self.__parent__ = None
        self.__mask__ = kwargs.pop('mask', None)
        if self.__mask__ and not isinstance(self.__mask__, Mask):
            self.__mask__ = Mask(self.__mask__)
        super(Model, self).__init__(*args, **kwargs)

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
            candidates[0].default = self.name

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
        tree = [self.name]
        return self.ancestors + tree if self.__parent__ else tree

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
            'x-mask': str(self.__mask__) if self.__mask__ else None,
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

    def extend(self, name, fields):
        '''
        Extend this model (Duplicate all fields)

        :param str name: The new model name
        :param dict fields: The new model extra fields
        '''
        model = Model(name, copy.deepcopy(self))
        model.update(fields)
        return model

    def inherit(self, name, fields):
        '''
        Inherit this model (use the Swagger composition pattern aka. allOf)

        :param str name: The new model name
        :param dict fields: The new model extra fields
        '''
        model = Model(name, fields)
        model.__parent__ = self
        return model

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
            name = RE_REQUIRED.match(error.message).group('name')
            path.append(name)
        key = '.'.join(str(p) for p in path)
        return key, error.message
