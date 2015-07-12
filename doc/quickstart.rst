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
    api.init_app(app)


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


Swagger ui
----------

You can turn off swaggger ui by ui argument:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api

    app = Flask(__name__)
    api = Api(app, ui=False)

If you need ui on custom url (default is "/"), you can disable default ui and register it manually:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, apidoc

    app = Flask(__name__)
    api = Api(app, ui=False)

    @api.route('/doc/', endpoint='doc')
    def swagger_ui():
        return apidoc.ui_for(api)

    app.register_blueprint(apidoc.apidoc)  # only needed for assets and templates
