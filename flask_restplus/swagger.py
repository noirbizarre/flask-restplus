# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import re
import six

from inspect import isclass
from collections import Hashable
from six import string_types

from flask import current_app


from . import fields
from .exceptions import SpecsError
from .utils import camel_to_dash, merge


#: Maps Flask/Werkzeug rooting types to Swagger ones
PATH_TYPES = {
    'int': 'integer',
    'float': 'number',
    'string': 'string',
    None: 'string',
}


#: Maps Flask-Restful/plus fields types to Swagger ones
FIELDS = {
    fields.Raw: {'type': 'object'},
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

DEFAULT_RESPONSE = {'description': 'Success'}


def not_none(data):
    '''Remove all keys where value is None'''
    return dict((k, v) for k, v in data.items() if v is not None)


def ref(model):
    '''Return a reference to model in definitions'''
    return {'$ref': '#/definitions/{0}'.format(model)}


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


def field_to_property(field):
    '''Convert a restful.Field into a Swagger property declaration'''
    prop = {'type': 'string'}

    if isinstance(field, fields.List):
        nested_field = field.container
        prop = {'type': 'array', 'items': field_to_property(nested_field)}

    elif isinstance(field, fields.Nested):
        nested_field = field.nested
        prop = ref(nested_field.__apidoc__['name'])
        if getattr(field, '__apidoc__', {}).get('as_list'):
            prop = {'type': 'array', 'items': prop}
        elif not field.allow_null:
            prop['required'] = True

    elif field in FIELDS:
        prop = FIELDS[field].copy()

    elif field.__class__ in FIELDS:
        prop = FIELDS[field.__class__].copy()

    elif hasattr(field, '__apidoc__'):
        if 'type' in field.__apidoc__:
            prop = {'type': field.__apidoc__['type']}
            if 'format' in field.__apidoc__:
                prop['format'] = field.__apidoc__['format']
        elif 'fields' in field.__apidoc__:
            prop = ref(field.__apidoc__.get('name', field.__class__.__name__))

    else:
        for cls in FIELDS:
            if isinstance(field, cls) or (isclass(field) and issubclass(field, cls)):
                prop = FIELDS[cls].copy()
                break

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
        prop['default'] = field.default

    return prop


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
            param['allowMultiple'] = True
        if arg.choices:
            param['enum'] = arg.choices
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
            'paths': paths,
            'info': infos,
            'produces': list(self.api.representations.keys()),
            'consumes': ['application/json'],
            'securityDefinitions': self.api.authorizations or None,
            'security': self.security_requirements(self.api.security) or None,
            'tags': tags,
            'definitions': self.serialize_definitions() or None,
        }
        return not_none(specs)

    def extract_resource_doc(self, resource, url):
        doc = getattr(resource, '__apidoc__', {})
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
            model, description = doc['body'] if isinstance(doc['body'], (list, tuple)) else (doc['body'], None)
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
        operations = {}
        for method in [m.lower() for m in resource.methods or []]:
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
        return doc[method]['id'] if 'id' in doc[method] else '{0}_{1}'.format(method, camel_to_dash(doc['name']))

    def parameters_for(self, doc, method):
        params = []
        for name, param in merge(doc['params'], doc[method]['params']).items():
            param['name'] = name
            if 'type' not in param:
                param['type'] = 'string'
            if 'in' not in param:
                param['in'] = 'query'
            params.append(param)
        return params

    def responses_for(self, doc, method):
        responses = {}

        for d in doc, doc[method]:
            if 'responses' in d:
                for code, response in d['responses'].items():
                    description, model = (response, None) if isinstance(response, string_types) else response
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

    def serialize_model(self, name, fields):
        properties = {}
        required = []
        for name, field in fields.items():
            prop = field_to_property(field)
            if prop.get('required'):
                required.append(name)
            if 'required' in prop:
                del prop['required']
            properties[name] = prop

        return not_none({
            'required': required or None,
            'properties': properties,
        })

    def serialize_definitions(self):
        return dict(
            (name, self.serialize_model(name, model))
            for name, model in self._registered_models.items()
        )

    def serialize_field(self, field):
        return field_to_property(field)

    def serialize_schema(self, model):
        if isinstance(model, (list, tuple)):
            schema = {'type': 'array'}
            model = model[0]

            if isinstance(model, dict) and hasattr(model, '__apidoc__'):
                model = model.__apidoc__['name']
                self.register_model(model)
                schema['items'] = ref(model)
                return schema

            elif isinstance(model, six.string_types):
                self.register_model(model)
                schema['items'] = ref(model)
                return schema

            elif model in PY_TYPES:
                schema['items'] = {'type': PY_TYPES[model]}
                return schema

        elif isinstance(model, dict) and hasattr(model, '__apidoc__'):
            model = model.__apidoc__['name']
            self.register_model(model)
            return ref(model)

        elif isinstance(model, six.string_types):
            self.register_model(model)
            return ref(model)

        elif isinstance(model, (type, type(None))) and model in PY_TYPES:
            return {'type': PY_TYPES[model]}

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
                elif isinstance(field, fields.List) and hasattr(field.container, '__apidoc__'):
                    self.register_model(field.container.__apidoc__['name'])
                elif (isinstance(field, fields.Raw)
                        or (isclass(field) and issubclass(field, fields.Raw))
                        ) and hasattr(field, '__apidoc__') and not field.__apidoc__.get('type'):
                    self.register_model(field.__apidoc__['name'])

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
        if isinstance(value, (six.string_types)):
            return {value: []}
        elif isinstance(value, dict):
            return dict(
                (k, v if isinstance(v, (list, tuple)) else [v])
                for k, v in value.items()
            )
        else:
            return None
