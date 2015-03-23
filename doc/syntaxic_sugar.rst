Syntaxic sugar
==============

One of the purpose of Flask-Restplus is to provide some syntaxic sugar of Flask-Restful.


Route with decorator
--------------------

The Api class has a ``route()`` decorator used to route API's endpoint.

When with Flask-Restful you were writting :

.. code-block:: python

    class MyResource(Resource):
        def get(self, id):
            return {}

    api.add_resource('/my-resource/<id>', MyResource.as_view('my-resource'))

With Flask-Restplus, you can write:

.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        def get(self, id):
            return {}

You can optionnaly provide class-wide documentation:

.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource', doc={params:{'id': 'An ID'}})
    class MyResource(Resource):
        def get(self, id):
            return {}

But it will be easier to read with two decorators for the same effect:

.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        def get(self, id):
            return {}

The namespace object provide the same feature:

.. code-block:: python

    ns = api.namespace('ns', 'Some namespace')

    # Will ba available to /api/ns/my-resource/<id>
    @ns.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        def get(self, id):
            return {}

All routes within a namespace are prefixed with the namespace name.


``abort`` shortcut
------------------

You can use the ``Api.abort()`` method to abort a request.
This shortcut always serialize the response in the right format.

.. code-block:: python

    @api.route('/failure')
    class MyResource(Resource):
        def get(self):
            api.abort(403)

        def post(self):
            api.abort(500, 'Some custom message')

``parser`` shortcut
-------------------

You can use the ``Api.parser()`` shortcut to obtain a RequestParser instance.

.. code-block:: python

    parser = api.parser()
    parser.add_argument('param', type=str, help='Some parameter')


``marshal`` shortcut
--------------------

You can use the ``Api.marshal()`` shortcut to serialize your objects.

.. code-block:: python

    return api.marshal(todos, fields), 201


Handle errors with ``@api.errorhandler()`` decorator
----------------------------------------------------

The ``@api.errorhandler()`` decorator allows you to register
a specific handler for a given exception, in the same maner
than you can do with Flask/Blueprint ``@errorhandler`` decorator.

.. code-block:: python

    @api.errorhandler(CustomException)
    def handle_custom_exception(error):
        '''Return a custom message and 400 status code'''
        return {'message': 'What you want'}, 400


    @api.errorhandler(AnotherException)
    def handle_another_exception(error):
        '''Return a custom message and 500 status code'''
        return {'message': error.specific}
