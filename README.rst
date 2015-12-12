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
    :target: http://flask-restplus.readthedocs.org/en/0.8.5/
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
    from flask_restplus import Api, Resource, fields

    app = Flask(__name__)
    api = Api(app, version='1.0', title='Todo API',
        description='A simple TODO API extracted from the original flask-restful example',
    )

    ns = api.namespace('todos', description='TODO operations')

    TODOS = {
        'todo1': {'task': 'build an API'},
        'todo2': {'task': '?????'},
        'todo3': {'task': 'profit!'},
    }

    todo = api.model('Todo', {
        'task': fields.String(required=True, description='The task details')
    })

    listed_todo = api.model('ListedTodo', {
        'id': fields.String(required=True, description='The todo ID'),
        'todo': fields.Nested(todo, description='The Todo')
    })


    def abort_if_todo_doesnt_exist(todo_id):
        if todo_id not in TODOS:
            api.abort(404, "Todo {} doesn't exist".format(todo_id))

    parser = api.parser()
    parser.add_argument('task', type=str, required=True, help='The task details', location='form')


    @ns.route('/<string:todo_id>')
    @api.response(404, 'Todo not found')
    @api.doc(params={'todo_id': 'The Todo ID'})
    class Todo(Resource):
        '''Show a single todo item and lets you delete them'''
        @api.doc(description='todo_id should be in {0}'.format(', '.join(TODOS.keys())))
        @api.marshal_with(todo)
        def get(self, todo_id):
            '''Fetch a given resource'''
            abort_if_todo_doesnt_exist(todo_id)
            return TODOS[todo_id]

        @api.response(204, 'Todo deleted')
        def delete(self, todo_id):
            '''Delete a given resource'''
            abort_if_todo_doesnt_exist(todo_id)
            del TODOS[todo_id]
            return '', 204

        @api.doc(parser=parser)
        @api.marshal_with(todo)
        def put(self, todo_id):
            '''Update a given resource'''
            args = parser.parse_args()
            task = {'task': args['task']}
            TODOS[todo_id] = task
            return task


    @ns.route('/')
    class TodoList(Resource):
        '''Shows a list of all todos, and lets you POST to add new tasks'''
        @api.marshal_list_with(listed_todo)
        def get(self):
            '''List all todos'''
            return [{'id': id, 'todo': todo} for id, todo in TODOS.items()]

        @api.doc(parser=parser)
        @api.marshal_with(todo, code=201)
        def post(self):
            '''Create a todo'''
            args = parser.parse_args()
            todo_id = 'todo%d' % (len(TODOS) + 1)
            TODOS[todo_id] = {'task': args['task']}
            return TODOS[todo_id], 201


    if __name__ == '__main__':
        app.run(debug=True)


Documentation
=============

The documentation is hosted `on Read the Docs <http://flask-restplus.readthedocs.org/en/0.8.5/>`_


.. _Swagger: http://swagger.io/
.. _Flask-Restful: http://flask-restful.readthedocs.org/en/latest/
