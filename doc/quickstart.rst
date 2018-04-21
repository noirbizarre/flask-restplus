.. _quickstart:

Quick start
===========

.. currentmodule:: flask_restplus

This guide assumes you have a working understanding of `Flask <http://flask.pocoo.org>`_,
and that you have already installed both Flask and Flask-RESTPlus.
If not, then follow the steps in the :ref:`installation` section.


Initialization
--------------

As every other extension, you can initialize it with an application object:

.. code-block:: python

    from flask import Flask
    from flask_restplus import Api

    app = Flask(__name__)
    api = Api(app)

or lazily with the factory pattern:

.. code-block:: python

    from flask import Flask
    from flask_restplus import Api

    api = Api()

    app = Flask(__name__)
    api.init_app(app)


A Minimal API
-------------

A minimal Flask-RESTPlus API looks like this:

.. code-block:: python

    from flask import Flask
    from flask_restplus import Resource, Api

    app = Flask(__name__)
    api = Api(app)

    @api.route('/hello')
    class HelloWorld(Resource):
        def get(self):
            return {'hello': 'world'}

    if __name__ == '__main__':
        app.run(debug=True)


Save this as api.py and run it using your Python interpreter.
Note that we've enabled `Flask debugging <http://flask.pocoo.org/docs/quickstart/#debug-mode>`_
mode to provide code reloading and better error messages.

.. code-block:: console

    $ python api.py
    * Running on http://127.0.0.1:5000/
    * Restarting with reloader


.. warning::

    Debug mode should never be used in a production environment!

Now open up a new prompt to test out your API using curl:

.. code-block:: console

    $ curl http://127.0.0.1:5000/hello
    {"hello": "world"}


You can also use the automatic documentation on you API root (by default).
In this case: http://127.0.0.1:5000/.
See :ref:`swaggerui` for a complete documentation on the automatic documentation.


Resourceful Routing
-------------------
The main building block provided by Flask-RESTPlus are resources.
Resources are built on top of :ref:`Flask pluggable views <flask:views>`,
giving you easy access to multiple HTTP methods just by defining methods on your resource.
A basic CRUD resource for a todo application (of course) looks like this:

.. code-block:: python

    from flask import Flask, request
    from flask_restplus import Resource, Api

    app = Flask(__name__)
    api = Api(app)

    todos = {}

    @api.route('/<string:todo_id>')
    class TodoSimple(Resource):
        def get(self, todo_id):
            return {todo_id: todos[todo_id]}

        def put(self, todo_id):
            todos[todo_id] = request.form['data']
            return {todo_id: todos[todo_id]}

    if __name__ == '__main__':
        app.run(debug=True)

You can try it like this:

.. code-block:: console

    $ curl http://localhost:5000/todo1 -d "data=Remember the milk" -X PUT
    {"todo1": "Remember the milk"}
    $ curl http://localhost:5000/todo1
    {"todo1": "Remember the milk"}
    $ curl http://localhost:5000/todo2 -d "data=Change my brakepads" -X PUT
    {"todo2": "Change my brakepads"}
    $ curl http://localhost:5000/todo2
    {"todo2": "Change my brakepads"}


Or from python if you have the `Requests <http://docs.python-requests.org/>`_ library installed:

.. code-block:: python

    >>> from requests import put, get
    >>> put('http://localhost:5000/todo1', data={'data': 'Remember the milk'}).json()
    {u'todo1': u'Remember the milk'}
    >>> get('http://localhost:5000/todo1').json()
    {u'todo1': u'Remember the milk'}
    >>> put('http://localhost:5000/todo2', data={'data': 'Change my brakepads'}).json()
    {u'todo2': u'Change my brakepads'}
    >>> get('http://localhost:5000/todo2').json()
    {u'todo2': u'Change my brakepads'}

Flask-RESTPlus understands multiple kinds of return values from view methods.
Similar to Flask, you can return any iterable and it will be converted into a response,
including raw Flask response objects.
Flask-RESTPlus also support setting the response code and response headers using multiple return values,
as shown below:

.. code-block:: python

    class Todo1(Resource):
        def get(self):
            # Default to 200 OK
            return {'task': 'Hello world'}

    class Todo2(Resource):
        def get(self):
            # Set the response code to 201
            return {'task': 'Hello world'}, 201

    class Todo3(Resource):
        def get(self):
            # Set the response code to 201 and return custom headers
            return {'task': 'Hello world'}, 201, {'Etag': 'some-opaque-string'}


