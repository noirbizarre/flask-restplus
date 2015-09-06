# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import re

from inspect import isclass
from collections import Hashable
try:
    from collections import OrderedDict  # noqa
except ImportError:
    from ordereddict import OrderedDict  # noqa
from six import string_types, itervalues, iteritems, iterkeys

from flask import current_app


from . import fields
from .exceptions import SpecsError
from .model import ApiModel
from .utils import merge, not_none, not_none_sorted


#: Maps Flask/Werkzeug rooting types to Swagger ones
PATH_TYPES = {
    'int': 'integer',
    'float': 'number',
    'string': 'string',
    None: 'string',
}


#: Maps Flask-Restful RequestParser locations to Swagger ones
LOCATIONS = {
    'args': 'query',
    'form': 'formData',
    'headers': 'header',
    'json': 'body',
    'values': 'query',
    'files': 'formData',
}


#: Maps Pyton primitives types to Swagger ones
PY_TYPES = {
    int: 'integer',
    str: 'string',
    bool: 'boolean',
    None: 'void'
}

RE_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')
RE_PARAMS = re.compile(r'<((?:[^:<>]+:)?[^<>]+)>')

DEFAULT_RESPONSE_DESCRIPTION = 'Success'
DEFAULT_RESPONSE = {'description': DEFAULT_RESPONSE_DESCRIPTION}


def ref(model):
    '''Return a reference to model in definitions'''
    name = model.name if isinstance(model, ApiModel) else model
    return {'$ref': '#/definitions/{0}'.format(name)}


def extract_path(path):
    '''
    Transform a Flask/Werkzeug URL pattern in a Swagger one.
    '''
    return RE_URL.sub(r'{\1}', path)


def extract_path_params(path):
    '''
    Extract Flask-style parameters from an URL pattern as Swagger ones.
    '''
    params = {}
    for match in RE_PARAMS.findall(path):
        descriptor, name = match.split(':') if ':' in match else (None, match)
        param = {
            'name': name,
            'in': 'path',
            'required': True
        }

        if descriptor in PATH_TYPES:
            param['type'] = PATH_TYPES[descriptor]
        elif descriptor in current_app.url_map.converters:
            param['type'] = 'string'
        else:
            raise ValueError('Unsupported type converter')
        params[name] = param
    return params


def parser_to_params(parser):
    '''Extract Swagger parameters from a RequestParser'''
    params = {}
    locations = set()
    for arg in parser.args:
        if arg.location == 'cookie':
            continue
        param = {'in': LOCATIONS.get(arg.location, 'query')}
        _handle_arg_type(arg, param)
        if arg.required:
            param['required'] = True
        if arg.help:
            param['description'] = arg.help
        if arg.default:
            param['default'] = arg.default
        if arg.action == 'append':
            param['items'] = {'type': param['type']}
            param['type'] = 'array'
        if arg.choices:
            param['enum'] = arg.choices
            param['collectionFormat'] = 'multi'
        # if param['in'] == 'body':
        #     params['body'] = param
        # else:
        params[arg.name] = param
        locations.add(param['in'])
    if 'body' in locations and 'formData' in locations:
        raise SpecsError("Can't use formData and body at the same time")
    return params


def _handle_arg_type(arg, param):
    if isinstance(arg.type, Hashable) and arg.type in PY_TYPES:
        param['type'] = PY_TYPES[arg.type]
    elif hasattr(arg.type, '__apidoc__'):
        param['type'] = arg.type.__apidoc__['name']
        param['in'] = 'body'
    elif arg.location == 'files':
        param['type'] = 'file'
    else:
        param['type'] = 'string'


class Swagger(object):
    def __init__(self, api):
        self.api = api
        self._registered_models = {}

    def as_dict(self):
        basepath = self.api.base_path
        if len(basepath) > 1 and basepath.endswith('/'):
            basepath = basepath[:-1]
        infos = {
            'title': self.api.title,
            'version': self.api.version,
        }
        if self.api.description:
            infos['description'] = self.api.description
        if self.api.terms_url:
            infos['termsOfService'] = self.api.terms_url
        if self.api.contact and (self.api.contact_email or self.api.contact_url):
            infos['contact'] = {
                'name': self.api.contact,
                'email': self.api.contact_email,
                'url': self.api.contact_url,
            }
        if self.api.license:
            infos['license'] = {'name': self.api.license}
            if self.api.license_url:
                infos['license']['url'] = self.api.license_url

        paths = {}
        tags = []
        for ns in self.api.namespaces:
            tags.append({
                'name': ns.name,
                'description': ns.description
            })
            for resource, urls, kwargs in ns.resources:
                for url in urls:
                    paths[extract_path(url)] = self.serialize_resource(ns, resource, url)

        specs = {
            'swagger': '2.0',
            'basePath': basepath,
            'paths': not_none_sorted(paths),
            'info': infos,
            'produces': list(iterkeys(self.api.representations)),
            'consumes': ['application/json'],
            'securityDefinitions': self.api.authorizations or None,
            'security': self.security_requirements(self.api.security) or None,
            'tags': tags,
            'definitions': self.serialize_definitions() or None,
        }
        return not_none(specs)

    def extract_resource_doc(self, resource, url):
        doc = getattr(resource, '__apidoc__', {})
        if doc is False:
            return False
        doc['name'] = resource.__name__
        doc['params'] = self.merge_params(extract_path_params(url), doc)
        for method in [m.lower() for m in resource.methods or []]:
            method_doc = doc.get(method, {})
            method_impl = getattr(resource, method)
            if hasattr(method_impl, 'im_func'):
                method_impl = method_impl.im_func
            elif hasattr(method_impl, '__func__'):
                method_impl = method_impl.__func__
            method_doc = merge(method_doc, getattr(method_impl, '__apidoc__', {}))
            if method_doc is not False:
                method_doc['docstring'] = getattr(method_impl, '__doc__')
                method_doc['params'] = self.merge_params({}, method_doc)
            doc[method] = method_doc
        return doc

    def merge_params(self, params, doc):
        if 'params' not in doc and 'parser' not in doc and 'body' not in doc:
            return params

        if 'parser' in doc:
            params = merge(params, parser_to_params(doc['parser']))

        if 'params' in doc:
            params = merge(params, doc['params'])

        if 'body' in doc:
            if isinstance(doc['body'], (list, tuple)) and len(doc['body']) == 2:
                model, description = doc['body']
            else:
                model, description = doc['body'], None
            params = merge(params, {
                'payload': not_none({
                    'name': 'payload',
                    'required': True,
                    'in': 'body',
                    'schema': self.serialize_schema(model),
                    'description': description
                })
            })

        return params

    def serialize_resource(self, ns, resource, url):
        doc = self.extract_resource_doc(resource, url)
        if doc is False:
            return
        operations = {}
        for method in [m.lower() for m in resource.methods or []]:
            if doc[method] is False:
                continue
            operations[method] = self.serialize_operation(doc, method)
            operations[method]['tags'] = [ns.name]
        return operations

    def serialize_operation(self, doc, method):
        operation = {
            'responses': self.responses_for(doc, method) or None,
            'summary': self.summary_for(doc, method) or None,
            'description': self.description_for(doc, method) or None,
            'operationId': self.operation_id_for(doc, method),
            'parameters': self.parameters_for(doc, method) or None,
            'security': self.security_for(doc, method),
        }
        # Handle deprecated annotation
        if doc.get('deprecated') or doc[method].get('deprecated'):
            operation['deprecated'] = True
        # Handle form exceptions:
        if operation['parameters'] and any(p['in'] == 'formData' for p in operation['parameters']):
            if any(p['type'] == 'file' for p in operation['parameters']):
                operation['consumes'] = ['multipart/form-data']
            else:
                operation['consumes'] = ['application/x-www-form-urlencoded', 'multipart/form-data']
        return not_none(operation)

    def summary_for(self, doc, method):
        '''Extract the first sentence from the first docstring line'''
        if not doc[method].get('docstring'):
            return
        first_line = doc[method]['docstring'].strip().split('\n')[0]
        return first_line.split('.')[0]

    def description_for(self, doc, method):
        '''Extract the description metadata and fallback on the whole docstring'''
        parts = []
        if 'description' in doc:
            parts.append(doc['description'])
        if method in doc and 'description' in doc[method]:
            parts.append(doc[method]['description'])
        if doc[method].get('docstring'):
            splitted = doc[method]['docstring'].strip().split('\n', 1)
            if len(splitted) == 2:
                parts.append(splitted[1].strip())

        return '\n'.join(parts).strip()

    def operation_id_for(self, doc, method):
        '''Extract the operation id'''
        return doc[method]['id'] if 'id' in doc[method] else self.api.default_id(doc['name'], method)

    def parameters_for(self, doc, method):
        params = []
        for name, param in iteritems(merge(doc['params'], doc[method]['params'])):
            param['name'] = name
            if 'type' not in param and 'schema' not in param:
                param['type'] = 'string'
            if 'in' not in param:
                param['in'] = 'query'

            if 'type' in param and 'schema' not in param:
                ptype = param.get('type', None)
                if isinstance(ptype, (list, tuple)):
                    typ = ptype[0]
                    param['type'] = 'array'
                    param['items'] = {'type': PY_TYPES.get(typ, typ)}

                elif isinstance(ptype, (type, type(None))) and ptype in PY_TYPES:
                    param['type'] = PY_TYPES[ptype]

            params.append(param)
        return params

    def responses_for(self, doc, method):
        # TODO: simplify/refactor responses/model handling
        responses = {}

        for d in doc, doc[method]:
            if 'responses' in d:
                for code, response in iteritems(d['responses']):
                    description, model = (response, None) if isinstance(response, string_types) else response
                    description = description or DEFAULT_RESPONSE_DESCRIPTION
                    if code in responses:
                        responses[code].update(description=description)
                    else:
                        responses[code] = {'description': description}
                    if model:
                        responses[code]['schema'] = self.serialize_schema(model)
            if 'model' in d:
                code = str(d.get('default_code', 200))
                if code not in responses:
                    responses[code] = DEFAULT_RESPONSE.copy()
                responses[code]['schema'] = self.serialize_schema(d['model'])

        if not responses:
            responses['200'] = DEFAULT_RESPONSE.copy()
        return responses

    def serialize_definitions(self):
        return dict(
            (name, model.__schema__)
            for name, model in iteritems(self._registered_models)
        )

    def serialize_schema(self, model):
        if isinstance(model, (list, tuple)):
            model = model[0]
            return {
                'type': 'array',
                'items': self.serialize_schema(model),
            }

        elif isinstance(model, ApiModel):
            self.register_model(model)
            return ref(model)

        elif isinstance(model, string_types):
            self.register_model(model)
            return ref(model)

        elif isclass(model) and issubclass(model, fields.BaseField):
            return self.serialize_schema(model())

        elif isinstance(model, fields.BaseField):
            return model.__schema__

        elif isinstance(model, (type, type(None))) and model in PY_TYPES:
            return {'type': PY_TYPES[model]}

        raise ValueError('Model {0} not registered'.format(model))

    def register_model(self, model):
        name = model.name if isinstance(model, ApiModel) else model
        if name not in self.api.models:
            raise ValueError('Model {0} not registered'.format(name))
        specs = self.api.models[name]
        self._registered_models[name] = specs
        if isinstance(specs, ApiModel):
            if specs.__parent__:
                self.register_model(specs.__parent__)
            for field in itervalues(specs):
                self.register_field(field)

    def register_field(self, field):
        if isinstance(field, fields.Polymorph):
            for model in itervalues(field.mapping):
                self.register_model(model)
        elif isinstance(field, fields.Nested):
            self.register_model(field.nested)
        elif isinstance(field, fields.List):
            self.register_field(field.container)

    def security_for(self, doc, method):
        security = None
        if 'security' in doc:
            auth = doc['security']
            security = self.security_requirements(auth)

        if 'security' in doc[method]:
            auth = doc[method]['security']
            security = self.security_requirements(auth)

        return security

    def security_requirements(self, value):
        if isinstance(value, (list, tuple)):
            return [self.security_requirement(v) for v in value]
        elif value:
            requirement = self.security_requirement(value)
            return [requirement] if requirement else None
        else:
            return []

    def security_requirement(self, value):
        if isinstance(value, (string_types)):
            return {value: []}
        elif isinstance(value, dict):
            return dict(
                (k, v if isinstance(v, (list, tuple)) else [v])
                for k, v in iteritems(value)
            )
        else:
            return None
