# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import difflib
import inspect
import re
import six
import sys

from flask import url_for, request, current_app
from flask.signals import got_request_exception

import flask_restful as restful

from jsonschema import RefResolver

from werkzeug import cached_property
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from werkzeug.http import HTTP_STATUS_CODES

from . import apidoc
from .errors import abort
from .marshalling import marshal, marshal_with
from .model import Model
from .mask import ParseError, MaskError
from .namespace import Namespace
from .postman import PostmanCollectionV1
from .resource import Resource
from .swagger import Swagger
from .utils import merge, default_id, camel_to_dash, unpack
from .reqparse import RequestParser

RE_RULES = re.compile('(<.*>)')

# List headers that should never be handled by Flask-RESTPlus
HEADERS_BLACKLIST = ('Content-Length',)


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

    :param flask.Flask|flask.Blueprint app: the Flask application object or a Blueprint
    :param str version: The API version (used in Swagger documentation)
    :param str title: The API title (used in Swagger documentation)
    :param str description: The API description (used in Swagger documentation)
    :param str terms_url: The API terms page URL (used in Swagger documentation)
    :param str contact: A contact email for the API (used in Swagger documentation)
    :param str license: The license associated to the API (used in Swagger documentation)
    :param str license_url: The license page URL (used in Swagger documentation)
    :param str endpoint: The API base endpoint (default to 'api).
    :param str default: The default namespace base name (default to 'default')
    :param str default_label: The default namespace label (used in Swagger documentation)
    :param str default_mediatype: The default media type to return
    :param bool validate: Whether or not the API should perform input payload validation.
    :param str doc: The documentation path. If set to a false value, documentation is disabled.
                (Default to '/')
    :param list decorators: Decorators to attach to every resource
    :param bool catch_all_404s: Use :meth:`handle_error`
        to handle 404 errors throughout your app
    :param url_part_order: A string that controls the order that the pieces
        of the url are concatenated when the full url is constructed.  'b'
        is the blueprint (or blueprint registration) prefix, 'a' is the api
        prefix, and 'e' is the path component the endpoint is added with
    :param dict authorizations: A Swagger Authorizations declaration as dictionary

    '''

    def __init__(self, app=None, version='1.0', title=None, description=None,
            terms_url=None, license=None, license_url=None,
            contact=None, contact_url=None, contact_email=None,
            authorizations=None, security=None, doc='/', default_id=default_id,
            default='default', default_label='Default namespace', validate=None,
            tags=None, **kwargs):
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
        self.default_id = default_id
        self._validate = validate
        self._doc = doc
        self._doc_view = None
        self._default_error_handler = None
        self.tags = tags or []

        self._error_handlers = {
            ParseError: mask_parse_error_handler,
            MaskError: mask_error_handler,
        }
        self._schema = None
        self.models = {}
        self._refresolver = None
        self.namespaces = []
        self.default_namespace = Namespace(self, default, default_label,
            endpoint='{0}-declaration'.format(default),
            path='/'
        )
        self.add_namespace(self.default_namespace)
        super(Api, self).__init__(app, **kwargs)

    def init_app(self, app, **kwargs):
        '''
        Allow to lazy register the API on a Flask application::

        >>> app = Flask(__name__)
        >>> api = Api()
        >>> api.init_app(app)

        :param flask.Flask app: the Flask application object
        :param str title: The API title (used in Swagger documentation)
        :param str description: The API description (used in Swagger documentation)
        :param str terms_url: The API terms page URL (used in Swagger documentation)
        :param str contact: A contact email for the API (used in Swagger documentation)
        :param str license: The license associated to the API (used in Swagger documentation)
        :param str license_url: The license page URL (used in Swagger documentation)

        '''
        self.title = kwargs.get('title', self.title)
        self.description = kwargs.get('description', self.description)
        self.terms_url = kwargs.get('terms_url', self.terms_url)
        self.contact = kwargs.get('contact', self.contact)
        self.contact_url = kwargs.get('contact_url', self.contact_url)
        self.contact_email = kwargs.get('contact_email', self.contact_email)
        self.license = kwargs.get('license', self.license)
        self.license_url = kwargs.get('license_url', self.license_url)
        self._add_specs = kwargs.get('add_specs', True)

        super(Api, self).init_app(app)

    def _init_app(self, app):
        self._register_specs(self.blueprint or app)
        self._register_doc(self.blueprint or app)
        super(Api, self)._init_app(app)
        self._register_apidoc(app)
        self._validate = self._validate if self._validate is not None else app.config.get('RESTPLUS_VALIDATE', False)
        app.config.setdefault('RESTPLUS_MASK_HEADER', 'X-Fields')
        app.config.setdefault('RESTPLUS_MASK_SWAGGER', True)

    def _register_apidoc(self, app):
        conf = app.extensions.setdefault('restplus', {})
        if not conf.get('apidoc_registered', False):
            app.register_blueprint(apidoc.apidoc)
        conf['apidoc_registered'] = True

    def _register_specs(self, app_or_blueprint):
        if self._add_specs:
            self._register_view(
                app_or_blueprint,
                SwaggerView,
                '/swagger.json',
                endpoint=str('specs'),
                resource_class_args=(self, )
            )

    def _register_doc(self, app_or_blueprint):
        if self._add_specs and self._doc:
            # Register documentation before root if enabled
            app_or_blueprint.add_url_rule(self._doc, 'doc', self.render_doc)
        app_or_blueprint.add_url_rule('/', 'root', self.render_root)

    def documentation(self, func):
        '''A decorator to specify a view funtion for the documentation'''
        self._doc_view = func
        return func

    def render_root(self):
        self.abort(404)

    def render_doc(self):
        '''Override this method to customize the documentation page'''
        if self._doc_view:
            return self._doc_view()
        elif not self._doc:
            self.abort(404)
        return apidoc.ui_for(self)

    def default_endpoint(self, resource, namespace=None):
        '''
        Provide a default endpoint for a resource on a given namespace.

        Endpoints are ensured not to collide.

        Override this method specify a custom algoryhtm for default endpoint.

        :param Resource resource: the resource for which we want an endpoint
        :param Namespace namespace: the namespace holdingg the resource
        :returns str: An endpoint name
        '''
        endpoint = camel_to_dash(resource.__name__)
        namespace = namespace or self.default_namespace
        if namespace is not self.default_namespace:
            endpoint = '{ns.name}_{endpoint}'.format(ns=namespace, endpoint=endpoint)
        if endpoint in namespace.resources:
            suffix = 2
            while True:
                new_endpoint = '{base}_{suffix}'.format(base=endpoint, suffix=suffix)
                if new_endpoint not in namespace.resources:
                    endpoint = new_endpoint
                    break
                suffix += 1
        return endpoint

    def add_resource(self, resource, *urls, **kwargs):
        '''
        Register a Swagger API declaration for a given API Namespace

        :param Resource resource: the resource ro register
        :param Namespace namespace: the namespace holdingg the resource
        '''
        namespace = kwargs.pop('namespace', None)
        if kwargs.pop('doc', True) and not namespace:
            return self.default_namespace.add_resource(resource, *urls, **kwargs)

        endpoint = kwargs.pop('endpoint', None)
        endpoint = str(endpoint or self.default_endpoint(resource, namespace))
        kwargs['endpoint'] = endpoint

        args = kwargs.pop('resource_class_args', [])
        if isinstance(args, tuple):
            args = list(args)
        args.insert(0, self)
        kwargs['resource_class_args'] = args

        super(Api, self).add_resource(resource, *urls, **kwargs)
        return endpoint

    def add_namespace(self, ns):
        if ns not in self.namespaces:
            self.namespaces.append(ns)

    def namespace(self, *args, **kwargs):
        '''
        A namespace factory.

        :returns Namespace: a new namespace instance
        '''
        ns = Namespace(self, *args, **kwargs)
        self.add_namespace(ns)
        return ns

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
        '''
        The Swagger specifications absolute url (ie. `swagger.json`)

        :returns str:
        '''
        return url_for(self.endpoint('specs'), _external=True)

    @property
    def base_url(self):
        '''
        The API base absolute url

        :returns str:
        '''
        return url_for(self.endpoint('root'), _external=True)

    @property
    def base_path(self):
        '''
        The API path

        :returns str:
        '''
        return url_for(self.endpoint('root'))

    @cached_property
    def __schema__(self):
        '''
        The Swagger specifications/schema for this API

        :returns dict: the schema as a serializable dict
        '''
        if not self._schema:
            self._schema = Swagger(self).as_dict()
        return self._schema

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

    def model(self, name=None, model=None, mask=None, **kwargs):
        '''
        Register a model

        Model can be either a dictionary or a fields. Raw subclass.
        '''
        model = Model(name, model, mask=mask)
        model.__apidoc__.update(kwargs)
        self.models[name] = model
        return model

    def extend(self, name, parent, fields):
        '''
        Extend a model (Duplicate all fields)
        '''
        if isinstance(parent, list):
            model = Model(None, {})
            for p in parent:
                model.update(copy.deepcopy(p))
            parent = model

        model = parent.extend(name, fields)
        self.models[name] = model
        return model

    def inherit(self, name, parent, fields):
        '''
        Inherit a modal (use the Swagger composition pattern aka. allOf)
        '''
        model = parent.inherit(name, fields)
        self.models[name] = model
        return model

    def expect(self, body, validate=None):
        '''
        A decorator to Specify the expected input model

        :param Model body: The expected model
        :param bool validate: whether to perform validation or not

        '''
        return self.doc(body=body, validate=validate or self._validate)

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
        :param int code: Optionnaly give the expected HTTP response code if its different from 200

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
                self._error_handlers[exception] = func
                return func
            return wrapper
        else:
            # Register the default error handler
            self._default_error_handler = exception
            return exception

    def handle_error(self, e):
        '''
        Error handler for the API transforms a raised exception into a Flask response,
        with the appropriate HTTP status code and body.

        :param Exception e: the raised Exception object

        '''
        got_request_exception.send(current_app._get_current_object(), exception=e)

        headers = Headers()
        if isinstance(e, HTTPException):
            code = e.code
            default_data = {
                'message': getattr(e, 'description', HTTP_STATUS_CODES.get(code, ''))
            }
            headers = e.get_response().headers
        elif e.__class__ in self._error_handlers:
            handler = self._error_handlers[e.__class__]
            result = handler(e)
            default_data, code, headers = unpack(result, 500)
        elif self._default_error_handler:
            result = self._default_error_handler(e)
            default_data, code, headers = unpack(result, 500)
        else:
            code = 500
            default_data = {
                'message': HTTP_STATUS_CODES.get(code, str(e)),
            }

        default_data['message'] = default_data.get('message', str(e))
        data = getattr(e, 'data', default_data)
        fallback_mediatype = None

        if code >= 500:
            exc_info = sys.exc_info()
            if exc_info[1] is None:
                exc_info = None
            current_app.log_exception(exc_info)

        elif code == 404 and current_app.config.get("ERROR_404_HELP", True):
            data['message'] = self._help_on_404(data.get('message', None))

        elif code == 406 and self.default_mediatype is None:
            # if we are handling NotAcceptable (406), make sure that
            # make_response uses a representation we support as the
            # default mediatype (so that make_response doesn't throw
            # another NotAcceptable error).
            supported_mediatypes = list(self.representations.keys())
            fallback_mediatype = supported_mediatypes[0] if supported_mediatypes else "text/plain"

        # Remove blacklisted headers
        for header in HEADERS_BLACKLIST:
            headers.pop(header, None)

        resp = self.make_response(data, code, headers, fallback_mediatype=fallback_mediatype)

        if code == 401:
            resp = self.unauthorized(resp)
        return resp

    def _help_on_404(self, message=None):
        rules = dict([(RE_RULES.sub('', rule.rule), rule.rule)
                      for rule in current_app.url_map.iter_rules()])
        close_matches = difflib.get_close_matches(request.path, rules.keys())
        if close_matches:
            # If we already have a message, add punctuation and continue it.
            message = ''.join((
                (message.rstrip('.') + '. ') if message else '',
                'You have requested this URI [',
                request.path,
                '] but did you mean ',
                ' or '.join((rules[match] for match in close_matches)),
                ' ?',
            ))
        return message

    def response(self, code, description, model=None, **kwargs):
        '''
        A decorator to specify one of the expected responses

        :param int code: the HTTP status code
        :param str description: a small description about the response
        :param Model model: an optionnal response model

        '''
        return self.doc(responses={code: (description, model) if model else description})

    def header(self, name, description=None, **kwargs):
        '''
        A decorator to specify one of the expected headers

        :param str name: the HTTP header name
        :param str description: a description about the header

        '''
        param = kwargs
        param['in'] = 'header'
        param['description'] = description
        return self.doc(params={name: param})

    def deprecated(self, func):
        '''A decorator to mark a resource or a method as deprecated'''
        return self.doc(deprecated=True)(func)

    def as_postman(self, urlvars=False, swagger=False):
        '''
        Serialize the API as Postman collection (v1)

        :param bool urlvars: whether to include or not placeholders for query strings
        :param bool swagger: whether to include or not the swagger.json specifications

        '''
        return PostmanCollectionV1(self, swagger=swagger).as_dict(urlvars=urlvars)

    @property
    def payload(self):
        '''Store the input payload in the current request context'''
        return request.get_json()

    @property
    def refresolver(self):
        if not self._refresolver:
            self._refresolver = RefResolver.from_schema(self.__schema__)
        return self._refresolver


class SwaggerView(Resource):
    '''Render the Swagger specifications as JSON'''
    def get(self):
        return self.api.__schema__

    def mediatypes(self):
        return ['application/json']


def mask_parse_error_handler(error):
    return {'message': 'Mask parse error: {0}'.format(error)}, 400


def mask_error_handler(error):
    return {'message': 'Mask error: {0}'.format(error)}, 400


def unshortcut_params_description(data):
    if 'params' in data:
        for name, description in six.iteritems(data['params']):
            if isinstance(description, six.string_types):
                data['params'][name] = {'description': description}
