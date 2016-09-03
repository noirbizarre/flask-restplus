# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import re

from inspect import isclass, getdoc
from collections import Hashable
from six import string_types, itervalues, iteritems, iterkeys

from flask import current_app

from ._compat import OrderedDict

from . import fields
from .model import Model, ModelBase
from .reqparse import RequestParser
from .utils import merge, not_none, not_none_sorted


#: Maps Flask/Werkzeug rooting types to Swagger ones
PATH_TYPES = {
    'int': 'integer',
    'float': 'number',
    'string': 'string',
    None: 'string',
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

RE_RAISES = re.compile(r'^:raises\s+(?P<name>[\w\d_]+)\s*:\s*(?P<description>.*)$', re.MULTILINE)


def ref(model):
    '''Return a reference to model in definitions'''
    name = model.name if isinstance(model, ModelBase) else model
    return {'$ref': '#/definitions/{0}'.format(name)}


def _v(value):
    '''Dereference values (callable)'''
    return value() if callable(value) else value


def extract_path(path):
    '''
    Transform a Flask/Werkzeug URL pattern in a Swagger one.
    '''
    return RE_URL.sub(r'{\1}', path)


def extract_path_params(path):
    '''
    Extract Flask-style parameters from an URL pattern as Swagger ones.
    '''
    params = OrderedDict()
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


def _param_to_header(param):
    param.pop('in', None)
    param.pop('name', None)

    typedef = param.get('type', 'string')
    if isinstance(typedef, Hashable) and typedef in PY_TYPES:
        param['type'] = PY_TYPES[typedef]
    elif hasattr(typedef, '__schema__'):
        param.update(typedef.__schema__)
    else:
        param['type'] = typedef
    return param


def parse_docstring(obj):
    raw = getdoc(obj)
    summary = raw.strip(' \n').split('\n')[0].split('.')[0] if raw else None
    raises = {}
    details = raw.replace(summary, '').lstrip('. \n').strip(' \n') if raw else None
    for match in RE_RAISES.finditer(raw or ''):
        raises[match.group('name')] = match.group('description')
        if details:
            details = details.replace(match.group(0), '')
    parsed = {
        'raw': raw,
        'summary': summary or None,
        'details': details or None,
        'returns': None,
        'params': [],
        'raises': raises,
    }
    return parsed


class Swagger(object):
    '''
    A Swagger documentation wrapper for an API instance.
    '''
    def __init__(self, api):
        self.api = api
        self._registered_models = {}

    def as_dict(self):
        '''
        Output the specification as a serializable ``dict``.

        :returns: the full Swagger specification in a serializable format
        :rtype: dict
        '''
        basepath = self.api.base_path
        if len(basepath) > 1 and basepath.endswith('/'):
            basepath = basepath[:-1]
        infos = {
            'title': _v(self.api.title),
            'version': _v(self.api.version),
        }
        if self.api.description:
            infos['description'] = _v(self.api.description)
        if self.api.terms_url:
            infos['termsOfService'] = _v(self.api.terms_url)
        if self.api.contact and (self.api.contact_email or self.api.contact_url):
            infos['contact'] = {
                'name': _v(self.api.contact),
                'email': _v(self.api.contact_email),
                'url': _v(self.api.contact_url),
            }
        if self.api.license:
            infos['license'] = {'name': _v(self.api.license)}
            if self.api.license_url:
                infos['license']['url'] = _v(self.api.license_url)

        paths = {}
        tags = self.extract_tags(self.api)

        # register errors
        responses = self.register_errors()

        for ns in self.api.namespaces:
            for resource, urls, kwargs in ns.resources:
                for url in self.api.ns_urls(ns, urls):
                    paths[extract_path(url)] = self.serialize_resource(ns, resource, url, kwargs)

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
            'responses': responses or None,
            'host': self.get_host(),
        }
        return not_none(specs)

    def get_host(self):
        hostname = current_app.config.get('SERVER_NAME', None) or None
        if hostname and self.api.blueprint and self.api.blueprint.subdomain:
            hostname = '.'.join((self.api.blueprint.subdomain, hostname))
        return hostname

    def extract_tags(self, api):
        tags = []
        by_name = {}
        for tag in api.tags:
            if isinstance(tag, string_types):
                tag = {'name': tag}
            elif isinstance(tag, (list, tuple)):
                tag = {'name': tag[0], 'description': tag[1]}
            elif isinstance(tag, dict) and 'name' in tag:
                pass
            else:
                raise ValueError('Unsupported tag format for {0}'.format(tag))
            tags.append(tag)
            by_name[tag['name']] = tag
        for ns in api.namespaces:
            if ns.name not in by_name:
                tags.append({
                    'name': ns.name,
                    'description': ns.description
                })
            elif ns.description:
                by_name[ns.name]['description'] = ns.description
        return tags

    def extract_resource_doc(self, resource, url):
        doc = getattr(resource, '__apidoc__', {})
        if doc is False:
            return False
        doc['name'] = resource.__name__
        params = merge(self.expected_params(doc), doc.get('params', {}))
        params = merge(params, extract_path_params(url))
        doc['params'] = params
        for method in [m.lower() for m in resource.methods or []]:
            method_doc = doc.get(method, OrderedDict())
            method_impl = getattr(resource, method)
            if hasattr(method_impl, 'im_func'):
                method_impl = method_impl.im_func
            elif hasattr(method_impl, '__func__'):
                method_impl = method_impl.__func__
            method_doc = merge(method_doc, getattr(method_impl, '__apidoc__', OrderedDict()))
            if method_doc is not False:
                method_doc['docstring'] = parse_docstring(method_impl)
                method_params = self.expected_params(method_doc)
                method_params = merge(method_params, method_doc.get('params', {}))
                inherited_params = dict((k, v) for k, v in iteritems(params) if k in method_params)
                method_doc['params'] = merge(inherited_params, method_params)
            doc[method] = method_doc
        return doc

    def expected_params(self, doc):
        params = {}
        if 'expect' not in doc:
            return params

        for expect in doc.get('expect', []):
            if isinstance(expect, RequestParser):
                parser_params = dict((p['name'], p) for p in expect.__schema__)
                params.update(parser_params)
            elif isinstance(expect, ModelBase):
                params['payload'] = not_none({
                    'name': 'payload',
                    'required': True,
                    'in': 'body',
                    'schema': self.serialize_schema(expect),
                })
            elif isinstance(expect, (list, tuple)):
                if len(expect) == 2:
                    # this is (payload, description) shortcut
                    model, description = expect
                    params['payload'] = not_none({
                        'name': 'payload',
                        'required': True,
                        'in': 'body',
                        'schema': self.serialize_schema(model),
                        'description': description
                    })
                else:
                    params['payload'] = not_none({
                        'name': 'payload',
                        'required': True,
                        'in': 'body',
                        'schema': self.serialize_schema(expect),
                    })
        return params

    def register_errors(self):
        responses = {}
        for exception, handler in self.api.error_handlers.items():
            doc = parse_docstring(handler)
            response = {
                'description': doc['summary']
            }
            apidoc = getattr(handler, '__apidoc__', {})
            if 'params' in apidoc:
                response['headers'] = dict(
                    (n, _param_to_header(o))
                    for n, o in apidoc['params'].items() if o.get('in') == 'header'
                )
            if 'responses' in apidoc:
                _, model = list(apidoc['responses'].values())[0]
                response['schema'] = self.serialize_schema(model)
            responses[exception.__name__] = not_none(response)
        return responses

    def serialize_resource(self, ns, resource, url, kwargs):
        doc = self.extract_resource_doc(resource, url)
        if doc is False:
            return
        path = {
            'parameters': self.parameters_for(doc) or None
        }
        for method in [m.lower() for m in resource.methods or []]:
            methods = [m.lower() for m in kwargs.get('methods', [])]
            if doc[method] is False or methods and method not in methods:
                continue
            path[method] = self.serialize_operation(doc, method)
            path[method]['tags'] = [ns.name]
        return not_none(path)

    def serialize_operation(self, doc, method):
        operation = {
            'responses': self.responses_for(doc, method) or None,
            'summary': doc[method]['docstring']['summary'],
            'description': self.description_for(doc, method) or None,
            'operationId': self.operation_id_for(doc, method),
            'parameters': self.parameters_for(doc[method]) or None,
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

    def description_for(self, doc, method):
        '''Extract the description metadata and fallback on the whole docstring'''
        parts = []
        if 'description' in doc:
            parts.append(doc['description'])
        if method in doc and 'description' in doc[method]:
            parts.append(doc[method]['description'])
        if doc[method]['docstring']['details']:
            parts.append(doc[method]['docstring']['details'])

        return '\n'.join(parts).strip()

    def operation_id_for(self, doc, method):
        '''Extract the operation id'''
        return doc[method]['id'] if 'id' in doc[method] else self.api.default_id(doc['name'], method)

    def parameters_for(self, doc):
        params = []
        for name, param in iteritems(doc['params']):
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

        # Handle fields mask
        mask = doc.get('__mask__')
        if (mask and current_app.config['RESTPLUS_MASK_SWAGGER']):
            param = {
                'name': current_app.config['RESTPLUS_MASK_HEADER'],
                'in': 'header',
                'type': 'string',
                'format': 'mask',
                'description': 'An optional fields mask',
            }
            if isinstance(mask, string_types):
                param['default'] = mask
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

            if 'docstring' in d:
                for name, description in d['docstring']['raises'].items():
                    for exception, handler in self.api.error_handlers.items():
                        error_responses = getattr(handler, '__apidoc__', {}).get('responses', {})
                        code = list(error_responses.keys())[0] if error_responses else None
                        if code and exception.__name__ == name:
                            responses[code] = {'$ref': '#/responses/{0}'.format(name)}
                            break

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

        elif isinstance(model, ModelBase):
            self.register_model(model)
            return ref(model)

        elif isinstance(model, string_types):
            self.register_model(model)
            return ref(model)

        elif isclass(model) and issubclass(model, fields.Raw):
            return self.serialize_schema(model())

        elif isinstance(model, fields.Raw):
            return model.__schema__

        elif isinstance(model, (type, type(None))) and model in PY_TYPES:
            return {'type': PY_TYPES[model]}

        raise ValueError('Model {0} not registered'.format(model))

    def register_model(self, model):
        name = model.name if isinstance(model, ModelBase) else model
        if name not in self.api.models:
            raise ValueError('Model {0} not registered'.format(name))
        specs = self.api.models[name]
        self._registered_models[name] = specs
        if isinstance(specs, ModelBase):
            for parent in specs.__parents__:
                self.register_model(parent)
        if isinstance(specs, Model):
            for field in itervalues(specs):
                self.register_field(field)
        return ref(model)

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
