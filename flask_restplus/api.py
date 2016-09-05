# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import difflib
import inspect
import operator
import re
import sys

from functools import wraps, partial
from types import MethodType

# from flask import url_for, request, current_app
# from flask import make_response as original_flask_make_response
# from flask.helpers import _endpoint_from_view_func
# from flask.signals import got_request_exception

from jsonschema import RefResolver, FormatChecker

# TODO: FUL-3505 and FUL-3376
from werkzeug import cached_property
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException, MethodNotAllowed, NotFound, NotAcceptable, InternalServerError
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.wrappers import Response as ResponseBase

from ._compat import OrderedDict
# from .mask import ParseError, MaskError
from .namespace import Namespace
# from .postman import PostmanCollectionV1
from .swagger import Swagger
from .utils import default_id, camel_to_dash # deleted unpack

# ### TODO: Would need to be readapted to RE_RULES = re.compile('({.*})')
# RE_RULES = re.compile('(<.*>)')

# List headers that should never be handled by Flask-RESTPlus
HEADERS_BLACKLIST = ('Content-Length',)


# Replaced output_json by None (cf. wsgiservice.Resource content negotiation)
# TODO: FUL-3376
DEFAULT_REPRESENTATIONS = [('application/json', None)]

### wsgiservice-specific imoprts
import wsgiservice




