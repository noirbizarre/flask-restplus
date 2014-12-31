Swagger UI documentation
========================

By default ``flask-restplus`` provide a Swagger UI documentation on your API root.


.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, Resource, fields

    app = Flask(__name__)
    api = Api(app, version='1.0', title='Sample API',
        description='A sample API',
    )

    @api.route('/my-resource/<id>', endpoint='my-resource')
    @api.doc(params={'id': 'An ID'})
    class MyResource(Resource):
        def get(self, id):
            return {}

        @api.doc(responses={403: 'Not Authorized'})
        def post(self, id):
            api.abort(403)


    if __name__ == '__main__':
        app.run(debug=True)


If you run the code below and visit your API root URL (http://localhost:5000) you will have an automatically generated SwaggerUI documentation.


You can specify a custom validator url by settings ``config.SWAGGER_VALIDATOR_URL``:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, Resource, fields

    app = Flask(__name__)
    app.config.SWAGGER_VALIDATOR_URL = 'http://domain.com/validator'

    api = Api(app, version='1.0', title='Sample API',
        description='A sample API',
    )

    '...'

    if __name__ == '__main__':
        app.run(debug=True)


You can totaly disable the generated Swagger UI by setting ``ui=False``:

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, Resource, fields

    app = Flask(__name__)
    api = Api(app, ui=False)

    '...'

    if __name__ == '__main__':
        app.run(debug=True)


You can also provide a custom UI by reusing the apidoc blueprint or rolling your own from scratch.

.. code-block:: python

    from flask import Flask, Blueprint, url_for
    from flask.ext.restplus import API, apidoc

    app = Flask(__name__)
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api = Api(blueprint, ui=False)

    '...'

    @blueprint.route('/doc/', endpoint='doc')
    def swagger_ui():
        return apidoc.ui_for(api)


    app.register_blueprint(blueprint)
    app.register_blueprint(apidoc)  # only needed for assets and templates

