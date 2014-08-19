Documenting your API with Swagger
=================================

A Swagger API documentation is automatically generated and available on your API root
but you need to provide some details with the ``Api.doc()`` decorator.


Documenting with the ``Api.doc()`` decorator
--------------------------------------------

This decorator allows you specify some details about your API.
They will be used in the Swagger API declarations.

You can document a class or a method.


.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        def get(self, id):
            return {}

        @api.doc(responses={403: 'Not Authorized'})
        def post(self, id):
            api.abort(403)


Documenting with the ``Api.marshal_with()`` decorator
-----------------------------------------------------

This decorator works like the Flask-Restful ``marshal_with`` decorator
with the difference that it documents the methods.
The optionnal parameter ``as_list`` allows you to specify wether or not the objects are returned as a list.

.. code-block:: python

    resource_fields = {
        'name': fields.String,
    }

    @api.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        @api.marshal_with(resource_fields, as_list=True)
        def get(self):
            return get_objects()

        @api.marshal_with(resource_fields)
        def post(self):
            return create_object()


The ``Api.marshal_list_with()`` decorator is strictly equivalent to ``Api.marshal_with(fields, as_list=True)``.

.. code-block:: python

    resource_fields = {
        'name': fields.String,
    }

    @api.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        @api.marshal_list_with(resource_fields)
        def get(self):
            return get_objects()

        @api.marshal_with(resource_fields)
        def post(self):
            return create_object()



Documenting with the ``Api.route()`` decorator
----------------------------------------------

You can provide class-wide documentation by using the ``Api.route()``'s' ``doc`` parameter.
It accept the same attribute/syntax than the ``Api.doc()`` decorator.

By example, these two declaration are equivalents:


.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        def get(self, id):
            return {}


.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource', doc={params:{'id': 'An ID'}})
    class MyResource(Resource):
        def get(self, id):
            return {}


Documenting with the ``Api.model()`` decorator
----------------------------------------------

The ``Api.model`` decorator allows you to declare the models that your API can serialize.

You can use it either on a fields dictionnary or a ``field.Raw`` subclass:

.. code-block:: python

    my_fields = api.model('MyModel', {
        'name': fields.String
    })

    @api.model('MyField')
    class MySpecialField(fields.Raw):
        pass


Cascading
---------

Documentation handling is done in cascade.
Method documentation override class-wide documentation.
Inherited documentation override parent one.

By example, these two declaration are equivalents:


.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        def get(self, id):
            return {}


.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'Class-wide description'})
    class MyResource(Resource):
        @api.doc(params={'id': 'An ID'})
        def get(self, id):
            return {}

You can also provide method specific documentation from a class decoration.
The following example will produce the same documentation than the two previous examples:

.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'Class-wide description'})
    @api.doc(get={'params': {'id': 'An ID'}})
    class MyResource(Resource):
        def get(self, id):
            return {}


Overriding the API root view
----------------------------

TODO