class Api(object):
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

    :param str version: The API version (used in Swagger documentation)
    :param str title: The API title (used in Swagger documentation)
    :param str description: The API description (used in Swagger documentation)
    :param str terms_url: The API terms page URL (used in Swagger documentation)
    :param str contact: A contact email for the API (used in Swagger documentation)
    :param str license: The license associated to the API (used in Swagger documentation)
    :param str license_url: The license page URL (used in Swagger documentation)
    :param func default_id: The default Swagger Operation.operationId string generation function
        accepting a resource class and HTTP method string
    :param str endpoint: The API base endpoint (default to 'api).
    :param str default: The default namespace base name (default to 'default')
    :param str default_label: The default namespace label (used in Swagger documentation)
    :param str default_mediatype: The default media type to return
    :param bool validate: API-wide request validation setting (can be overridden by concrete methods).
    :param str doc: The documentation path. If set to a false value, documentation is disabled.
                (Default to '/')
    :param list decorators: Decorators to attach to every resource
    :param bool catch_all_404s: Use :meth:`handle_error`
        to handle 404 errors throughout your app
    :param dict authorizations: A Swagger Authorizations declaration as dictionary
    :param bool serve_challenge_on_401: Serve basic authentication challenge with 401
        responses (default 'False')
    :param FormatChecker format_checker: A jsonschema.FormatChecker object that is hooked into
    the Model validator. A default or a custom FormatChecker can be provided (e.g., with custom
    checkers), otherwise the default action is to not enforce any format validation.
    '''

    def __init__(self,
            version='1.0', title=None, description=None,
            terms_url=None, license=None, license_url=None,
            contact=None, contact_url=None, contact_email=None,
            authorizations=None, security=None, swagger_path='/swagger.json', default_id=default_id, #default='default', default_label='Default namespace',
            validate=None,
            tags=None, prefix='',
            decorators=None, # catch_all_404s=False, serve_challenge_on_401=False, # TODO FUL-3505
            format_checker=None,
            **kwargs): # TODO: FUL-3376 Delete kwargs
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
        self._validate = validate          # Api-wide request validation setting
        self._swagger_path = swagger_path

        self._default_error_handler = None # TODO: FUL-3505
        self.tags = tags or []

        # TODO: FUL-3505
        # self.error_handlers = {
        #     ParseError: mask_parse_error_handler,
        #     MaskError: mask_error_handler,
        # }

        self._schema = None # cache for Swagger JSON specification
        self.models = {}
        self._refresolver = None
        self.format_checker = format_checker
        self.namespaces = []

        # # TODO: FUL-3376 (probably deletable)
        # # delete default namespace as it's just syntactic ease not to define an extra namespace
        # if default is not None and default_label is not None:
        #     self.default_namespace = self.namespace(default, default_label,
        #         endpoint='{0}-declaration'.format(default),
        #         validate=validate,
        #         api=self,
        #     )

        self.representations = OrderedDict(DEFAULT_REPRESENTATIONS)

        self.prefix = prefix

        self.decorators = decorators if decorators else []

        # TODO: FUL-3505
        # self.catch_all_404s = catch_all_404s
        # self.serve_challenge_on_401 = serve_challenge_on_401

        # TODO: FUL-3376 (probably deletable)
        self.resources = []


    # NOTE: init_app and _init_app methods deleted here
    # These methods mainly served to allow distributed initialization

    # TODO: NOW
    def create_wsgiservice_app(self):
        '''
        Creates a :class:`wsgiservice.application.Application` instance from the resources owned by self (the namespaces of this Api instance)
        '''
        # TODO: Make the Swagger specification resources configurable, such as with a
        #       endpoint path -> (predicate, extra_info) dict that supplies a boolean
        #       predicate callback that decides whether to include endpoint in documentation
        #       and a

        SwaggerResourceClass = generate_swagger_resource(api=self, swagger_path=self._swagger_path)

        self.resources.append((SwaggerResourceClass, self._swagger_path, {}))

        # Check for resource._path == url (Api.prefix ignored)
        # Note that we do not use the base_path here as it's assumed to be merged in elsewhere
        for resource, url, _ in self.resources:
            if getattr(resource,'_path',None) is not None:
                if resource._path != url:
                    raise Exception # raise a path error exception due to inconsistent mount point

        return wsgiservice.get_app(
            {resource.__name__ : resource for resource, _, _ in self.resources})


    # # TODO: FUL-3376 (probably deletable)
    # def __getattr__(self, name):
    #     try:
    #         return getattr(self.default_namespace, name)
    #     except AttributeError:
    #         raise AttributeError('Api does not have {0} attribute'.format(name))


    # TODO: FUL-3376 (probably deletable to do copy elision)
    ## Add resource, assigned urls and constructor named/kw-args to sequence of resources
    def register_resource(self, namespace, resource, url, **kwargs):

        kwargs['endpoint'] = default_endpoint(resource, namespace)

        self.resources.append((resource, url, kwargs))


    # NOTE: _register_view method deleted here
    # Constructed flask view function(s) from resource class (including binding of resource constructor to
    # named/kw-arguments), application of all Api-level decorators to the resulting view function and return
    # value transformation based on requested content type registering the view with the flask.Application
    # instance.

    # NOTE: default_endpoint method moved outside this instance (as not dependent on internal attributes)

    # Add namespace to list in this Api instance and this Api instance to list of Api objects
    # in namespace
    # # TODO: FUL-3505
    def add_namespace(self, ns):
        if ns not in self.namespaces:
            self.namespaces.append(ns)
            if self not in ns.apis:
                ns.apis.append(self)

        # Copy all resources
        # TODO: FUL-3376 copy elision?
        for resource, url, kwargs in ns.resources:
            self.register_resource(ns, resource, url, **kwargs)

        # Copy all models
        # TODO: FUL-3376 copy elision?
        for name, definition in ns.models.items():
            self.models[name] = definition

        # TODO: FUL-3505
        # # Register error handlers
        # for exception, handler in ns.error_handlers.items():
        #     self.error_handlers[exception] = handler


    # TODO: FUL-3376 Remove this at later stage (Api should become a namespace collection)
    def get_resources(self):
        '''Get resources held by this instance'''
        resources = {}
        for ns in self.namespaces:
            for resource, _, _ in ns.resources:
                resources[resource.__name__] = resource
        return resources


    # TODO: FUL-3376: replace prefix by a more reasonable name such as _base_path ###
    @property
    def base_path(self):
        '''
        The base path of the API

        :rtype: str
        '''
        return self.prefix

    # Swagger schema as a dictionary
    # TODO: FUL-3376 make it accessible as a @property
    def __schema__(self):
        '''
        The Swagger specifications/schema for this API

        :returns dict: the schema as a serializable dict
        '''
        if not self._schema:
            self._schema = Swagger(self).as_dict()
        return self._schema

    # ### error handler registration ###
    # # TODO: FUL-3505
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
    #         self._default_error_handler = exception
    #         return exception
    #
    # # TODO: FUL-3505
    # def owns_endpoint(self, endpoint):
    #     '''
    #     Tests if an endpoint name (not path) belongs to this Api.
    #     Takes into account the Blueprint name part of the endpoint name.
    #
    #     :param str endpoint: The name of the endpoint being checked
    #     :return: bool
    #     '''
    #
    #     if self.blueprint:
    #         if endpoint.startswith(self.blueprint.name):
    #             endpoint = endpoint.split(self.blueprint.name + '.', 1)[-1]
    #         else:
    #             return False
    #     return endpoint in self.endpoints
    #
    # # TODO: FUL-3505
    # def _should_use_fr_error_handler(self):
    #     '''
    #     Determine if error should be handled with FR or default Flask
    #
    #     The goal is to return Flask error handlers for non-FR-related routes,
    #     and FR errors (with the correct media type) for FR endpoints. This
    #     method currently handles 404 and 405 errors.
    #
    #     :return: bool
    #     '''
    #     adapter = current_app.create_url_adapter(request)
    #
    #     try:
    #         adapter.match()
    #     except MethodNotAllowed as e:
    #         # Check if the other HTTP methods at this url would hit the Api
    #         valid_route_method = e.valid_methods[0]
    #         rule, _ = adapter.match(method=valid_route_method, return_rule=True)
    #         return self.owns_endpoint(rule.endpoint)
    #     except NotFound:
    #         return self.catch_all_404s
    #     except:
    #         # Werkzeug throws other kinds of exceptions, such as Redirect
    #         pass
    #
    # # TODO: FUL-3505
    # def _has_fr_route(self):
    #     '''Encapsulating the rules for whether the request was to a Flask endpoint'''
    #     # 404's, 405's, which might not have a url_rule
    #     if self._should_use_fr_error_handler():
    #         return True
    #     # for all other errors, just check if FR dispatched the route
    #     if not request.url_rule:
    #         return False
    #     return self.owns_endpoint(request.url_rule.endpoint)
    #
    # # TODO: FUL-3505
    # def error_router(self, original_handler, e):
    #     '''
    #     This function decides whether the error occured in a flask-restplus
    #     endpoint or not. If it happened in a flask-restplus endpoint, our
    #     handler will be dispatched. If it happened in an unrelated view, the
    #     app's original error handler will be dispatched.
    #     In the event that the error occurred in a flask-restplus endpoint but
    #     the local handler can't resolve the situation, the router will fall
    #     back onto the original_handler as last resort.
    #
    #     :param function original_handler: the original Flask error handler for the app
    #     :param Exception e: the exception raised while handling the request
    #     '''
    #     if self._has_fr_route():
    #         try:
    #             return self.handle_error(e)
    #         except Exception:
    #             pass  # Fall through to original handler
    #     return original_handler(e)
    #
    # # TODO: FUL-3505
    # def handle_error(self, e):
    #     '''
    #     Error handler for the API transforms a raised exception into a Flask response,
    #     with the appropriate HTTP status code and body.
    #
    #     :param Exception e: the raised Exception object
    #
    #     '''
    #     got_request_exception.send(current_app._get_current_object(), exception=e)
    #
    #     headers = Headers()
    #     if e.__class__ in self.error_handlers:
    #         handler = self.error_handlers[e.__class__]
    #         result = handler(e)
    #         default_data, code, headers = unpack(result, 500)
    #     elif isinstance(e, HTTPException):
    #         code = e.code
    #         default_data = {
    #             'message': getattr(e, 'description', HTTP_STATUS_CODES.get(code, ''))
    #         }
    #         headers = e.get_response().headers
    #     elif self._default_error_handler:
    #         result = self._default_error_handler(e)
    #         default_data, code, headers = unpack(result, 500)
    #     else:
    #         code = 500
    #         default_data = {
    #             'message': HTTP_STATUS_CODES.get(code, str(e)),
    #         }
    #
    #     default_data['message'] = default_data.get('message', str(e))
    #     data = getattr(e, 'data', default_data)
    #     fallback_mediatype = None
    #
    #     if code >= 500:
    #         exc_info = sys.exc_info()
    #         if exc_info[1] is None:
    #             exc_info = None
    #         current_app.log_exception(exc_info)
    #
    #     elif code == 404 and current_app.config.get("ERROR_404_HELP", True):
    #         data['message'] = self._help_on_404(data.get('message', None))
    #
    #     elif code == 406 and self.default_mediatype is None:
    #         # if we are handling NotAcceptable (406), make sure that
    #         # make_response uses a representation we support as the
    #         # default mediatype (so that make_response doesn't throw
    #         # another NotAcceptable error).
    #         supported_mediatypes = list(self.representations.keys())
    #         fallback_mediatype = supported_mediatypes[0] if supported_mediatypes else "text/plain"
    #
    #     # Remove blacklisted headers
    #     for header in HEADERS_BLACKLIST:
    #         headers.pop(header, None)
    #
    #     resp = self.make_response(data, code, headers, fallback_mediatype=fallback_mediatype)
    #
    #     if code == 401:
    #         resp = self.unauthorized(resp)
    #     return resp
    #
    # # TODO: FUL-3505
    # def _help_on_404(self, message=None):
    #     rules = dict([(RE_RULES.sub('', rule.rule), rule.rule)
    #                   for rule in current_app.url_map.iter_rules()])
    #     close_matches = difflib.get_close_matches(request.path, rules.keys())
    #     if close_matches:
    #         # If we already have a message, add punctuation and continue it.
    #         message = ''.join((
    #             (message.rstrip('.') + '. ') if message else '',
    #             'You have requested this URI [',
    #             request.path,
    #             '] but did you mean ',
    #             ' or '.join((rules[match] for match in close_matches)),
    #             ' ?',
    #         ))
    #     return message

    # #TODO: FUL-3376 (decide whether this should be added as a feature)
    ### Postman API specification ###
    # def as_postman(self, urlvars=False, swagger=False):
    #     '''
    #     Serialize the API as Postman collection (v1)
    #
    #     :param bool urlvars: whether to include or not placeholders for query strings
    #     :param bool swagger: whether to include or not the swagger.json specifications
    #
    #     '''
    #     return PostmanCollectionV1(self, swagger=swagger).as_dict(urlvars=urlvars)

    @property
    def refresolver(self):
        '''
        JSON schema model system reference resolver
        '''
        if not self._refresolver:
            self._refresolver = RefResolver.from_schema(self.__schema__)
        return self._refresolver

    # NOTE: deleted representation here
    # Was used to define response transformations to custom custom media types such as JSON/XML/etc.

    # TODO: FUL-3375
    # ### security: unauthorized request ###
    # def unauthorized(self, response):
    #     '''Given a response, change it to ask for credentials'''
    #
    #     if self.serve_challenge_on_401:
    #         realm = current_app.config.get("HTTP_BASIC_AUTH_REALM", "flask-restplus")
    #         challenge = u"{0} realm=\"{1}\"".format("Basic", realm)
    #
    #         response.headers['WWW-Authenticate'] = challenge
    #     return response

    # TODO: FUL-3376
    ###  Retrieve URL path for a particular resource ###
    # To work with absolute URLs would need host name
    def url_for(self, resource, **values):
        '''
        Generates a URL to the given resource.
        '''

        for resource_class, url, _ in iter(self.resources):
            if resource == resource_class:
                return self.base_path + url.lstrip('/')
        else:
            return None


# # TODO: FUL-3505
# def mask_parse_error_handler(error):
#     '''When a mask can't be parsed'''
#     return {'message': 'Mask parse error: {0}'.format(error)}, 400
#
#
# def mask_error_handler(error):
#     '''When any error occurs on mask'''
#     return {'message': 'Mask error: {0}'.format(error)}, 400


### Swagger Documentation resource factory
def generate_swagger_resource(api, swagger_path):
    '''
    Returns a wsgiservice Swagger documentation Resource class that binds the Api instance
    '''

    # @namespace.route(swagger_path)
    class SwaggerResource(wsgiservice.Resource):
        '''
        Resource for the Swagger specification of the bound Api
        '''
        _path = swagger_path

        def GET(self):
            return api.__schema__()

    return SwaggerResource


def default_endpoint(resource, namespace):
    '''
    Provide a default endpoint name for a resource on a given namespace.

    :param Resource resource: the resource modeling the endpoint
    :param Namespace namespace: the namespace holding the resource
    :returns str: An endpoint name
    '''
    endpoint = camel_to_dash(resource.__name__)
    return '{ns.name}_{endpoint}'.format(ns=namespace, endpoint=endpoint)
