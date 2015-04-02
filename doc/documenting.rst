Documenting your API with Swagger
=================================

A Swagger API documentation is automatically generated and available on your API root
but you need to provide some details with the ``@api.doc()`` decorator.


Documenting with the ``@api.doc()`` decorator
---------------------------------------------

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


Documenting with the ``@api.model()`` decorator
-----------------------------------------------

The ``@api.model`` decorator allows you to declare the models that your API can serialize.

You can also extend fields and use the ``__schema_format__`` and ``__schema_type__``
to specify the produced types:

.. code-block:: python

    my_fields = api.model('MyModel', {
        'name': fields.String,
        'age': fields.Integer(min=0)
    })

    class MyIntField(fields.Integer):
        __schema_format__ = 'int64'

    class MySpecialField(fields.Raw):
        __schema_type__ = 'some-type'
        __schema_format__ = 'some-format'



Duplicating with ``api.extend``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``api.extend`` method allows you to register an augmented model.
It saves you duplicating all fields.

.. code-block:: python

    parent = api.model('Parent', {
        'name': fields.String
    })

    child = api.extend('Child', parent, {
        'age': fields.Integer
    })


Polymorphism with ``api.inherit``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``api.inherit`` method allows to extend a model in the "Swagger way"
and to start handling polymorphism.
It will register both the parent and the child in the Swagger models definitions.

.. code-block:: python

    parent = api.model('Parent', {
        'name': fields.String,
        'class': fields.String(discriminator=True)
    })

    child = api.inherit('Child', parent, {
        'extra': fields.String
    })

Will produce the following Swagger definitions:

.. code-block:: json

    "Child": {
        "properties": {
            "name": {"type": "string"},
            "class": {"type": "string"}
        },
        "discriminator": "class",
        "required": ["class"]
    },
    "Child": {
        "allOf": [{
                "$ref": "#/definitions/Parent"
            }, {
                "properties": {
                    "extra": {"type": "string"}
                }
            }
        ]
    }

The ``class`` field in this example will be populated with the serialized model name
only if the property does not exists in the serialized object.

The ``Polymorph`` field allows you to specify a mapping between Python classes
and fields specifications.

.. code-block:: python

    mapping = {
        Child1: child1_fields,
        Child2: child2_fields,
    }

    fields = api.model('Thing', {
        owner: fields.Polymorph(mapping)
    })


Documenting with the ``@api.marshal_with()`` decorator
------------------------------------------------------

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


Documenting with the ``@api.response()`` decorator
--------------------------------------------------

The ``@api.response()`` decorator allows you to document the known responses
and is a shortcut for ``@api.doc(responses='...')``.

The following synatxes are equivalents:

.. code-block:: python

    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.response(200, 'Success')
        @api.response(400, 'Validation Error')
        def get(self):
            pass


    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.doc(responses={
            200: 'Success',
            400: 'Validation Error'
        })
        def get(self):
            pass

You can optionnaly specify a response model as third argument:


.. code-block:: python

    model = api.model('Model', {
        'name': fields.String,
    })

    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.response(200, 'Success', model)
        def get(self):
            pass

If you use the ``@api.marshal_with()`` decorator, it automatically document the response:

.. code-block:: python

    model = api.model('Model', {
        'name': fields.String,
    })

    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.response(400, 'Validation error')
        @api.marshal_with(model, code=201, description='Object created')
        def post(self):
            pass

At least, you can specify a default response sent without knowing the response code

.. code-block:: python

    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.response('default', 'Error')
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

    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.doc(id='get_something')
        def get(self):
            return {}

You can also use the first argument for the same purpose:

.. code-block:: python

    @api.route('/my-resource/')
    class MyResource(Resource):
        @api.doc('get_something')
        def get(self):
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

You can specify an input format for ``POST`` and ``PUT`` with the ``body`` documentation.


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
