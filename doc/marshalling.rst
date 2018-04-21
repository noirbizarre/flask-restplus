.. _fields:

Response marshalling
====================

.. currentmodule:: flask_restplus


Flask-RESTPlus provides an easy way to control what data you actually render in
your response or expect as in input payload.
With the :mod:`~.fields` module, you can use whatever objects (ORM
models/custom classes/etc.) you want in your resource.
:mod:`~.fields` also lets you format and filter the response
so you don't have to worry about exposing internal data structures.

It's also very clear when looking at your code what data will be rendered and
how it will be formatted.


Basic Usage
-----------
You can define a dict or OrderedDict of fields whose keys are names of attributes or keys on the object to render,
and whose values are a class that will format & return the value for that field.
This example has three fields:
two are :class:`~fields.String` and one is a :class:`~fields.DateTime`,
formatted as an ISO 8601 datetime string (RFC 822 is supported as well):

.. code-block:: python

    from flask_restplus import Resource, fields

    model = api.model('Model', {
        'name': fields.String,
        'address': fields.String,
        'date_updated': fields.DateTime(dt_format='rfc822'),
    })

    @api.route('/todo')
    class Todo(Resource):
        @api.marshal_with(model, envelope='resource')
        def get(self, **kwargs):
            return db_get_todo()  # Some function that queries the db


This example assumes that you have a custom database object (``todo``) that
has attributes ``name``, ``address``, and ``date_updated``.
Any additional attributes on the object are considered private and won't be rendered in the output.
An optional ``envelope`` keyword argument is specified to wrap the resulting output.

The decorator :meth:`~Api.marshal_with` is what actually takes your data object and applies the field filtering.
The marshalling can work on single objects, dicts, or lists of objects.

.. note ::

    :func:`marshal_with` is a convenience decorator, that is functionally
    equivalent to:

    .. code-block:: python

        class Todo(Resource):
            def get(self, **kwargs):
                return marshal(db_get_todo(), model), 200

    The :meth:`@api.marshal_with <Api.marshal_with>` decorator add the swagger documentation ability.

This explicit expression can be used to return HTTP status codes other than 200
along with a successful response (see :func:`~errors.abort` for errors).


Renaming Attributes
-------------------

Often times your public facing field name is different from your internal field name.
To configure this mapping, use the ``attribute`` keyword argument. ::

    model = {
        'name': fields.String(attribute='private_name'),
        'address': fields.String,
    }

A lambda (or any callable) can also be specified as the ``attribute`` ::

    model = {
        'name': fields.String(attribute=lambda x: x._private_name),
        'address': fields.String,
    }

Nested properties can also be accessed with ``attribute``::

    model = {
        'name': fields.String(attribute='people_list.0.person_dictionary.name'),
        'address': fields.String,
    }


Default Values
--------------

If for some reason your data object doesn't have an attribute in your fields list,
you can specify a default value to return instead of :obj:`None`.

.. code-block:: python

    model = {
        'name': fields.String(default='Anonymous User'),
        'address': fields.String,
    }


Custom Fields & Multiple Values
-------------------------------

Sometimes you have your own custom formatting needs.
You can subclass the :class:`fields.Raw` class and implement the format function.
This is especially useful when an attribute stores multiple pieces of information.
e.g. a bit-field whose individual bits represent distinct values.
You can use fields to multiplex a single attribute to multiple output values.


This example assumes that bit 1 in the ``flags`` attribute signifies a
"Normal" or "Urgent" item, and bit 2 signifies "Read" or "Unread".
These items might be easy to store in a bitfield,
but for a human readable output it's nice to convert them to seperate string fields.

.. code-block:: python

    class UrgentItem(fields.Raw):
        def format(self, value):
            return "Urgent" if value & 0x01 else "Normal"

    class UnreadItem(fields.Raw):
        def format(self, value):
            return "Unread" if value & 0x02 else "Read"

    model = {
        'name': fields.String,
        'priority': UrgentItem(attribute='flags'),
        'status': UnreadItem(attribute='flags'),
    }


Url & Other Concrete Fields
---------------------------

Flask-RESTPlus includes a special field, :class:`fields.Url`,
that synthesizes a uri for the resource that's being requested.
This is also a good example of how to add data to your response that's not actually present on your data object.

.. code-block:: python

    class RandomNumber(fields.Raw):
        def output(self, key, obj):
            return random.random()

    model = {
        'name': fields.String,
        # todo_resource is the endpoint name when you called api.route()
        'uri': fields.Url('todo_resource'),
        'random': RandomNumber,
    }


By default :class:`fields.Url` returns a relative uri.
To generate an absolute uri that includes the scheme, hostname and port,
pass the keyword argument ``absolute=True`` in the field declaration.
To override the default scheme, pass the ``scheme`` keyword argument:

