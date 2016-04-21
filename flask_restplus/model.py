# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import re
import warnings

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
    :param str mask: an optional default model mask
    '''
    def __init__(self, name, *args, **kwargs):
        self.__apidoc__ = {
            'name': name
        }
        self.name = name
        self.__parents__ = []
        self.__mask__ = kwargs.pop('mask', None)
        if self.__mask__ and not isinstance(self.__mask__, Mask):
            self.__mask__ = Mask(self.__mask__)
        super(Model, self).__init__(*args, **kwargs)

        def instance_clone(name, *parents):
            return self.__class__.clone(name, self, *parents)
        self.clone = instance_clone

        def instance_inherit(name, *parents):
            return self.__class__.inherit(name, self, *parents)
        self.inherit = instance_inherit

    @cached_property
    def resolved(self):
        '''
        Resolve real fields before submitting them to marshal
        '''
        # Duplicate fields
        resolved = copy.deepcopy(self)

        # Recursively copy parent fields if necessary
        for parent in self.__parents__:
            resolved.update(parent.resolved)

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
        ancestors = [p.ancestors for p in self.__parents__]
        return set.union(set([self.name]), *ancestors)

    def get_parent(self, name):
        if self.name == name:
            return self
        else:
            for parent in self.__parents__:
                found = parent.get_parent(name)
                if found:
                    return found
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
            'type': 'object',
        })

        if self.__parents__:
            refs = [
                {'$ref': '#/definitions/{0}'.format(parent.name)}
                for parent in self.__parents__
            ]

            return {
                'allOf': refs + [schema]
            }
        else:
            return schema

    def extend(self, name, fields):
        '''
        Extend this model (Duplicate all fields)

        :param str name: The new model name
        :param dict fields: The new model extra fields

        :depreated: since 0.9. Use :meth:`clone` instead.
        '''
        warnings.warn('extend is is deprecated, use clone instead', DeprecationWarning, stacklevel=2)
        if isinstance(fields, (list, tuple)):
            return self.clone(name, *fields)
        else:
            return self.clone(name, fields)

    @classmethod
    def clone(cls, name, *parents):
        '''
        Clone these models (Duplicate all fields)

        It can be used from the class

        >>> model = Model.clone(fields_1, fields_2)

        or from an Instanciated model

        >>> new_model = model.clone(fields_1, fields_2)

        :param str name: The new model name
        :param dict parents: The new model extra fields
        '''
        fields = {}
        for parent in parents:
            fields.update(copy.deepcopy(parent))
        return cls(name, fields)

    @classmethod
    def inherit(cls, name, *parents):
        '''
        Inherit this model (use the Swagger composition pattern aka. allOf)

        :param str name: The new model name
        :param dict fields: The new model extra fields
        '''
        model = Model(name, parents[-1])
        model.__parents__ = parents[:-1]
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

    def __unicode__(self):
        return 'Model({name},{{{fields}}})'.format(name=self.name, fields=','.join(self.keys()))

    __str__ = __unicode__
