# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
import six
import warnings

from wsgiservice.resource import Resource as wsgiservice_resource

# from .errors import abort
# from .marshalling import marshal, marshal_with
from .model import Model
# from .reqparse import RequestParser
from .utils import merge


from wsgiservice_adaptors import get_resource_http_methods


# TODO: FUL-3375 Specify authentication schemes on the namespace level
# TODO: FUL-3505 Possibly specify specialized error handling on the namespace level
# TODO: FUL-3376
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
    def __init__(self, name, description=None, path='/', decorators=None, validate=None, **kwargs):
        self.name = name
        self.description = description
        self.path = path.rstrip('/') + '/' if path else ('/' + name + '/')

        # self._schema = None # unused attribute
        self._validate = validate
        self.models = {}
        # # TODO: Provide explicit security/error handling interface instead of passing callbacks
        # self.decorators = decorators if decorators else []
        self.resources = []
        # self.error_handlers = {}
        # self.default_error_handler = None
        self.apis = []
        if 'api' in kwargs:
            self.apis.append(kwargs['api'])

    ### Add resource to namespace (maintained in triple of resource class, urls (with added namespace prefix path)
    ### and any extra labels such as endpoint name, resource constructor named/keyword arguments in list/tuple or dict
    ### form)
    def add_resource(self, resource, url, **kwargs):
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
        self.resources.append((resource, url, kwargs))
        for api in self.apis:
            api.register_resource(self, resource, url, **kwargs)

    def route(self, url, **kwargs):
        '''
        A decorator to route resources.
        '''
        if url[0] != '/':
            raise ValueError
        if len(url) > 1:
            url = self.path.rstrip('/') + url
        elif len(self.path) > 1:
            url = self.path.rstrip('/')
        else:
            url = self.path

        def wrapper(cls):
            doc = kwargs.pop('doc', None)
            if doc is not None:
                self._handle_api_doc(cls, doc)
            # the following implements the side-effects of the wsgiservice mount decorator
            if getattr(cls,'_path',None) is None:
                cls._path = url
            else:
                if cls._path != url:
                    raise ValueError

            self.add_resource(cls, url, **kwargs)
            return cls
        return wrapper


    # Adds documentation dictionary (obtained from keyword arguments passed to Namespace.doc)
    # with prexisting __apidoc__ function/class attribute (after adapting 'params' and 'parser'/
    # 'body' entries). In case of doc == False the __apidoc__ attribute is set to false
    def _handle_api_doc(self, cls, doc):
        if doc is False:
            cls.__apidoc__ = False
            return
        unshortcut_params_description(doc)
        handle_deprecations(doc)
        for http_method in [method.lower() for method in get_resource_http_methods(cls)]:
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

    # ### error handling
    # # TODO: FUL-3505
    # def abort(self, *args, **kwargs):
    #     '''
    #     Properly abort the current request
    #
    #     See: :func:`~flask_restplus.errors.abort`
    #     '''
    #     abort(*args, **kwargs)


    ### Adding models ("interface types") to the Namespace.models Model instance dictionary
    ### that contains parts of the Model type hierarchy relevant to this namespace of the API

    # Add model to the namespace
    def add_model(self, name, definition):
        self.models[name] = definition
        for api in self.apis:
            api.models[name] = definition
        return definition

    # TODO: FUL-3376 Clean up mask
    def model(self, name=None, model=None, mask=None, **kwargs):
        '''
        Register a model

        .. seealso:: :class:`Model`
        '''
        model = Model(name, model, mask=mask)
        model.__apidoc__.update(kwargs)
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


    ### Parameter models ###

    # Parameter model annotation (validation is done in the Resource base class)
    def expect(self, *inputs, **kwargs):
        '''
        A decorator to Specify the expected input model

        :param Model|Parse inputs: An expect model or request parser
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


    ### Response models ###

    # Possibly affects marshal_with
    def as_list(self, field):
        '''Allow to specify nested lists for documentation'''
        field.__apidoc__ = merge(getattr(field, '__apidoc__', {}), {'as_list': True})
        return field

    # Response model annotation and rearrangement of return value of decorated method
    # TODO: FUL-3376 mask
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
                # '__mask__': kwargs.get('mask', True),  # Mask values can't be determined outside app context
            }
            func.__apidoc__ = merge(getattr(func, '__apidoc__', {}), doc)
            # deleted: marshal_with(fields, **kwargs)(func)
            return func
        return wrapper

    def marshal_list_with(self, fields, **kwargs):
        '''A shortcut decorator for :meth:`~Api.marshal_with` with ``as_list=True``'''
        return self.marshal_with(fields, True, **kwargs)


    ### Error handler registry ###
    # # TODO: FUL-3505
    # # Error handling in this way is Flask-specific and implemented differently in the
    # # __call__ operator of the wsgiservice.Resource base class
    # def errorhandler(self, exception):
    #     '''A decorator to register an error handler for a given exception'''
    #     if inspect.isclass(exception) and issubclass(exception, Exception):
    #         # Register an error handler for a given exception
    #         def wrapper(func):
    #             self.error_handlers[exception] = func
    #             return func
    #         return wrapper
    #     else:
    #         # Register the default error handler
    #         self.default_error_handler = exception
    #         return exception


    ### Simple parameter annotation ###
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

    ### Simple response annotation ###
    def response(self, code, description, model=None, **kwargs):
        '''
        A decorator to specify one of the expected responses

        :param int code: the HTTP status code
        :param str description: a small description about the response
        :param Model model: an optional response model

        '''
        return self.doc(responses={code: (description, model) if model else description})

    ### Simple header annotation ###
    def header(self, name, description=None, **kwargs):
        '''
        A decorator to specify one of the expected headers

        :param str name: the HTTP header name
        :param str description: a description about the header

        '''
        return self.param(name, description=description, _in='header', **kwargs)

    ### Simple deprecated annotation ###
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