.. code-block:: python

    model = {
        'uri': fields.Url('todo_resource', absolute=True)
        'https_uri': fields.Url('todo_resource', absolute=True, scheme='https')
    }


Complex Structures
------------------

You can have a flat structure that :func:`marshal` will transform to a nested structure:

.. code-block:: python

    >>> from flask_restplus import fields, marshal
    >>> import json
    >>>
    >>> resource_fields = {'name': fields.String}
    >>> resource_fields['address'] = {}
    >>> resource_fields['address']['line 1'] = fields.String(attribute='addr1')
    >>> resource_fields['address']['line 2'] = fields.String(attribute='addr2')
    >>> resource_fields['address']['city'] = fields.String
    >>> resource_fields['address']['state'] = fields.String
    >>> resource_fields['address']['zip'] = fields.String
    >>> data = {'name': 'bob', 'addr1': '123 fake street', 'addr2': '', 'city': 'New York', 'state': 'NY', 'zip': '10468'}
    >>> json.dumps(marshal(data, resource_fields))
    '{"name": "bob", "address": {"line 1": "123 fake street", "line 2": "", "state": "NY", "zip": "10468", "city": "New York"}}'

.. note ::
    The address field doesn't actually exist on the data object,
    but any of the sub-fields can access attributes directly from the object
    as if they were not nested.

.. _list-field:

List Field
----------

You can also unmarshal fields as lists ::

    >>> from flask_restplus import fields, marshal
    >>> import json
    >>>
    >>> resource_fields = {'name': fields.String, 'first_names': fields.List(fields.String)}
    >>> data = {'name': 'Bougnazal', 'first_names' : ['Emile', 'Raoul']}
    >>> json.dumps(marshal(data, resource_fields))
    >>> '{"first_names": ["Emile", "Raoul"], "name": "Bougnazal"}'

.. _nested-field:

Nested Field
------------

While nesting fields using dicts can turn a flat data object into a nested
response, you can use :class:`~fields.Nested` to unmarshal nested data
structures and render them appropriately. ::

    >>> from flask_restplus import fields, marshal
    >>> import json
    >>>
    >>> address_fields = {}
    >>> address_fields['line 1'] = fields.String(attribute='addr1')
    >>> address_fields['line 2'] = fields.String(attribute='addr2')
    >>> address_fields['city'] = fields.String(attribute='city')
    >>> address_fields['state'] = fields.String(attribute='state')
    >>> address_fields['zip'] = fields.String(attribute='zip')
    >>>
    >>> resource_fields = {}
    >>> resource_fields['name'] = fields.String
    >>> resource_fields['billing_address'] = fields.Nested(address_fields)
    >>> resource_fields['shipping_address'] = fields.Nested(address_fields)
    >>> address1 = {'addr1': '123 fake street', 'city': 'New York', 'state': 'NY', 'zip': '10468'}
    >>> address2 = {'addr1': '555 nowhere', 'city': 'New York', 'state': 'NY', 'zip': '10468'}
    >>> data = {'name': 'bob', 'billing_address': address1, 'shipping_address': address2}
    >>>
    >>> json.dumps(marshal(data, resource_fields))
    '{"billing_address": {"line 1": "123 fake street", "line 2": null, "state": "NY", "zip": "10468", "city": "New York"}, "name": "bob", "shipping_address": {"line 1": "555 nowhere", "line 2": null, "state": "NY", "zip": "10468", "city": "New York"}}'

This example uses two :class:`~fields.Nested` fields.
The :class:`~fields.Nested` constructor takes a dict of fields to render as sub-fields.input.
The important difference between the :class:`~fields.Nested` constructor and nested dicts (previous example),
is the context for attributes.
In this example,
``billing_address`` is a complex object that has its own fields and
the context passed to the nested field is the sub-object instead of the original ``data`` object.
In other words:
``data.billing_address.addr1`` is in scope here,
whereas in the previous example ``data.addr1`` was the location attribute.
Remember: :class:`~fields.Nested` and :class:`~fields.List` objects create a new scope for attributes.

By default when the sub-object is `None`, an object with default values for the nested fields will be generated instead of `null`. This can be modified by passing the `allow_null` parameter, see the :class:`~fields.Nested` constructor for more details.

Use :class:`~fields.Nested` with :class:`~fields.List` to marshal lists of more complex objects:

.. code-block:: python

    user_fields = api.model('User', {
        'id': fields.Integer,
        'name': fields.String,
    })

    user_list_fields = api.model('UserList', {
        'users': fields.List(fields.Nested(user_fields)),
    })


The ``api.model()`` factory
----------------------------

The :meth:`~Namespace.model` factory allows you to instantiate
and register models to your :class:`API` or :class:`Namespace`.

.. code-block:: python

    my_fields = api.model('MyModel', {
        'name': fields.String,
        'age': fields.Integer(min=0)
    })

    # Equivalent to
    my_fields = Model('MyModel', {
        'name': fields.String,
        'age': fields.Integer(min=0)
    })
    api.models[my_fields.name] = my_fields


Duplicating with ``clone``
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`Model.clone` method allows you to instantiate an augmented model.
It saves you duplicating all fields.

.. code-block:: python

    parent = Model('Parent', {
        'name': fields.String
    })

    child = parent.clone('Child', {
        'age': fields.Integer
    })

The :meth:`Api/Namespace.clone <~Namespace.clone>` also register it on the API.

.. code-block:: python

    parent = api.model('Parent', {
        'name': fields.String
    })

    child = api.clone('Child', parent, {
        'age': fields.Integer
    })


Polymorphism with ``api.inherit``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`Model.inherit` method allows to extend a model in the "Swagger way"
and to start handling polymorphism.

.. code-block:: python

    parent = api.model('Parent', {
        'name': fields.String,
        'class': fields.String(discriminator=True)
    })

    child = api.inherit('Child', parent, {
        'extra': fields.String
    })

The :meth:`Api/Namespace.clone <~Namespace.clone>` will register both the parent and the child
in the Swagger models definitions.

.. code-block:: python

    parent = Model('Parent', {
        'name': fields.String,
        'class': fields.String(discriminator=True)
    })

    child = parent.inherit('Child', {
        'extra': fields.String
    })


The ``class`` field in this example will be populated with the serialized model name
only if the property does not exists in the serialized object.

The :class:`~fields.Polymorph` field allows you to specify a mapping between Python classes
and fields specifications.

.. code-block:: python

    mapping = {
        Child1: child1_fields,
        Child2: child2_fields,
    }

    fields = api.model('Thing', {
        owner: fields.Polymorph(mapping)
    })


Custom fields
-------------

Custom output fields let you perform your own output formatting without having
to modify your internal objects directly.
All you have to do is subclass :class:`~fields.Raw` and implement the :meth:`~fields.Raw.format` method:

.. code-block:: python

    class AllCapsString(fields.Raw):
        def format(self, value):
            return value.upper()


    # example usage
    fields = {
        'name': fields.String,
        'all_caps_name': AllCapsString(attribute='name'),
    }

You can also use the :attr:`__schema_format__`, ``__schema_type__`` and
``__schema_example__`` to specify the produced types and examples:

.. code-block:: python

    class MyIntField(fields.Integer):
        __schema_format__ = 'int64'

    class MySpecialField(fields.Raw):
        __schema_type__ = 'some-type'
        __schema_format__ = 'some-format'

    class MyVerySpecialField(fields.Raw):
        __schema_example__ = 'hello, world'


Skip fields which value is None
-------------------------------

You can skip those fields which values is ``None`` instead of marshaling those fields with JSON value, null.
This feature is useful to reduce the size of response when you have a lots of fields which value may be None,
but which fields are ``None`` are unpredictable.

Let consider the following example with an optional ``skip_none`` keyword argument be set to True.

.. code-block:: python

    >>> from flask_restplus import Model, fields, marshal_with
    >>> import json
    >>> model = Model('Model', {
    ...     'name': fields.String,
    ...     'address_1': fields.String,
    ...     'address_2': fields.String
    ... })
    >>> @marshal_with(model, skip_none=True)
    ... def get():
    ...     return {'name': 'John', 'address_1': None}
    ...
    >>> get()
    OrderedDict([('name', 'John')])

You can see that ``address_1`` and ``address_2`` are skipped by :func:`marshal_with`.
``address_1`` be skipped because value is ``None``.
``address_2`` be skipped because the dictionary return by ``get()`` have no key, ``address_2``.

Skip none in Nested fields
~~~~~~~~~~~~~~~~~~~~~~~~~~

If your module use :class:`fields.Nested`, you need to pass ``skip_none=True`` keyword argument to :class:`fields.Nested`.

.. code-block:: python

    >>> from flask_restplus import Model, fields, marshal_with
    >>> import json
    >>> model = Model('Model', {
    ...     'name': fields.String,
    ...     'location': fields.Nested(location_model, skip_none=True)
    ... })


Define model using JSON Schema
------------------------------

You can define models using `JSON Schema <http://json-schema.org/examples.html>`_ (Draft v4).

.. code-block:: python

    address = api.schema_model('Address', {
        'properties': {
            'road': {
                'type': 'string'
            },
        },
        'type': 'object'
    })

    person = address = api.schema_model('Person', {
        'required': ['address'],
        'properties': {
            'name': {
                'type': 'string'
            },
            'age': {
                'type': 'integer'
            },
            'birthdate': {
                'type': 'string',
                'format': 'date-time'
            },
            'address': {
                '$ref': '#/definitions/Address',
            }
        },
        'type': 'object'
    })
