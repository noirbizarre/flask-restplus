import pytest

from flask_restplus import fields, Api, Resource
from flask_restplus.swagger import Swagger

api = Api()

person = api.model('Person', {
    'name': fields.String,
    'age': fields.Integer
})

family = api.model('Family', {
    'name': fields.String,
    'father': fields.Nested(person),
    'mother': fields.Nested(person),
    'children': fields.List(fields.Nested(person))
})


@api.route('/families', endpoint='families')
class Families(Resource):
    @api.marshal_with(family)
    def get(self):
        '''List all families'''
        pass

    @api.marshal_with(family)
    @api.response(201, 'Family created')
    def post(self):
        '''Create a new family'''
        pass


@api.route('/families/<name>/', endpoint='family')
@api.response(404, 'Family not found')
class Family(Resource):
    @api.marshal_with(family)
    def get(self):
        '''Get a family given its name'''
        pass

    @api.marshal_with(family)
    def put(self):
        '''Update a family given its name'''
        pass


@api.route('/persons', endpoint='persons')
class Persons(Resource):
    @api.marshal_with(person)
    def get(self):
        '''List all persons'''
        pass

    @api.marshal_with(person)
    @api.response(201, 'Person created')
    def post(self):
        '''Create a new person'''
        pass


@api.route('/persons/<name>/', endpoint='person')
@api.response(404, 'Person not found')
class Person(Resource):
    @api.marshal_with(person)
    def get(self):
        '''Get a person given its name'''
        pass

    @api.marshal_with(person)
    def put(self):
        '''Update a person given its name'''
        pass


def swagger_specs(app):
    with app.test_request_context('/'):
        return Swagger(api).as_dict()


def swagger_specs_cached(app):
    with app.test_request_context('/'):
        return api.__schema__


@pytest.mark.benchmark(group='swagger')
class SwaggerBenchmark(object):
    @pytest.fixture(autouse=True)
    def register(self, app):
        api.init_app(app)

    def bench_swagger_specs(self, app, benchmark):
        benchmark(swagger_specs, app)

    def bench_swagger_specs_cached(self, app, benchmark):
        benchmark(swagger_specs_cached, app)
