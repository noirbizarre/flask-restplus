Documenting your API with Swagger
=================================

A Swagger API documentation is automatically generated and available on your API root
but you need to provide some details with the ``@api.doc()`` decorator.


Documenting with the ``@api.doc()`` decorator
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


Documenting with the ``@api.model()`` and ``@api.extend`` decorators
--------------------------------------------------------------------

The ``@api.model`` decorator allows you to declare the models that your API can serialize.

You can use it either on a fields dictionnary or a ``field.Raw`` subclass:

.. code-block:: python

    my_fields = api.model('MyModel', {
        'name': fields.String
    })

    @api.model('MyField')
    class MySpecialField(fields.Raw):
        pass

    @api.model(type='integer', format='int64')
    class MyIntField(fields.Raw):
        pass

    @api.model(fields={'name': fields.String, 'age': fields.Integer})
    class Person(fields.Raw):
        def format(self, value):
            return {'name': value.name, 'age': value.age}

The ``api.extend`` method allows you to register an augmented model.
It saves you duplicating all fields.

.. code-block:: python

    parent = api.model('Parent', {
        'name': fields.String
    })

    child = api.extend('Child', parent, {
        'age': fields.Integer
    })


Documenting with the ``@api.marshal_with()`` decorator
-----------------------------------------------------

This decorator works like the Flask-Restful ``marshal_with`` decorator
with the difference that it documents the methods.
The optionnal parameter ``as_list`` allows you to specify wether or not the objects are returned as a list.

.. code-block:: python

    resource_fields = api.model('Resource', {
        'name': fields.String,
    })

    @api.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        @api.marshal_with(resource_fields, as_list=True)
        def get(self):
            return get_objects()

        @api.marshal_with(resource_fields)
        def post(self):
            return create_object()


The ``@pi.marshal_list_with()`` decorator is strictly equivalent to ``Api.marshal_with(fields, as_list=True)``.

.. code-block:: python

    resource_fields = api.model('Resource', {
        'name': fields.String,
    })

    @api.route('/my-resource/<id>', endpoint='my-resource')
    class MyResource(Resource):
        @api.marshal_list_with(resource_fields)
        def get(self):
            return get_objects()

        @api.marshal_with(resource_fields)
        def post(self):
            return create_object()


Documenting with the ``@api.expect()`` decorator
------------------------------------------------

The ``@api.expect()`` decorator allows you to specify the expected input fields
and is a shortcut for ``@api.doc(body=<fields>)``.

The following synatxes are equivalents:

.. code-block:: python

    resource_fields = api.model('Resource', {
        'name': fields.String,
    })

    @api.route('/my-resource/<id>')
    class MyResource(Resource):
        @api.expect(resource_fields)
        def get(self):
            pass

.. code-block:: python

    resource_fields = api.model('Resource', {
        'name': fields.String,
    })

    @api.route('/my-resource/<id>')
    class MyResource(Resource):
        @api.doc(body=resource_fields)
        def get(self):
            pass

It allows you specify lists as expected input too:


.. code-block:: python

    resource_fields = api.model('Resource', {
        'name': fields.String,
    })

    @api.route('/my-resource/<id>')
    class MyResource(Resource):
        @api.expect([resource_fields])
        def get(self):
            pass


Documenting with the ``@api.route()`` decorator
-----------------------------------------------

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


Documenting the fields
----------------------

Every Flask-Restplus fields accepts additional but optional arguments used to document the field:

- ``required``: a boolean indicating if the field is always set (*default*: ``False``)
- ``description``: some details about the field (*default*: ``None``)

There is also field specific attributes.

The ``String`` field accept an optional ``enum`` argument to restrict the authorized values.

The ``Integer``, ``Float`` and ``Arbitrary`` fields accept
both ``min`` and ``max`` arguments to restrict the possible values.

.. code-block:: python

    my_fields = api.model('MyModel', {
        'name': fields.String(description='The name', required=True),
        'type': fields.String(description='The object type', enum=['A', 'B']),
        'age': fields.Integer(min=0),
    })


Documenting the methods
-----------------------

Each resource will be documented as a Swagger path.

Each resource method (``get``, ``post``, ``put``, ``delete``, ``path``, ``options``, ``head``)
will be documented as a swagger operation.

You can specify the Swagger unique ``operationId`` with the ``id`` documentation.

.. code-block:: python

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        @api.doc(id='get_something')
        def get(self, id):
            return {}

If not specified, a default operationId is providen with the following pattern::

    {{verb}}_{{resource class name | camelCase2dashes }}

In the previous example, the default generated operationId will be ``get_my_resource``


You can override the default operationId genertor by giving a callable as ``default_id`` parameter to your API.
This callable will receive two positionnal arguments:

 - the resource class name
 - this lower cased HTTP method

.. code-block:: python

    def default_id(resource, method):
        return ''.join((method, resource))

    api = Api(app, default_id=default_id)

In the previous example, the generated operationId will be ``getMyResource``


Each operation will automatically receive the namespace tag.
If the resource is attached to the root API, it will receive the default namespace tag.


Method parameters
~~~~~~~~~~~~~~~~~

For each method, the path parameter are automatically extracted.
You can provide additional parameters (from query parameters, body or form)
or additionnal details on path parameters with the ``params`` documentation.

Input and output models
~~~~~~~~~~~~~~~~~~~~~~~

You can specify the serialized output model with the ``model`` documentation.

You can specify an input format for ``POST`` and ``PUT`` iwth the ``body`` documentation.


.. code-block:: python

    fields = api.model('MyModel', {
        'name': fields.String(description='The name', required=True),
        'type': fields.String(description='The object type', enum=['A', 'B']),
        'age': fields.Integer(min=0),
    })


    @api.model(fields={'name': fields.String, 'age': fields.Integer})
    class Person(fields.Raw):
        def format(self, value):
            return {'name': value.name, 'age': value.age}


    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        @api.doc(model=fields)
        def get(self, id):
            return {}

        @api.doc(model='MyModel', body=Person)
        def post(self, id):
            return {}


You can't have body and form or file parameters at the same time,
it will raise a SpecsError.

Models can be specified with a RequestParser.

.. code-block:: python

    parser = api.parser()
    parser.add_argument('param', type=int, help='Some param', location='form')
    parser.add_argument('in_files', type=FileStorage, location='files')

    @api.route('/with-parser/', endpoint='with-parser')
    class WithParserResource(restplus.Resource):
        @api.doc(parser=parser)
        def get(self):
            return {}


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


Hiding from documentation
-------------------------

You can hide some ressources or methods from documentation using one of the following syntaxes:

.. code-block:: python

    # Hide the full ressource
    @api.route('/resource1/', doc=False)
    class Resource1(Resource):
        def get(self):
            return {}

    @api.route('/resource2/')
    @api.doc(False)
    class Resource2(Resource):
        def get(self):
            return {}

    @api.route('/resource3/')
    @api.hide
    class Resource3(Resource):
        def get(self):
            return {}

    # Hide methods
    @api.route('/resource4/')
    @api.doc(delete=False)
    class Resource4(Resource):
        def get(self):
            return {}

        @api.doc(False)
        def post(self):
            return {}

        @api.hide
        def put(self):
            return {}

        def delete(self):
            return {}
