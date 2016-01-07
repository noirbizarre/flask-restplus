Error handling
==============


HTTPException handling
----------------------

TODO


Handle errors with ``@api.errorhandler()`` decorator
----------------------------------------------------

The ``@api.errorhandler()`` decorator allows you to register
a specific handler for a given exception, in the same manner
that you can do with Flask/Blueprint ``@errorhandler`` decorator.

.. code-block:: python

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


It also allows for overriding the default error handler when used wihtout parameter:

.. code-block:: python

    @api.errorhandler
    def default_error_handler(error):
        '''Default error handler'''
        return {'message': str(error)}, getattr(error, 'code', 500)
