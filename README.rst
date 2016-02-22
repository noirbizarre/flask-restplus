==============
Flask RestPlus
==============

.. image:: https://secure.travis-ci.org/noirbizarre/flask-restplus.png
    :target: http://travis-ci.org/noirbizarre/flask-restplus
    :alt: Build status
.. image:: https://coveralls.io/repos/noirbizarre/flask-restplus/badge.png?branch=master
    :target: https://coveralls.io/r/noirbizarre/flask-restplus?branch=master
    :alt: Code coverage
.. image:: https://requires.io/github/noirbizarre/flask-restplus/requirements.png?branch=master
    :target: https://requires.io/github/noirbizarre/flask-restplus/requirements/?branch=master
    :alt: Requirements Status
.. image:: https://readthedocs.org/projects/flask-restplus/badge/?version=latest
    :target: http://flask-restplus.readthedocs.org/en/0.9.0/
    :alt: Documentation status
.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/noirbizarre/flask-restplus
   :target: https://gitter.im/noirbizarre/flask-restplus?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

Flask-RestPlus provides syntaxic sugar, helpers and automatically generated `Swagger`_ documentation on top of `Flask-Restful`_.

Compatibility
=============

Flask-RestPlus requires Python 2.7+.


Installation
============

You can install Flask-Restplus with pip:

.. code-block:: console

    $ pip install flask-restplus

or with easy_install:

.. code-block:: console

    $ easy_install flask-restplus


Quick start
===========

With Flask-Restplus, you only import the api instance to route and document your endpoints.

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, Resource, fields

    app = Flask(__name__)
    api = Api(app, version='1.0', title='TodoMVC API',
        description='A simple TodoMVC API',
    )

    ns = api.namespace('todos', description='TODO operations')

    todo = api.model('Todo', {
        'id': fields.Integer(readOnly=True, description='The task unique identifier'),
        'task': fields.String(required=True, description='The task details')
    })


    class TodoDAO(object):
        def __init__(self):
            self.counter = 0
            self.todos = []

        def get(self, id):
            for todo in self.todos:
                if todo['id'] == id:
                    return todo
            api.abort(404, "Todo {} doesn't exist".format(id))

        def create(self, data):
            todo = data
            todo['id'] = self.counter = self.counter + 1
            self.todos.append(todo)
            return todo

        def update(self, id, data):
            todo = self.get(id)
            todo.update(data)
            return todo

        def delete(self, id):
            todo = self.get(id)
            self.todos.remove(todo)


    DAO = TodoDAO()
    DAO.create({'task': 'Build an API'})
    DAO.create({'task': '?????'})
    DAO.create({'task': 'profit!'})


    @ns.route('/')
    class TodoList(Resource):
        '''Shows a list of all todos, and lets you POST to add new tasks'''
        @ns.doc('list_todos')
        @ns.marshal_list_with(todo)
        def get(self):
            '''List all tasks'''
            return DAO.todos

        @ns.doc('create_todo')
        @ns.expect(todo)
        @ns.marshal_with(todo, code=201)
        def post(self):
            '''Create a new task'''
            return DAO.create(api.payload), 201


    @ns.route('/<int:id>')
    @ns.response(404, 'Todo not found')
    @ns.param('id', 'The task identifier')
    class Todo(Resource):
        '''Show a single todo item and lets you delete them'''
        @ns.doc('get_todo')
        @ns.marshal_with(todo)
        def get(self, id):
            '''Fetch a given resource'''
            return DAO.get(id)

        @ns.doc('delete_todo')
        @ns.response(204, 'Todo deleted')
        def delete(self, id):
            '''Delete a task given its identifier'''
            DAO.delete(id)
            return '', 204

        @ns.expect(todo)
        @ns.marshal_with(todo)
        def put(self, id):
            '''Update a task given its identifier'''
            return DAO.update(id, api.payload)


    if __name__ == '__main__':
        app.run(debug=True)




Documentation
=============

The documentation is hosted `on Read the Docs <http://flask-restplus.readthedocs.org/en/0.9.0/>`_


.. _Swagger: http://swagger.io/
.. _Flask-Restful: http://flask-restful.readthedocs.org/en/latest/
