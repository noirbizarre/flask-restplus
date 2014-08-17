Quick start
===========

As every other extension, you can initialize it with an application object:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api

    app = Flask(__name__)
    api = Api(app)

of lazily with the factory pattern:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api

    api = Api()

    app = Flask(__name__)
    api.init_app(api)


With Flask-Restplus, you only import the api instance to route and document your endpoints.

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, Resource, fields

    app = Flask(__name__)
    api = Api(app)

    @api.route('/somewhere')
    class Somewhere(Resource):
        def get(self):
            return {}

        def post(self)
            api.abort(403)
