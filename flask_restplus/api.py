# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import six

from flask import url_for, request
from flask.ext import restful

from jsonschema import RefResolver

from werkzeug import cached_property
from werkzeug.exceptions import HTTPException

from . import apidoc
from .model import ApiModel
from .namespace import ApiNamespace
from .postman import PostmanCollectionV1
from .resource import Resource
from .swagger import Swagger
from .utils import merge, default_id
from .reqparse import RequestParser


class Api(restful.Api):
    '''
    The main entry point for the application.
    You need to initialize it with a Flask Application: ::

    >>> app = Flask(__name__)
    >>> api = Api(app)

    Alternatively, you can use :meth:`init_app` to set the Flask application
    after it has been constructed.

    The endpoint parameter prefix all views and resources:

        - The API root/documentation will be ``{endpoint}.root``
        - A resource registered as 'resource' will be available as ``{endpoint}.resource``

    :param app: the Flask application object
    :type app: flask.Flask

    :param version: The API version (used in Swagger documentation)
    :type version: str

    :param title: The API title (used in Swagger documentation)
    :type title: str

    :param description: The API description (used in Swagger documentation)
    :type description: str

    :param terms_url: The API terms page URL (used in Swagger documentation)
    :type terms_url: str

    :param contact: A contact email for the API (used in Swagger documentation)
    :type contact: str

    :param license: The license associated to the API (used in Swagger documentation)
    :type license: str

    :param license_url: The license page URL (used in Swagger documentation)
    :type license_url: str

    :param endpoint: The API base endpoint (default to 'api).
    :type endpoint: str

    :param default: The default namespace base name (default to 'default')
    :type default: str

    :param default_label: The default namespace label (used in Swagger documentation)
    :type default_label: str

    :param default_mediatype: The default media type to return
    :type default_mediatype: str

    :param validate: Whether or not the API should perform input payload validation.
    :type validate: bool

    :param decorators: Decorators to attach to every resource
    :type decorators: list

    :param catch_all_404s: Use :meth:`handle_error`
        to handle 404 errors throughout your app
    :param url_part_order: A string that controls the order that the pieces
        of the url are concatenated when the full url is constructed.  'b'
        is the blueprint (or blueprint registration) prefix, 'a' is the api
        prefix, and 'e' is the path component the endpoint is added with
    :type catch_all_404s: bool

    :param errors: A dictionary to define a custom response for each
        exception or error raised during a request
    :type errors: dict

    :param authorizations: A Swagger Authorizations declaration as dictionary
    :type authorizations: dict

    '''

    def __init__(self, app=None, version='1.0', title=None, description=None,
            terms_url=None, license=None, license_url=None,
            contact=None, contact_url=None, contact_email=None,
            authorizations=None, security=None, ui=True, default_id=default_id,
            default='default', default_label='Default namespace', validate=None, **kwargs):
        self.version = version
        self.title = title or 'API'
        self.description = description
        self.terms_url = terms_url
        self.contact = contact
        self.contact_email = contact_email
        self.contact_url = contact_url
        self.license = license
        self.license_url = license_url
        self.authorizations = authorizations
        self.security = security
        self.ui = ui
        self.default_id = default_id
        self.validate = validate

        self._error_handlers = {}
        self._schema = None
        self.models = {}
        self._refresolver = None
        self.namespaces = []
        self.default_namespace = ApiNamespace(self, default, default_label,
            endpoint='{0}-declaration'.format(default),
            path='/'
        )
        self.add_namespace(self.default_namespace)
        super(Api, self).__init__(app, **kwargs)

    def init_app(self, app, **kwargs):
        self.title = kwargs.get('title', self.title)
        self.description = kwargs.get('description', self.description)
        self.terms_url = kwargs.get('terms_url', self.terms_url)
        self.contact = kwargs.get('contact', self.contact)
        self.contact_url = kwargs.get('contact_url', self.contact_url)
        self.contact_email = kwargs.get('contact_email', self.contact_email)
        self.license = kwargs.get('license', self.license)
        self.license_url = kwargs.get('license_url', self.license_url)

        if kwargs.get('add_specs', True):
            self.add_resource(self.swagger_view(), '/swagger.json', endpoint='specs', doc=False)

        super(Api, self).init_app(app)

        if self.blueprint:
            self.blueprint.add_url_rule('/', 'root', self.render_root)

    def _init_app(self, app):
        super(Api, self)._init_app(app)
        if not self.blueprint:
            app.add_url_rule('/', 'root', self.render_root)
        self.register_apidoc(app)
        self.validate = self.validate if self.validate is not None else app.config.get('RESTPLUS_VALIDATE', False)

    def register_apidoc(self, app):
        conf = app.extensions.setdefault('restplus', {})
        if not conf.get('apidoc_registered', False):
            app.register_blueprint(apidoc.apidoc)
        conf['apidoc_registered'] = True

    def swagger_view(self):
        class SwaggerView(Resource):
            api = self

            def get(self):
                return self.api.__schema__

            def mediatypes(self):
                return ['application/json']
        return SwaggerView

    def render_root(self):
        '''Override this method to customize the documentation page'''
        if not self.ui:
            self.abort(404)
        return apidoc.ui_for(self)

    def add_resource(self, resource, *urls, **kwargs):
        '''Register a Swagger API declaration for a given API Namespace'''
        kwargs['endpoint'] = str(kwargs.pop('endpoint', None) or resource.__name__.lower())
        if kwargs.pop('doc', True) and not kwargs.pop('namespace', None):
            self.default_namespace.resources.append((resource, urls, kwargs))

        args = kwargs.pop('resource_class_args', [])
        if isinstance(args, tuple):
            args = list(args)
        args.insert(0, self)
        kwargs['resource_class_args'] = args

        super(Api, self).add_resource(resource, *urls, **kwargs)

    def add_namespace(self, ns):
        if ns not in self.namespaces:
            self.namespaces.append(ns)

    def namespace(self, *args, **kwargs):
        ns = ApiNamespace(self, *args, **kwargs)
        self.add_namespace(ns)
        return ns

    def route(self, *urls, **kwargs):
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
        for key in 'get', 'post', 'put', 'delete', 'options', 'head', 'patch':
            if key in doc:
                if doc[key] is False:
                    continue
                unshortcut_params_description(doc[key])
        cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), doc)

    def endpoint(self, name):
        if self.blueprint:
            return '{0}.{1}'.format(self.blueprint.name, name)
        else:
            return name

    @property
    def specs_url(self):
        return url_for(self.endpoint('specs'), _external=True)

    @property
    def base_url(self):
        return url_for(self.endpoint('root'), _external=True)

    @property
    def base_path(self):
        return url_for(self.endpoint('root'))

    @cached_property
    def __schema__(self):
        if not self._schema:
            self._schema = Swagger(self).as_dict()
        return self._schema

    def doc(self, shortcut=None, **kwargs):
        '''Add some api documentation to the decorated object'''
        if isinstance(shortcut, six.text_type):
            kwargs['id'] = shortcut
        show = shortcut if isinstance(shortcut, bool) else True

        def wrapper(documented):
            self._handle_api_doc(documented, kwargs if show else False)
            return documented
        return wrapper

    def hide(self, func):
        return self.doc(False)(func)

    def abort(self, code=500, message=None, **kwargs):
        '''Properly abort the current request'''
        if message or kwargs and 'status' not in kwargs:
            kwargs['status'] = code
        if message:
            kwargs['message'] = str(message)
        restful.abort(code, **kwargs)

    def model(self, name=None, model=None, **kwargs):
        '''
        Register a model

        Model can be either a dictionary or a fields. Raw subclass.
        '''
        if isinstance(model, dict):
            model = ApiModel(model)
            model.__apidoc__ = kwargs
            model.__apidoc__['name'] = name
            self.models[name] = model
            return model
        else:
            def wrapper(cls):
                cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), kwargs)
                cls.__apidoc__['name'] = name or cls.__name__
                self.models[name or cls.__name__] = kwargs.get('fields', cls)
                return cls
            return wrapper

    def extend(self, name, parent, fields):
        '''
        Extend a model (Duplicate all fields)
        '''
        if isinstance(parent, list):
            parents = []

            for item in parent:
                parents.append(copy.deepcopy(item))

            parent = {}

            for value in parents:
                parent.update(value)

        model = ApiModel(copy.deepcopy(parent))
        model.__apidoc__['name'] = name
        model.update(fields)
        self.models[name] = model
        return model

    def inherit(self, name, parent, fields):
        '''
        Inherit a modal (use the Swagger composition pattern aka. allOf)
        '''
        model = ApiModel(fields)
        model.__apidoc__['name'] = name
        model.__parent__ = parent
        self.models[name] = model
        return model

    def expect(self, body, validate=None):
        '''Specify the expected input model'''
        return self.doc(body=body, validate=validate or self.validate)

    def parser(self):
        '''Instanciate a RequestParser'''
        return RequestParser()

    def as_list(self, field):
        '''Allow to specify nested lists for documentation'''
        field.__apidoc__ = merge(getattr(field, '__apidoc__', {}), {'as_list': True})
        return field

    def marshal_with(self, fields, as_list=False, code=200, description=None, **kwargs):
        '''
        A decorator specifying the fields to use for serialization.

        :param as_list: Indicate that the return type is a list (for the documentation)
        :type as_list: bool
        :param code: Optionnaly give the expected HTTP response code if its different from 200
        :type code: integer
        '''
        def wrapper(func):
            doc = {
                'responses': {
                    code: (description, [fields]) if as_list else (description, fields)
                }
            }
            # doc = {'model': [fields]} if as_list else {'model': fields}
            # doc['default_code'] = code
            # doc['description'] = description
            func.__apidoc__ = merge(getattr(func, '__apidoc__', {}), doc)
            resolved = getattr(fields, 'resolved', fields)
            return restful.marshal_with(resolved, **kwargs)(func)
        return wrapper

    def marshal_list_with(self, fields, **kwargs):
        '''A shortcut decorator for ``marshal_with(as_list=True, code=code)``'''
        return self.marshal_with(fields, True, **kwargs)

    def marshal(self, data, fields):
        '''A shortcut to the ``marshal`` helper'''
        resolved = getattr(fields, 'resolved', fields)
        return restful.marshal(data, resolved)

    def errorhandler(self, exception):
        '''Register an error handler for a given exception'''
        def wrapper(func):
            self._error_handlers[exception] = func
            return func
        return wrapper

    def handle_error(self, e):
        if e.__class__ in self._error_handlers:
            handler = self._error_handlers[e.__class__]
            result = handler(e)
            e = HTTPException(str(e))
            e.data, e.code = result if len(result) == 2 else (result, 500)
        return super(Api, self).handle_error(e)

    def response(self, code, description, model=None, **kwargs):
        '''Specify one of the expected responses'''
        return self.doc(responses={code: (description, model) if model else description})

    def header(self, name, description=None, **kwargs):
        '''Specify one of the expected headers'''
        param = kwargs
        param['in'] = 'header'
        param['description'] = description
        return self.doc(params={name: param})

    def deprecated(self, func):
        '''Mark a resource or a method as deprecated'''
        return self.doc(deprecated=True)(func)

    def as_postman(self, urlvars=False, swagger=False):
        return PostmanCollectionV1(self, swagger=swagger).as_dict(urlvars=urlvars)

    @property
    def payload(self):
        return request.get_json()

    @property
    def refresolver(self):
        if not self._refresolver:
            self._refresolver = RefResolver.from_schema(self.__schema__)
        return self._refresolver


def unshortcut_params_description(data):
    if 'params' in data:
        for name, description in six.iteritems(data['params']):
            if isinstance(description, six.string_types):
                data['params'][name] = {'description': description}
