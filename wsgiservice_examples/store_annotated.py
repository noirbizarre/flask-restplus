"""The store service is a simple document store. It stores key/value pairs on
the documents. This is currently a dummy implementation with ony in-memory
storage.
"""

import uuid
from wsgiservice import *
import logging
import sys


from flask_restplus import namespace, api, fields

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

data = {}


# Namespace instantiation (sets path prefix and documentation tag/description for all owned (mounted) resources)
ns = namespace.Namespace(
    name='store_interface_ns', description='An associative (key,document) store',
    path='/', decorators=None, validate=None)


# # TODO: define model
id_model = ns.model('id', { 'id': fields.String(pattern=r'[-0-9a-zA-Z]{36}',
                                                description='UUID of key-document pair',
                                                example='3c805c7c-9ff0-4879-8eb7-d2eee97ca39d') } )

## model inheritance, alternatively use ns.clone to copy all fields
doc_model = ns.inherit('doc_model',
                        {'doc': fields.String(description='The document',example='Some document goes here...')})


# saved_model = ns.model('saved_model',{'saved': fields.Boolean(description='Storage status')})
id_saved_model = ns.clone('id_saved_model', id_model, {'saved': fields.Boolean(description='Storage status',example='True')})

# # TODO: Error annotations (e.g. marshal_with, others)


# PUT request handler
def put_document(id,doc_resource_request_post):
    """Overwrite or create the document indicated by the ID. Parameters
    are passed as key/value pairs in the POST data."""
    data.setdefault(id, {'id': id})
    for key in doc_resource_request_post:
        data[id][key] = doc_resource_request_post[key]
    return {'id': id, 'saved': True}


#@mount('/{id}')    # Api.create_wsgiservice_app adds _path attribute to Resources of owned Namespaces
@ns.route('/{id}')  # TODO: Check path paramater documentation generated from Namespace.route/Api.route
@ns.param(name='id', description='User ID, must be a valid UUID.')  # parameter documentation
@validate('id', re=r'[-0-9a-zA-Z]{36}', doc='User ID, must be a valid UUID.')  # TODO: replace by request parser or model
class Document(Resource):
    """Represents an individual document in the document store. The storage
    is only persistent in-memory, so it will go away when the service is
    restarted.
    """
    NOT_FOUND = (KeyError,)

    # parameter model
    # @expect(id) # TODO: models
    # @ns.security('basic_auth','api_key')
    @ns.response(code=200,description='Returned requested document',model=None)
    def GET(self, id):
        "Return the document indicated by the ID."
        return data[id]

    # parameter model
    # @expect(doc_model)
    # TODO: extract into separate function in order not to perform request validation twice
    @ns.param(name='doc', description='Document replacing old document.', _in='formData')
    @ns.marshal_with(id_saved_model,code=200, description='Document updated')
    @ns.security('basic_auth')
    def PUT(self, id):
        """Overwrite or create the document indicated by the ID. Parameters
        are passed as key/value pairs in the POST data."""
        return put_document(id,self.request.POST)

    def DELETE(self, id):
        "Delete the document indicated by the ID."
        del data[id]


# URL endpoint
#@mount('/')
@ns.route('/')
class Documents(Resource):

    # @ns.expect(doc_model)

    @ns.deprecated
    @ns.param(name='doc',description='Document to post.',_in='formData') # could be replaced by @ns.expect(...) if body would be parsed correctly
    @ns.response(code=201, description='Document posted', model=id_saved_model)  # -> @ns.marshal(code=201,description='id',id_model)
    def POST(self):
        """Create a new document, assigning a unique ID. Parameters are
                passed in as key/value pairs in the POST data."""
        id = str(uuid.uuid4())
        self.response.body_raw = put_document(id,self.request.POST)
        raise_201(self, id)



# API security definitions
# dictionary of name -  Swagger Security Scheme object
security_defintions = { 'api_token'    : { 'type'        : 'apiKey',
                                           'name'        : 'Authorization',
                                           'in'          : 'header',
                                           'description' : 'API token authenatication: ' \
                                           'Enter the token you received from http://... ' \
                                           'in this format: \"Token xwdt...\"'
                                           },
                        'basic_auth': {'type': 'basic'} }



# API wide applied security settings (list of security schemes to authorize with the API
# (logical OR between list elements))
# Assembled to a Swagger Security Requirement object by documentation generator
api_wide_security = ('api_token',
                     'basic_auth' )



# Note only that for Beekeeper's application the URL prefix for mounting the wsgiservice.Application instance to the
# URLMap must be retrieved from the Api instance with Api.base_path() in order to enforce consistency between application
# and documentation
api = api.Api(version='1', title=None, description=None,
              terms_url=None, license=None, license_url=None,
              contact=None, contact_url=None, contact_email=None,
              authorizations=security_defintions, security=api_wide_security, doc='/', # default_id=default_id, # this is flask-restplus.utils.default_id
              validate=None,
              tags=None, prefix='/',  # NOTE the special prefix as the base_path
              default_mediatype='application/json', decorators=None,
              catch_all_404s=False, serve_challenge_on_401=False, format_checker=None)

api.add_namespace(ns)

# wsgiservice.Application factory using the resources owned by the Api instance
app = api.create_wsgiservice_app()

# app = get_app(globals())

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8001"
    make_server('', 8001, app).serve_forever()
