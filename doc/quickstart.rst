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


Swagger UI
----------

You can control the Swagger UI path with the ``doc`` parameter (default to the API root):

.. code-block:: python

    from flask import Flask, Blueprint
    from flask.ext.restplus import Api

    app = Flask(__name__)
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api = Api(blueprint, doc='/doc/')

    app.register_blueprint(blueprint)

    assert url_for('api.doc') == '/api/doc/'

If you need a custom UI, you can register a custom view function
with the ``@api.documentation`` decorator:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, apidoc

    app = Flask(__name__)
    api = Api(app)

    @api.documentation
    def custom_ui():
        return apidoc.ui_for(api)