Endpoints
---------

Many times in an API, your resource will have multiple URLs.
You can pass multiple URLs to the :meth:`~Api.add_resource` method or to the :meth:`~Api.route` decorator,
both on the :class:`~Api` object.
Each one will be routed to your :class:`~Resource`:

.. code-block:: python

    api.add_resource(HelloWorld, '/hello', '/world')

    # or

    @api.route('/hello', '/world')
    class HelloWorld(Resource):
        pass

You can also match parts of the path as variables to your resource methods.

.. code-block:: python

    api.add_resource(Todo, '/todo/<int:todo_id>', endpoint='todo_ep')

    # or

    @api.route('/todo/<int:todo_id>', endpoint='todo_ep')
    class HelloWorld(Resource):
        pass

.. note ::

    If a request does not match any of your application's endpoints,
    Flask-RESTPlus will return a 404 error message with suggestions of other
    endpoints that closely match the requested endpoint.
    This can be disabled by setting ``ERROR_404_HELP`` to ``False`` in your application config.


Argument Parsing
----------------

While Flask provides easy access to request data (i.e. querystring or POST form encoded data),
it's still a pain to validate form data.
Flask-RESTPlus has built-in support for request data validation
using a library similar to :mod:`python:argparse`.

.. code-block:: python

    from flask_restplus import reqparse

    parser = reqparse.RequestParser()
    parser.add_argument('rate', type=int, help='Rate to charge for this resource')
    args = parser.parse_args()

.. note ::

    Unlike the :mod:`python:argparse` module, :meth:`~reqparse.RequestParser.parse_args`
    returns a Python dictionary instead of a custom data structure.

Using the :class:`~reqparse.RequestParser` class also gives you sane error messages for free.
If an argument fails to pass validation,
Flask-RESTPlus will respond with a 400 Bad Request and a response highlighting the error.

.. code-block:: console

    $ curl -d 'rate=foo' http://127.0.0.1:5000/todos
    {'status': 400, 'message': 'foo cannot be converted to int'}


The :mod:`~inputs` module provides a number of included common conversion
functions such as :func:`~inputs.date` and :func:`~inputs.url`.

Calling :meth:`~reqparse.RequestParser.parse_args` with ``strict=True`` ensures that an error is thrown if
the request includes arguments your parser does not define.

.. code-block:: python

    args = parser.parse_args(strict=True)


Data Formatting
---------------

By default, all fields in your return iterable will be rendered as-is.
While this works great when you're just dealing with Python data structures,
it can become very frustrating when working with objects.
To solve this problem, Flask-RESTPlus provides the :mod:`fields` module and the
:meth:`marshal_with` decorator.
Similar to the Django ORM and WTForm,
you use the ``fields`` module to describe the structure of your response.

.. code-block:: python

    from collections import OrderedDict

    from flask import Flask
    from flask_restplus import fields, Api, Resource

    app = Flask(__name__)
    api = Api(app)

    model = api.model('Model', {
        'task': fields.String,
        'uri': fields.Url('todo_ep')
    })

    class TodoDao(object):
        def __init__(self, todo_id, task):
            self.todo_id = todo_id
            self.task = task

            # This field will not be sent in the response
            self.status = 'active'

    @api.route('/todo')
    class Todo(Resource):
        @api.marshal_with(model)
        def get(self, **kwargs):
            return TodoDao(todo_id='my_todo', task='Remember the milk')


The above example takes a python object and prepares it to be serialized.
The :meth:`~Api.marshal_with` decorator will apply the transformation described by ``model``.
The only field extracted from the object is ``task``.
The :class:`fields.Url` field is a special field that takes an endpoint name
and generates a URL for that endpoint in the response.
Using the :meth:`~Api.marshal_with` decorator also document the output in the swagger specifications.
Many of the field types you need are already included.
See the :mod:`fields` guide for a complete list.

Order Preservation
~~~~~~~~~~~~~~~~~~

By default, fields order is not preserved as this have a performance drop effect.
If you still require fields order preservation, you can pass a ``ordered=True``
parameter to some classes or function to force order preservation:

- globally on :class:`Api`: ``api = Api(ordered=True)``
- globally on :class:`Namespace`: ``ns = Namespace(ordered=True)``
- locally on :func:`marshal`: ``return marshal(data, fields, ordered=True)``


Full example
------------

See the :doc:`example` section for fully functional example.
