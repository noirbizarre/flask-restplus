# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import MutableMapping

from flask import url_for, Blueprint, render_template, redirect
from flask.ext import restful

from .namespace import ApiNamespace
from .swagger import ApiSpecs, ApiDeclaration
from .utils import merge


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

    :param prefix: Prefix all routes with a value, eg v1 or 2010-04-01
    :type prefix: str

    :param default_mediatype: The default media type to return
    :type default_mediatype: str

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
            terms_url=None, contact=None, license=None, license_url=None,
            endpoint='api', prefix=None, authorizations=None,
            default='default', default_label='Default namespace', **kwargs):
        self.version = version
        self.title = title
        self.description = description
        self.terms_url = terms_url
        self.contact = contact
        self.license = license
        self.license_url = license_url
        self.endpoint = endpoint
        self.authorizations = authorizations

        self.models = {}
        self.namespaces = []
        self.default_namespace = ApiNamespace(self, '', default_label,
            endpoint='{0}-declaration'.format(default),
            json_path='/{0}.json'.format(default)
        )

        self.blueprint = Blueprint(self.endpoint, __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/swaggerui',
            url_prefix=prefix,
        )

        @self.blueprint.route('/images/throbber.gif')
        def fix_throbber():
            return redirect(url_for('.static'.format(self.endpoint),
                filename='bower/swagger-ui/dist/images/throbber.gif'
            ))

        self.blueprint.record(self._deferred_blueprint_init)

        super(Api, self).__init__(self.blueprint, **kwargs)

        view_func = self.output(ApiSpecs.as_view(str('specs'), api=self))
        url = self._complete_url('/specs.json', '')
        self.blueprint.add_url_rule(url, view_func=view_func)
        self.blueprint.add_url_rule('/', 'root', self.render_ui)
        self.blueprint.add_app_template_global(self.swagger_static)
        self.add_namespace(self.default_namespace)

        if app:
            app.register_blueprint(self.blueprint)

    def init_app(self, app, **kwargs):
        if isinstance(app, Blueprint):
            return
        self.title = kwargs.get('title', self.title)
        self.description = kwargs.get('description', self.description)
        self.terms_url = kwargs.get('terms_url', self.terms_url)
        self.contact = kwargs.get('contact', self.contact)
        self.license = kwargs.get('license', self.license)
        self.license_url = kwargs.get('license_url', self.license_url)

        app.register_blueprint(self.blueprint)

    def render_ui(self):
        '''Override this method to customize the documentation page'''
        return render_template('swagger-ui.html', api_endpoint=self.endpoint, specs_url=self.specs_url)

    def swagger_static(self, filename):
        return url_for(
            '{0}.static'.format(self.endpoint),
            filename='bower/swagger-ui/dist/{0}'.format(filename)
        )

    def _register_namespace(self, ns):
        '''Register a Swagger API declaration for a given API Namespace'''
        endpoint = str(ns.endpoint)
        view_func = self.output(ApiDeclaration.as_view(endpoint, api=self, namespace=ns))
        url = self._complete_url(ns.json_path, '')
        self.blueprint.add_url_rule(url, view_func=view_func)

    def _register_view(self, app, resource, *urls, **kwargs):
        super(Api, self)._register_view(app, resource, *urls, **kwargs)
        # Ugly fix on owned endpoints
        prefix = '{0}.'.format(self.blueprint.name)
        self.endpoints = set(e if e.startswith(prefix) else ''.join((prefix, e)) for e in self.endpoints)

    def add_resource(self, resource, *urls, **kwargs):
        '''Register a Swagger API declaration for a given API Namespace'''
        kwargs['endpoint'] = str(kwargs.pop('endpoint', None) or resource.__name__.lower())
        if not kwargs.pop('namespace', None):
            self.default_namespace.resources.append((resource, urls, kwargs))

        # If blueprint is already registered, force URL declaration
        if self.blueprint_setup:
            kwargs['endpoint'] = str('{0}.{1}'.format(self.blueprint.name, kwargs['endpoint']))
            self._register_view(self.blueprint_setup.app, resource, *urls, **kwargs)
        else:
            super(Api, self).add_resource(resource, *urls, **kwargs)

    def add_namespace(self, ns):
        if ns not in self.namespaces:
            view_func = self.output(ApiDeclaration.as_view(ns.endpoint, api=self, namespace=ns))
            url = self._complete_url(ns.json_path, '')
            self.namespaces.append(ns)
            self.endpoints.add(ns.endpoint)
            if self.blueprint_setup:
                # Set the rule to a string directly, as the blueprint is already set up.
                self.blueprint_setup.add_url_rule(url, view_func=view_func)
            else:
                self.blueprint.add_url_rule(url, view_func=view_func)

    def namespace(self, *args, **kwargs):
        ns = ApiNamespace(self, *args, **kwargs)
        self.add_namespace(ns)
        return ns

    def route(self, *urls, **kwargs):
        def wrapper(cls):
            doc = kwargs.pop('doc', None)
            if doc:
                self._handle_api_doc(cls, doc)
            self.add_resource(cls, *urls, **kwargs)
            return cls
        return wrapper

    def _handle_api_doc(self, cls, doc):
        unshortcut_params_description(doc)
        for key in 'get', 'post', 'put', 'delete':
            if key in doc:
                unshortcut_params_description(doc[key])
        cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), doc)

    @property
    def specs_url(self):
        return url_for('{0}.specs'.format(self.endpoint), _external=True)

    @property
    def base_url(self):
        return url_for('{0}.root'.format(self.endpoint), _external=True)

    def doc(self, **kwargs):
        '''Add some api documentation to the decorated object'''
        def wrapper(documented):
            self._handle_api_doc(documented, kwargs)
            return documented
        return wrapper

    def owns_endpoint(self, endpoint):
        '''Override the default implementation as there is always a Blueprint'''
        return endpoint in self.endpoints

    def abort(self, code=500, message=None, **kwargs):
        '''Properly abort the current request'''
        if message or kwargs and 'status' not in kwargs:
            kwargs['status'] = code
        if message:
            kwargs['message'] = str(message)
        restful.abort(code, **kwargs)

    def model(self, name, model=None, **kwargs):
        '''
        Register a model

        Model can be either a dictionnary or a class.
        '''
        if isinstance(model, dict):
            model = ApiModel(model)
            model.__apidoc__['name'] = name
            self.models[name] = model
            return model
        else:
            def wrapper(cls):
                cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), kwargs)
                cls.__apidoc__['name'] = name
                return cls
            return wrapper

    def parser(self):
        '''Instanciate a RequestParser'''
        return restful.reqparse.RequestParser()

    def as_list(self, field):
        '''Allow to specify nested lists for documentation'''
        field.__apidoc__ = merge(getattr(field, '__apidoc__', {}), {'as_list': True})
        return field

    def marshal_with(self, fields, as_list=False):
        '''
        A decorator specifying the fields to use for serialization

        :param as_list: Indicate that the return type is a list (for the documentation)
        :type as_list: bool
        '''
        def wrapper(func):
            doc = {'model': [fields]} if as_list else {'model': fields}
            func.__apidoc__ = merge(getattr(func, '__apidoc__', {}), doc)
            return restful.marshal_with(fields)(func)
        return wrapper

    def marshal_list_with(self, fields):
        '''A shortcut decorator for ``marshal_with(as_list=True)``'''
        return self.marshal_with(fields, True)

    marshal = restful.marshal


class ApiModel(dict, MutableMapping):
    def __init__(self, *args, **kwargs):
        self.__apidoc__ = {}
        super(ApiModel, self).__init__(*args, **kwargs)


def unshortcut_params_description(data):
    if 'params' in data:
        for name, description in data['params'].items():
            if isinstance(description, basestring):
                data['params'][name] = {'description': description}
