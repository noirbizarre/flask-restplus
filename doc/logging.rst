Logging
===============

Flask-RESTPlus extends `Flask's logging <https://flask.palletsprojects.com/en/1.1.x/logging/>`_
by providing each ``API`` and ``Namespace`` it's own standard Python :class:`logging.Logger` instance.
This allows separation of logging on a per namespace basis to allow more fine-grained detail and configuration.

By default, these loggers inherit configuration from the Flask application object logger.

.. code-block:: python

    import logging

    import flask

    from flask_restplus import Api, Resource

    # configure root logger
    logging.basicConfig(level=logging.INFO)

    app = flask.Flask(__name__)

    api = Api(app)


    # each of these loggers uses configuration from app.logger
    ns1 = api.namespace('api/v1', description='test')
    ns2 = api.namespace('api/v2', description='test')


    @ns1.route('/my-resource')
    class MyResource(Resource):
        def get(self):
            # will log
            ns1.logger.info("hello from ns1")
            return {"message": "hello"}


    @ns2.route('/my-resource')
    class MyNewResource(Resource):
        def get(self):
            # won't log due to INFO log level from app.logger
            ns2.logger.debug("hello from ns2")
            return {"message": "hello"}


Loggers can be configured individually to override the configuration from the Flask
application object logger. In the above example, ``ns2`` log level can be set to
``DEBUG`` individually:

.. code-block:: python

    # ns1 will have log level INFO from app.logger
    ns1 = api.namespace('api/v1', description='test')

    # ns2 will have log level DEBUG
    ns2 = api.namespace('api/v2', description='test')
    ns2.logger.setLevel(logging.DEBUG)


    @ns1.route('/my-resource')
    class MyResource(Resource):
        def get(self):
            # will log
            ns1.logger.info("hello from ns1")
            return {"message": "hello"}


    @ns2.route('/my-resource')
    class MyNewResource(Resource):
        def get(self):
            # will log
            ns2.logger.debug("hello from ns2")
            return {"message": "hello"}


Adding additional handlers:


.. code-block:: python

    # configure a file handler for ns1 only
    ns1 = api.namespace('api/v1')
    fh = logging.FileHandler("v1.log")
    ns1.logger.addHandler(fh)

    ns2 = api.namespace('api/v2')


    @ns1.route('/my-resource')
    class MyResource(Resource):
        def get(self):
            # will log to *both* v1.log file and app.logger handlers
            ns1.logger.info("hello from ns1")
            return {"message": "hello"}


    @ns2.route('/my-resource')
    class MyNewResource(Resource):
        def get(self):
            # will log to *only* app.logger handlers
            ns2.logger.info("hello from ns2")
            return {"message": "hello"}