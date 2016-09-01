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



### Api instance ###
api = wsgiservice_restplus.api.Api(
    version='1.0', title='Document store REST API',
    description='This API provides access to a simple in-memory document store',
    terms_url=None, license=None, license_url=None,
    contact='author', contact_url='beekeeper.io', contact_email='maintainer@beekeeper.io',
    doc='/',
    prefix='/api_base_path/',
    default_mediatype='application/json')


### Namespace instance ###
ns = wsgiservice_restplus.namespace.Namespace(
    name='document_collection_ns',
    description='An associative (key,document) store',
    path='/ns_sub_path/')



### JSON Schema model definitions ###
doc_model      = ns.model('doc_model',
                          {'doc': wsgiservice_restplus.fields.String(
                                                description='The document',
                                                example='Some document goes here...')})

id_model       = ns.model('id_model',
                          { 'id': wsgiservice_restplus.fields.String(
                                                pattern=r'[-0-9a-zA-Z]{36}',
                                                description='UUID of the document',
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




@ns.param(name='id', description='User ID, must be a valid UUID.')
@ns.route('/{id}')
class Document(Resource):
    """
    Represents an individual document in the document store.
    """

    NOT_FOUND = (KeyError,)

    @ns.response(code=200,description='Returned requested document',model=id_doc_model)
    @ns.response(code=404, description='Not found', model=error_model)
    def GET(self, id):
        "Return the document indicated by the ID."
        return data[id]

    @ns.response(code=200,description='Deleted specified document')
    def DELETE(self, id):
        "Delete the document indicated by the ID."
        del data[id]


@ns.route('/')
class Documents(Resource):
    """
    Represents the document collection held in the document store.
    """

    @ns.param(name='doc',description='Document to post.',_in='formData') # @ns.expect(doc_model)
    @ns.response(code=201, description='Document posted', model=id_saved_model)
    def POST(self):
        """
        Create a new document, assigning a unique ID.

        Parameters are passed in as key/value pairs in the POST data.
        """
        id = str(uuid.uuid4())
        self.response.body_raw = update_document(id,self.request.POST)
        raise_201(self, id)



### Add namespace to Api
api.add_namespace(ns)


### Create a wsgiservice application from resources owned by the Api instance
app = api.create_wsgiservice_app() # instead of app = get_app(globals())


### Start WSGI server
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print "Running on port 8001"
    make_server('', 8001, app).serve_forever()