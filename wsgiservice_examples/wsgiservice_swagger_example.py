"""
The store service is a simple document store. It stores key/value pairs on
the documents. This is currently a dummy implementation with ony in-memory
storage.
"""

import uuid
from wsgiservice import *
import logging
import sys


import flask_restplus as wsgiservice_restplus

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)


#TODO: Show more diverse fields (such as email and so on) and make the security work
# TODO: required/not required...

# Namespace instantiation (sets path prefix and documentation tag/description for all owned (mounted) resources)
ns = wsgiservice_restplus.namespace.Namespace(
    name='store_interface',
    description='An associative (key,document) store',
    path='/ns_path/')



# JSON Schema model definitions
doc_model      = ns.model('doc_model',
                          {'doc': wsgiservice_restplus.fields.String(
                                                description='The document',
                                                example='Some document goes here...')})

id_model       = ns.model('id_model',
                          { 'id': wsgiservice_restplus.fields.String(
                                                pattern=r'[-0-9a-zA-Z]{36}',
                                                description='UUID of key-document pair',
                                                example='3c805c7c-9ff0-4879-8eb7-d2eee97ca39d') } )

id_doc_model    = ns.clone('id_doc_model',id_model,doc_model)

# model inheritance
id_saved_model = ns.inherit('id_saved_model',
                            id_model,
                            {'saved': wsgiservice_restplus.fields.Boolean(
                                                description='Storage status',
                                                example='True')})

error_model    = ns.model('error',
                          { 'error': wsgiservice_restplus.fields.String(
                                                description='Description of the error',
                                                example='The error was ...') } )


# The non-persistent document data store
data = {}


def update_document(id,doc_resource_request_post):
    """
    Overwrite or create the document indicated by the ID.

    Parameters are passed as key/value pairs in the POST data.
    """
    data.setdefault(id, {'id': id})
    for key in doc_resource_request_post:
        data[id][key] = doc_resource_request_post[key]
    return {'id': id, 'saved': True}


# @validate('id', re=r'[-0-9a-zA-Z]{36}', doc='User ID, must be a valid UUID.')  # TODO: replace by request parser or model

@ns.route('/{id}')
@ns.param(name='id', description='User ID, must be a valid UUID.')#, model=wsgiservice_restplus.fields.String(
                                                 # pattern=r'[-0-9a-zA-Z]{36}',
                                                 # description='UUID of key-document pair',
                                                 # example='3c805c7c-9ff0-4879-8eb7-d2eee97ca39d') )  # path parameter documentation
class Document(Resource):
    """
    Represents an individual document in the document store.

    The storage is only persistent in-memory, so it will go away when the service is
    restarted.
    """
    NOT_FOUND = (KeyError,)

    @ns.response(code=200,description='Returned requested document',model=id_doc_model)
    @ns.response(code=404, description='Not found', model=error_model)
    def GET(self, id):
        "Return the document indicated by the ID."
        return data[id]

    # TODO: Remove
    # # parameter model
    # # @expect(doc_model)
    # # TODO: extract into separate function in order not to perform request validation twice
    # @ns.param(name='doc', description='Document replacing old document.', _in='formData')
    # @ns.marshal_with(id_saved_model,code=200, description='Document updated')
    # def PUT(self, id):
    #     """Overwrite or create the document indicated by the ID. Parameters
    #     are passed as key/value pairs in the POST data."""
    #     return update_document(id,self.request.POST)

    @ns.response(code=200,description='Deleted specified document')
    def DELETE(self, id):
        "Delete the document indicated by the ID."
        del data[id]


# security
def token_authentication(request):
    if request.header.get('Authorization',None) and request.header['Authorization'][:5].lower() == 'token':
        return request.header['Authorization'][5:].strip(' ') == 'secret_1234'
    else:
        return False

@ns.route('/')
class Documents(Resource):

    # @ns.security('api_token')
    # @ns.expect(doc_model) # Swagger-UI will send request in body with this decorator
    @ns.param(name='doc',description='Document to post.',_in='formData') # could be replaced by @ns.expect(...) if body would be parsed correctly
    @ns.response(code=201, description='Document posted', model=id_saved_model)  # -> @ns.marshal(code=201,description='id',id_model)
    # @ns.response(code=401, description='Authentication error', model=error_model)
    def POST(self):
        """
        Create a new document, assigning a unique ID. Parameters are
        passed in as key/value pairs in the POST data.
        """
        # if not token_authentication(self.request):
        #     msg = 'Please authenticate'
        #     raise_401(self,msg,msg)
        id = str(uuid.uuid4())
        # TODO: Parse body parameter of self.request
        self.response.body_raw = update_document(id,self.request.POST)
        raise_201(self, id)



### Api instance construction ###

api = wsgiservice_restplus.api.Api(
    version='1.0', title='Document store REST API', description='This API provides access to a simple in-memory document store',
    terms_url=None, license=None, license_url=None,
    contact='Maintainer name', contact_url='beekeeper.io', contact_email='maintainer@beekeeper.io',
    authorizations=None, security=None, doc='/', # default_id=default_id, # this is flask-restplus.utils.default_id
    default='default', default_label='Default namespace', validate=None,
    tags=None, prefix='/documents/',
    default_mediatype='application/json')

api.add_namespace(ns)

# Application factory using the resources owned by the Api instance
app = api.create_wsgiservice_app() # instead of app = get_app(globals())

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8001"
    make_server('', 8001, app).serve_forever()