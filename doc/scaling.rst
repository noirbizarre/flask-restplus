.. _scaling:

Scaling your project
====================

.. currentmodule:: flask_restplus

This page covers building a slightly more complex Flask-RESTPlus app that will
cover out some best practices when setting up a real-world Flask-RESTPlus-based API.
The :ref:`quickstart` section is great for getting started with your first Flask-RESTplus app,
so if you're new to Flask-RESTPlus you'd be better off checking that out first.


Multiple namespaces
-------------------

There are many different ways to organize your Flask-RESTPlus app,
but here we'll describe one that scales pretty well with larger apps
and maintains a nice level organization.

Flask-RESTPlus provides a way to use almost the same pattern as Blueprint.
The main idea is to split your app into reusables namespaces.

Here's an example directory structure::

    project/
    ├── app.py
    ├── core
    │   ├── __init__.py
    │   ├── utils.py
    │   └── ...
    └── apis
        ├── __init__.py
        ├── namespace1.py
        ├── namespace2.py
        ├── ...
        └── namespaceX.py


The `app` module will serve as a main application entry point following one of the classic
Flask patterns (See :ref:`flask:larger-applications` and :ref:`flask:app-factories`).

The `core` module is an example, it caontains the business logic.
In fact, you call it whatever you want, and there can be many packages.

The `apis` package will be your main API entry point that you need to import and register on the application,
whereas the namespaces modules are reusables namespaces designed like you would do with blueprint.

A namespace module will contains models and resources declarations declaration.
For example:

.. code-block:: Python

    from flask_restplus import Namespace, Resource, fields

    api = Namespace('cats', description='Cats related operations')

    cat = api.model('Cat', {
        'id': fields.String(required=True, description='The cat identifier'),
        'name': fields.String(required=True, description='The cat name'),
    })

    CATS = [
        {'id': 'felix', 'name': 'Felix'},
    ]

    @api.route('/')
    class CatList(Resource):
        @api.doc('list_cats')
        @api.marshal_list_with(cat)
        def get(self):
            '''List all cats'''
            return CATS

    @api.route('/<id>')
    @api.param('id', 'The cat identifier')
    @api.response(404, 'Cat not found')
    class Cat(Resource):
        @api.doc('get_cat')
        @api.marshal_with(cat)
        def get(self, id):
            '''Fetch a cat given its identifier'''
            for cat in CATS:
                if cat['id'] == id:
                    return cat
            api.abort(404)


The `apis.__init__` module should aggregate them:

.. code-block:: Python

    from flask_restplus import Api

    from .namespace1 import api as ns1
    from .namespace2 import api as ns2
    # ...
    from .namespaceX import api as nsX

    api = Api(
        title='My Title',
        version='1.0',
        description='A description',
        # All API metadatas
    )

    api.add_namespace(ns1)
    api.add_namespace(ns2)
    # ...
    api.add_namespace(nsX)


You can define custom url-prefixes for namespaces during registering them in your API.
You don't have to bind url-prefix while declaration of Namespace object.

.. code-block:: Python

    from flask_restplus import Api

    from .namespace1 import api as ns1
    from .namespace2 import api as ns2
    # ...
    from .namespaceX import api as nsX

    api = Api(
        title='My Title',
        version='1.0',
        description='A description',
        # All API metadatas
    )

    api.add_namespace(ns1, path='/prefix/of/ns1')
    api.add_namespace(ns2, path='/prefix/of/ns2')
    # ...
    api.add_namespace(nsX, path='/prefix/of/nsX')


Using this pattern, you simple have to register your API in `app.py` like that:

.. code-block:: Python

    from flask import Flask
    from apis import api

    app = Flask(__name__)
    api.init_app(app)

    app.run(debug=True)


Use With Blueprints
-------------------

See :ref:`blueprints` in the Flask documentation for what blueprints are and why you should use them.
Here's an example of how to link an :class:`Api` up to a :class:`~flask.Blueprint`.

.. code-block:: python

    from flask import Blueprint
    from flask_restplus import Api

    blueprint = Blueprint('api', __name__)
    api = Api(blueprint)
    # ...

Using a blueprint will allow you to mount your API on any url prefix and/or subdomain
in you application:


.. code-block:: Python

    from flask import Flask
    from apis import blueprint as api

    app = Flask(__name__)
    app.register_blueprint(api, url_prefix='/api/1')
    app.run(debug=True)

.. note ::

    Calling :meth:`Api.init_app` is not required here because registering the
    blueprint with the app takes care of setting up the routing for the application.

.. note::

    When using blueprints, remember to use the blueprint name with :func:`~flask.url_for`:

    .. code-block:: python

        # without blueprint
        url_for('my_api_endpoint')

        # with blueprint
        url_for('api.my_api_endpoint')


Multiple APIs with reusable namespaces
--------------------------------------

Sometimes you need to maintain multiple versions of an API.
If you built your API using namespaces composition,
it's quite simple to scale it to multiple APIs.

Given the previous layout, we can migrate it to the following directory structure::

    project/
    ├── app.py
    ├── apiv1.py
    ├── apiv2.py
    └── apis
        ├── __init__.py
        ├── namespace1.py
        ├── namespace2.py
        ├── ...
        └── namespaceX.py

Each `apivX` module will have the following pattern:

.. code-block:: python

    from flask import Blueprint
    from flask_restplus import Api

    api = Api(blueprint)

    from .apis.namespace1 import api as ns1
    from .apis.namespace2 import api as ns2
    # ...
    from .apis.namespaceX import api as nsX

    blueprint = Blueprint('api', __name__, url_prefix='/api/1')
    api = Api(blueprint
        title='My Title',
        version='1.0',
        description='A description',
        # All API metadatas
    )

    api.add_namespace(ns1)
    api.add_namespace(ns2)
    # ...
    api.add_namespace(nsX)

And the app will simply mount them:

.. code-block:: Python

    from flask import Flask
    from api1 import blueprint as api1
    from apiX import blueprint as apiX

    app = Flask(__name__)
    app.register_blueprint(api1)
    app.register_blueprint(apiX)
    app.run(debug=True)


These are only proposals and you can do whatever suits your needs.
Look at the `github repository examples folder`_ for more complete examples.

.. _github repository examples folder: https://github.com/noirbizarre/flask-restplus/tree/master/examples
