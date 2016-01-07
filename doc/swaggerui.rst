.. _swaggerui:

Swagger UI documentation
========================


.. currentmodule:: flask_restplus

By default ``flask-restplus`` provide a Swagger UI documentation on your API root.


.. code-block:: python

    from flask import Flask
    from flask_restplus import Api, Resource, fields

    app = Flask(__name__)
    api = Api(app, version='1.0', title='Sample API',
        description='A sample API',
    )

    @api.route('/my-resource/<id>')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        def get(self, id):
            return {}

        @api.response(403, 'Not Authorized')
        def post(self, id):
            api.abort(403)


    if __name__ == '__main__':
        app.run(debug=True)


If you run the code below and visit your API root URL (http://localhost:5000)
you will have an automatically generated SwaggerUI documentation.

.. image:: _static/screenshot-apidoc-quickstart.png


Customizing the documentation
-----------------------------

You can control the Swagger UI path with the ``doc`` parameter (default to the API root):

.. code-block:: python

    from flask import Flask, Blueprint
    from flask_restplus import Api

    app = Flask(__name__)
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api = Api(blueprint, doc='/doc/')

    app.register_blueprint(blueprint)

    assert url_for('api.doc') == '/api/doc/'


You can specify a custom validator url by setting ``config.SWAGGER_VALIDATOR_URL``:

.. code-block:: python

    from flask import Flask
    from flask_restplus import Api

    app = Flask(__name__)
    app.config.SWAGGER_VALIDATOR_URL = 'http://domain.com/validator'

    api = Api(app)


You can also specify the initial expansion state with the ``config.SWAGGER_UI_DOC_EXPANSION``
setting (``none``, ``list`` or ``full``):

.. code-block:: python

    from flask import Flask
    from flask_restplus import Api

    app = Flask(__name__)
    app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

    api = Api(app)


If you need a custom UI,
you can register a custom view function with the :meth:`~Api.documentation` decorator.
You can provide a custom UI by reusing the apidoc blueprint or rolling your own from scratch.

.. code-block:: python

    from flask import Flask
    from flask_restplus import API, apidoc

    app = Flask(__name__)
    api = Api(app)

    @api.documentation
    def custom_ui():
        return apidoc.ui_for(api)


Disabling the documentation
---------------------------

You can totally disable the generated Swagger UI by setting ``doc=False``:

.. code-block:: python

    from flask import Flask
    from flask_restplus import Api

    app = Flask(__name__)
    api = Api(app, doc=False)
