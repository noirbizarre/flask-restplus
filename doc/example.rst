Full example
============

Here is a full example of a `TodoMVC <http://todomvc.com/>`_ API.

.. code-block:: python

    from flask import Flask
    from flask.ext.restplus import Api, Resource, fields
    from werkzeug.contrib.fixers import ProxyFix

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
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
        @api.doc('list_todos')
        @api.marshal_list_with(todo)
        def get(self):
            '''List all tasks'''
            return DAO.todos

        @api.doc('create_todo')
        @api.expect(todo)
        @api.marshal_with(todo, code=201)
        def post(self):
            '''Create a new task'''
            return DAO.create(api.payload), 201


    @ns.route('/<int:id>')
    @api.response(404, 'Todo not found')
    @api.doc(params={'id': 'The task identifier'})
    class Todo(Resource):
        '''Show a single todo item and lets you delete them'''
        @api.doc('get_todo')
        @api.marshal_with(todo)
        def get(self, id):
            '''Fetch a given resource'''
            return DAO.get(id)

        @api.doc('delete_todo')
        @api.response(204, 'Todo deleted')
        def delete(self, id):
            '''Delete a task given its identifier'''
            DAO.delete(id)
            return '', 204

        @api.expect(todo)
        @api.marshal_with(todo)
        def put(self, id):
            '''Update a task given its identifier'''
            return DAO.update(id, api.payload)


    if __name__ == '__main__':
        app.run(debug=True)


You can find other examples in the `github repository examples folder`_.

.. _github repository examples folder: https://github.com/noirbizarre/flask-restplus/tree/master/examples
