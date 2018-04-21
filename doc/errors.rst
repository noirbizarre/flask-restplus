Error handling
==============

.. currentmodule:: flask_restplus

HTTPException handling
----------------------

Werkzeug HTTPException are automatically properly seriliazed
reusing the description attribute.

.. code-block:: python

    from werkzeug.exceptions import BadRequest
    raise BadRequest()

will return a 400 HTTP code and output

.. code-block:: json

    {
        "message": "The browser (or proxy) sent a request that this server could not understand."
    }

whereas this:

.. code-block:: python

    from werkzeug.exceptions import BadRequest
    raise BadRequest('My custom message')

will output

.. code-block:: json

    {
        "message": "My custom message"
    }

You can attach extras attributes to the output by providing a data attribute to your exception.

.. code-block:: python

    from werkzeug.exceptions import BadRequest
    e = BadRequest('My custom message')
    e.data = {'custom': 'value'}
    raise e

will output

.. code-block:: json

    {
        "message": "My custom message",
        "custom": "value"
    }

The Flask abort helper
----------------------

The :meth:`abort <werkeug.exceptions.Aborter.__call__>` helper
properly wraps errors into a :exc:`~werkzeug.exceptions.HTTPException`
so it will have the same behavior.

.. code-block:: python

    from flask import abort
    abort(400)

will return a 400 HTTP code and output

.. code-block:: json

    {
        "message": "The browser (or proxy) sent a request that this server could not understand."
    }

whereas this:

.. code-block:: python

    from flask import abort
    abort(400, 'My custom message')

will output

.. code-block:: json

    {
        "message": "My custom message"
    }


The Flask-RESTPlus abort helper
-------------------------------

The :func:`errors.abort` and the :meth:`Namespace.abort` helpers
works like the original Flask :func:`flask.abort`
but it will also add the keyword arguments to the response.

.. code-block:: python

    from flask_restplus import abort
    abort(400, custom='value')

will return a 400 HTTP code and output

.. code-block:: json

    {
        "message": "The browser (or proxy) sent a request that this server could not understand.",
        "custom": "value"
    }

whereas this:

.. code-block:: python

    from flask import abort
    abort(400, 'My custom message', custom='value')

will output

.. code-block:: json

    {
        "message": "My custom message",
        "custom": "value"
    }


The ``@api.errorhandler`` decorator
-----------------------------------

The :meth:`@api.errorhandler <Api.errorhandler>` decorator
allows you to register a specific handler for a given exception (or any exceptions inherited from it), in the same manner
that you can do with Flask/Blueprint :meth:`@errorhandler <flask:flask.Flask.errorhandler>` decorator.

.. code-block:: python

    @api.errorhandler(RootException)
    def handle_root_exception(error):
        '''Return a custom message and 400 status code'''
        return {'message': 'What you want'}, 400

    @api.errorhandler(CustomException)
    def handle_custom_exception(error):
        '''Return a custom message and 400 status code'''
        return {'message': 'What you want'}, 400


    @api.errorhandler(AnotherException)
    def handle_another_exception(error):
        '''Return a custom message and 500 status code'''
        return {'message': error.specific}


    @api.errorhandler(FakeException)
    def handle_fake_exception_with_header(error):
        '''Return a custom message and 400 status code'''
        return {'message': error.message}, 400, {'My-Header': 'Value'}

You can also document the error:

.. code-block:: python

    @api.errorhandler(FakeException)
    @api.marshal_with(error_fields, code=400)
    @api.header('My-Header',  'Some description')
    def handle_fake_exception_with_header(error):
        '''This is a custom error'''
        return {'message': error.message}, 400, {'My-Header': 'Value'}


    @api.route('/test/')
    class TestResource(Resource):
        def get(self):
            '''
            Do something

            :raises CustomException: In case of something
            '''
            pass

In this example, the ``:raise:`` docstring will be automatically extracted
and the response 400 will be documented properly.


It also allows for overriding the default error handler when used without parameter:

.. code-block:: python

    @api.errorhandler
    def default_error_handler(error):
        '''Default error handler'''
        return {'message': str(error)}, getattr(error, 'code', 500)

.. note ::

    Flask-RESTPlus will return a message in the error response by default.
    If a custom response is required as an error and the message field is not needed,
    it can be disabled by setting ``ERROR_INCLUDE_MESSAGE`` to ``False`` in your application config.

Error handlers can also be registered on namespaces. An error handler registered on a namespace
will override one registered on the api.


.. code-block:: python

    ns = Namespace('cats', description='Cats related operations')

    @ns.errorhandler
    def specific_namespace_error_handler(error):
        '''Namespace error handler'''
        return {'message': str(error)}, getattr(error, 'code', 500)
