.. _api:

API
===

.. currentmodule:: flask_restplus

Core
----

.. autoclass:: Api
    :members:
    :inherited-members:

.. autoclass:: Namespace
    :members:


.. autoclass:: Resource
    :members:
    :inherited-members:


Models
------

.. autoclass:: flask_restplus.Model
    :members:

All fields accept a ``required`` boolean and a ``description`` string in ``kwargs``.

.. automodule:: flask_restplus.fields
    :members:


Serialization
-------------
.. currentmodule:: flask_restplus

.. autofunction:: marshal

.. autofunction:: marshal_with

.. autofunction:: marshal_with_field

.. autoclass:: flask_restplus.mask.Mask
    :members:

.. autofunction:: flask_restplus.mask.apply


Request parsing
---------------

.. automodule:: flask_restplus.reqparse
    :members:

Inputs
~~~~~~

.. automodule:: flask_restplus.inputs
    :members:


Errors
------

.. automodule:: flask_restplus.errors
    :members:

.. autoexception:: flask_restplus.fields.MarshallingError

.. autoexception:: flask_restplus.mask.MaskError

.. autoexception:: flask_restplus.mask.ParseError


Internals
---------

These are internal classes or helpers.
Most of the time you shouldn't have to deal directly with them.

.. autoclass:: flask_restplus.api.SwaggerView

.. autoclass:: flask_restplus.swagger.Swagger

.. autoclass:: flask_restplus.postman.PostmanCollectionV1

.. automodule:: flask_restplus.utils
    :members:
