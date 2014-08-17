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

The namespace object provide the same feature:

.. code-block:: python

    ns = api.namespcae('ns', 'Some namespace')

    @ns.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        def get(self, id):
            return {}


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
