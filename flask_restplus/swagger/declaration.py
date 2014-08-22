# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import string_types

from .. import fields
from ..utils import camel_to_dash

from . import mappings
from .base import SwaggerBaseView
from .utils import extract_path, extract_path_params, field_to_property, parser_to_params


class ApiDeclaration(SwaggerBaseView):
    def __init__(self, api, namespace):
        self.namespace = namespace
        self._registered_models = {}
        super(ApiDeclaration, self).__init__(api)

    def get(self):
        response = super(ApiDeclaration, self).get()
        response['basePath'] = self.api.base_url.rstrip('/')
        response['resourcePath'] = self.namespace.path
        response['produces'] = [str(k) for k in self.api.representations.keys()]
        for resource, urls, kwargs in self.namespace.resources:
            for url in urls:
                response['apis'].append(self.serialize_resource(resource, url))
        if self._registered_models:
            response['models'] = dict(
                (name, self.serialize_model(name, model))
                for name, model in self._registered_models.items()
            )
        return response

    def serialize_resource(self, resource, url):
        data = {
            'path': extract_path(url),
            'description': resource.__doc__,
            'operations': self.extract_operations(resource, url)
        }
        return data

    def extract_operations(self, resource, url):
        operations = []
        for method in [m.lower() for m in resource.methods]:
            operation = {
                'method': method,
                'nickname': self.extract_nickname(resource, method),
                'parameters': self.extract_parameters(resource, url, method),
                'summary': self.extract_summary(resource, method) or None,
                'notes': self.extract_notes(resource, method) or None,
                'responseMessages': self.extract_responses(resource, method) or None,
                'authorizations': self.extract_authorizations(resource, method),
            }
            self.extract_model(operation, resource, method)
            operations.append(dict((k, v) for k, v in operation.items() if v is not None))
        return operations

    def extract_summary(self, resource, method):
        '''Extract the first sentence from the first docstring line'''
        method_impl = self.get_method(resource, method)
        if not method_impl or not method_impl.__doc__:
            return
        first_line = method_impl.__doc__.strip().split('\n')[0]
        return first_line.split('.')[0]

    def extract_notes(self, resource, method):
        '''Extract the notes metadata and fallback on the whole docstring'''
        parts = []
        if hasattr(resource, '__apidoc__'):
            if 'notes' in resource.__apidoc__:
                parts.append(resource.__apidoc__['notes'])
            if method in resource.__apidoc__ and 'notes' in resource.__apidoc__[method]:
                parts.append(resource.__apidoc__[method]['notes'])

        method_impl = self.get_method(resource, method)
        if method_impl:
            if hasattr(method_impl, '__apidoc__') and 'notes' in method_impl.__apidoc__:
                parts.append(method_impl.__apidoc__['notes'])
            else:
                docstring = getattr(method_impl, '__doc__', None)
                if docstring:
                    splitted = docstring.strip().split('\n', 1)
                    if len(splitted) == 2:
                        parts.append(splitted[1].strip())
        return '\n'.join(parts).strip()

    def extract_nickname(self, resource, method):
        '''Extract the operation nickname'''
        method_impl = self.get_method(resource, method)
        if hasattr(method_impl, '__apidoc__') and 'nickname' in method_impl.__apidoc__:
            return method_impl.__apidoc__['nickname']
        return '{0}_{1}'.format(method, camel_to_dash(resource.__name__))

    def get_method(self, cls, name):
        '''Get a class method by name'''
        method = cls.__dict__.get(name, None)
        if method is None:
            for cls in cls.__mro__:
                for item_key in cls.__dict__.keys():
                    if item_key == name:
                        method = cls.__dict__[item_key]
        return method

    def extract_parameters(self, resource, url, method):
        params = extract_path_params(url)
        params = self.update_params(params, resource, method)
        method_impl = self.get_method(resource, method)
        if method_impl:
            params = self.update_params(params, method_impl)
        return params

    def update_params(self, params, obj, method=None):
        if not hasattr(obj, '__apidoc__') or ('params' not in obj.__apidoc__ and 'parser' not in obj.__apidoc__):
            return params
        by_name = dict((p['name'], p) for p in params)
        cascade = []

        if 'parser' in obj.__apidoc__:
            cascade.append(parser_to_params(obj.__apidoc__['parser']))

        if 'params' in obj.__apidoc__:
            cascade.append(obj.__apidoc__['params'])

        if method and method in obj.__apidoc__ and 'params' in obj.__apidoc__[method]:
            cascade.append(obj.__apidoc__[method]['params'])

        for params in cascade:
            self._update_params_by_name(by_name, params)
        return by_name.values()

    def _update_params_by_name(self, params, new_params):
        for name, param in new_params.items():
            if name in params:
                params[name].update(param)
            else:
                params[name] = param
                params[name].update(name=name)
            if 'type' not in params[name]:
                params[name]['type'] = 'string'
            if 'paramType' not in params[name]:
                params[name]['paramType'] = 'query'
        return params

    def extract_responses(self, resource, method):
        responses = {}
        if hasattr(resource, '__apidoc__'):
            if 'responses' in resource.__apidoc__:
                self._update_responses(responses, resource.__apidoc__['responses'])
            if method in resource.__apidoc__ and 'responses' in resource.__apidoc__[method]:
                self._update_responses(responses, resource.__apidoc__[method]['responses'])
        implem = self.get_method(resource, method)
        if implem and hasattr(implem, '__apidoc__') and 'responses' in implem.__apidoc__:
            self._update_responses(responses, implem.__apidoc__['responses'])
        return responses.values()

    def _update_responses(self, responses, new_responses):
        for code, response in new_responses.items():
            message, model = (response, None) if isinstance(response, string_types) else response
            if code in responses:
                responses[code].update(message=message)
            else:
                responses[code] = {'code': code, 'message': message}
            if model:
                responses[code].update(responseModel=model)
        return responses

    def serialize_model(self, name, fields):
        return {
            'id': name,
            'properties': dict((n, self.serialize_field(f)) for n, f in fields.items()),
        }

    def serialize_field(self, field):
        return field_to_property(field)

    def extract_model(self, operation, resource, method):
        method_impl = self.get_method(resource, method)
        if hasattr(method_impl, '__apidoc__') and 'model' in method_impl.__apidoc__:
            model = method_impl.__apidoc__['model']
        elif (hasattr(resource, '__apidoc__') and method in resource.__apidoc__
            and 'model' in resource.__apidoc__[method]):
            model = resource.__apidoc__[method]['model']
        elif hasattr(resource, '__apidoc__') and 'model' in resource.__apidoc__:
            model = resource.__apidoc__['model']
        else:
            return

        if isinstance(model, (list, tuple)):
            operation['type'] = 'array'
            model = model[0]

            if isinstance(model, dict) and hasattr(model, '__apidoc__'):
                model = model.__apidoc__['name']
                self.register_model(model)
                operation['items'] = {'$ref': model}
                return

            elif isinstance(model, basestring):
                self.register_model(model)
                operation['items'] = {'$ref': model}
                return

            elif model in mappings.PY_TYPES:
                operation['items'] = {'type': mappings.PY_TYPES[model]}
                return

        elif isinstance(model, dict) and hasattr(model, '__apidoc__'):
            model = model.__apidoc__['name']
            self.register_model(model)
            operation['type'] = model
            return

        elif isinstance(model, basestring):
            self.register_model(model)
            operation['type'] = model
            return

        elif isinstance(model, (type, type(None))) and model in mappings.PY_TYPES:
            operation['type'] = mappings.PY_TYPES[model]
            return

        raise ValueError('Model {0} not registered'.format(model))

    def register_model(self, model):
        if model not in self.api.models:
            raise ValueError('Model {0} not registered'.format(model))
        specs = self.api.models[model]
        self._registered_models[model] = specs
        if isinstance(specs, dict):
            for name, field in specs.items():
                if isinstance(field, fields.Nested) and hasattr(field.nested, '__apidoc__'):
                    self.register_model(field.nested.__apidoc__['name'])
                    # self._registered_models[model]

    def extract_authorizations(self, resource, method):
        authorizations = None
        if hasattr(resource, '__apidoc__') and 'authorizations' in resource.__apidoc__:
            auth = resource.__apidoc__['authorizations']
            if isinstance(auth, basestring):
                authorizations = {auth: []}
            elif auth is None:
                authorizations = {}

        method_impl = self.get_method(resource, method)
        if hasattr(method_impl, '__apidoc__') and 'authorizations' in method_impl.__apidoc__:
            auth = method_impl.__apidoc__['authorizations']
            if isinstance(auth, basestring):
                authorizations = {auth: []}
            elif auth is None:
                authorizations = {}

        return authorizations
