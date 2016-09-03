# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
import six
import warnings

from flask.views import http_method_funcs

from .errors import abort
from .marshalling import marshal, marshal_with
from .model import Model, SchemaModel
from .reqparse import RequestParser
from .utils import merge


class Namespace(object):
    '''
    Group resources together.

    Namespace is to API what :class:`flask:flask.Blueprint` is for :class:`flask:flask.Flask`.

    :param str name: The namespace name
    :param str description: An optionale short description
    :param str path: An optional prefix path. If not provided, prefix is ``/+name``
    :param list decorators: A list of decorators to apply to each resources
    :param bool validate: Whether or not to perform validation on this namespace
    :param Api api: an optional API to attache to the namespace
    '''
    def __init__(self, name, description=None, path=None, decorators=None, validate=None, **kwargs):
        self.name = name
        self.description = description
        self._path = path

        self._schema = None
        self._validate = validate
        self.models = {}
        self.urls = {}
        self.decorators = decorators if decorators else []
        self.resources = []
        self.error_handlers = {}
        self.default_error_handler = None
        self.apis = []
        if 'api' in kwargs:
            self.apis.append(kwargs['api'])
            
    @property
    def path(self):
        return (self._path or ('/' + self.name)).rstrip('/')

    def add_resource(self, resource, *urls, **kwargs):
        '''
        Register a Resource for a given API Namespace

        :param Resource resource: the resource ro register
        :param str urls: one or more url routes to match for the resource,
                         standard flask routing rules apply.
                         Any url variables will be passed to the resource method as args.
        :param str endpoint: endpoint name (defaults to :meth:`Resource.__name__.lower`
            Can be used to reference this route in :class:`fields.Url` fields
        :param list|tuple resource_class_args: args to be forwarded to the constructor of the resource.
        :param dict resource_class_kwargs: kwargs to be forwarded to the constructor of the resource.

        Additional keyword arguments not specified above will be passed as-is
        to :meth:`flask.Flask.add_url_rule`.

        Examples::

            namespace.add_resource(HelloWorld, '/', '/hello')
            namespace.add_resource(Foo, '/foo', endpoint="foo")
            namespace.add_resource(FooSpecial, '/special/foo', endpoint="foo")
        '''
        self.resources.append((resource, urls, kwargs))
        for api in self.apis:
            ns_urls = api.ns_urls(self, urls)
            api.register_resource(self, resource, *ns_urls, **kwargs)

    def route(self, *urls, **kwargs):
        '''
        A decorator to route resources.
        '''
        def wrapper(cls):
            doc = kwargs.pop('doc', None)
            if doc is not None:
                self._handle_api_doc(cls, doc)
            self.add_resource(cls, *urls, **kwargs)
            return cls
        return wrapper

    def _handle_api_doc(self, cls, doc):
        if doc is False:
            cls.__apidoc__ = False
            return
        unshortcut_params_description(doc)
        handle_deprecations(doc)
        for http_method in http_method_funcs:
            if http_method in doc:
                if doc[http_method] is False:
                    continue
                unshortcut_params_description(doc[http_method])
                handle_deprecations(doc[http_method])
                if 'expect' in doc[http_method] and not isinstance(doc[http_method]['expect'], (list, tuple)):
                    doc[http_method]['expect'] = [doc[http_method]['expect']]
        cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), doc)

    def doc(self, shortcut=None, **kwargs):
        '''A decorator to add some api documentation to the decorated object'''
        if isinstance(shortcut, six.text_type):
            kwargs['id'] = shortcut
        show = shortcut if isinstance(shortcut, bool) else True

        def wrapper(documented):
            self._handle_api_doc(documented, kwargs if show else False)
            return documented
        return wrapper

    def hide(self, func):
        '''A decorator to hide a resource or a method from specifications'''
        return self.doc(False)(func)

    def abort(self, *args, **kwargs):
        '''
        Properly abort the current request

        See: :func:`~flask_restplus.errors.abort`
        '''
        abort(*args, **kwargs)

    def add_model(self, name, definition):
        self.models[name] = definition
        for api in self.apis:
            api.models[name] = definition
        return definition

    def model(self, name=None, model=None, mask=None, **kwargs):
        '''
        Register a model

        .. seealso:: :class:`Model`
        '''
        model = Model(name, model, mask=mask)
        model.__apidoc__.update(kwargs)
        return self.add_model(name, model)

    def schema_model(self, name=None, schema=None):
        '''
        Register a model

        .. seealso:: :class:`Model`
        '''
        model = SchemaModel(name, schema)
        return self.add_model(name, model)

    def extend(self, name, parent, fields):
        '''
        Extend a model (Duplicate all fields)

        :deprecated: since 0.9. Use :meth:`clone` instead
        '''
        if isinstance(parent, list):
            parents = parent + [fields]
            model = Model.extend(name, *parents)
        else:
            model = Model.extend(name, parent, fields)
        return self.add_model(name, model)

    def clone(self, name, *specs):
        '''
        Clone a model (Duplicate all fields)

        :param str name: the resulting model name
        :param specs: a list of models from which to clone the fields

        .. seealso:: :meth:`Model.clone`

        '''
        model = Model.clone(name, *specs)
        return self.add_model(name, model)

    def inherit(self, name, *specs):
        '''
        Inherit a modal (use the Swagger composition pattern aka. allOf)

        .. seealso:: :meth:`Model.inherit`
        '''
        model = Model.inherit(name, *specs)
        return self.add_model(name, model)

    def expect(self, *inputs, **kwargs):
        '''
        A decorator to Specify the expected input model

        :param ModelBase|Parse inputs: An expect model or request parser
        :param bool validate: whether to perform validation or not

        '''
        expect = []
        params = {
            'validate': kwargs.get('validate', None) or self._validate,
            'expect': expect
        }
        for param in inputs:
            expect.append(param)
        return self.doc(**params)

    def parser(self):
        '''Instanciate a :class:`~RequestParser`'''
        return RequestParser()

    def as_list(self, field):
        '''Allow to specify nested lists for documentation'''
        field.__apidoc__ = merge(getattr(field, '__apidoc__', {}), {'as_list': True})
        return field

    def marshal_with(self, fields, as_list=False, code=200, description=None, **kwargs):
        '''
        A decorator specifying the fields to use for serialization.

        :param bool as_list: Indicate that the return type is a list (for the documentation)
        :param int code: Optionally give the expected HTTP response code if its different from 200

        '''
        def wrapper(func):
            doc = {
                'responses': {
                    code: (description, [fields]) if as_list else (description, fields)
                },
                '__mask__': kwargs.get('mask', True),  # Mask values can't be determined outside app context
            }
            func.__apidoc__ = merge(getattr(func, '__apidoc__', {}), doc)
            return marshal_with(fields, **kwargs)(func)
        return wrapper

    def marshal_list_with(self, fields, **kwargs):
        '''A shortcut decorator for :meth:`~Api.marshal_with` with ``as_list=True``'''
        return self.marshal_with(fields, True, **kwargs)

    def marshal(self, *args, **kwargs):
        '''A shortcut to the :func:`marshal` helper'''
        return marshal(*args, **kwargs)

    def errorhandler(self, exception):
        '''A decorator to register an error handler for a given exception'''
        if inspect.isclass(exception) and issubclass(exception, Exception):
            # Register an error handler for a given exception
            def wrapper(func):
                self.error_handlers[exception] = func
                return func
            return wrapper
        else:
            # Register the default error handler
            self.default_error_handler = exception
            return exception

    def param(self, name, description=None, _in='query', **kwargs):
        '''
        A decorator to specify one of the expected parameters

        :param str name: the parameter name
        :param str description: a small description
        :param str _in: the parameter location `(query|header|formData|body|cookie)`
        '''
        param = kwargs
        param['in'] = _in
        param['description'] = description
        return self.doc(params={name: param})

    def response(self, code, description, model=None, **kwargs):
        '''
        A decorator to specify one of the expected responses

        :param int code: the HTTP status code
        :param str description: a small description about the response
        :param ModelBase model: an optional response model

        '''
        return self.doc(responses={code: (description, model) if model else description})

    def header(self, name, description=None, **kwargs):
        '''
        A decorator to specify one of the expected headers

        :param str name: the HTTP header name
        :param str description: a description about the header

        '''
        return self.param(name, description=description, _in='header', **kwargs)

    def deprecated(self, func):
        '''A decorator to mark a resource or a method as deprecated'''
        return self.doc(deprecated=True)(func)


def unshortcut_params_description(data):
    if 'params' in data:
        for name, description in six.iteritems(data['params']):
            if isinstance(description, six.string_types):
                data['params'][name] = {'description': description}


def handle_deprecations(doc):
    if 'parser' in doc:
        warnings.warn('The parser attribute is deprecated, use expect instead', DeprecationWarning, stacklevel=2)
        doc['expect'] = doc.get('expect', []) + [doc.pop('parser')]
    if 'body' in doc:
        warnings.warn('The body attribute is deprecated, use expect instead', DeprecationWarning, stacklevel=2)
        doc['expect'] = doc.get('expect', []) + [doc.pop('body')]
