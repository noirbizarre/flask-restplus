import pytest

from faker import Faker

from flask_restplus import marshal, fields

fake = Faker()

person_fields = {
    'name': fields.String,
    'age': fields.Integer
}

family_fields = {
    'father': fields.Nested(person_fields),
    'mother': fields.Nested(person_fields),
    'children': fields.List(fields.Nested(person_fields))
}


def person():
    return {
        'name': fake.name(),
        'age': fake.pyint()
    }


def family():
    return {
        'father': person(),
        'mother': person(),
        'children': [person(), person()]
    }


def marshal_simple():
    return marshal(person(), person_fields)


def marshal_nested():
    return marshal(family(), family_fields)


def marshal_simple_with_mask(app):
    with app.test_request_context('/', headers={'X-Fields': 'name'}):
        return marshal(person(), person_fields)


def marshal_nested_with_mask(app):
    with app.test_request_context('/', headers={'X-Fields': 'father,children{name}'}):
        return marshal(family(), family_fields)


@pytest.mark.benchmark(group='marhsalling')
class MarshallingBenchmark(object):
    def bench_marshal_simple(self, benchmark):
        benchmark(marshal_simple)

    def bench_marshal_nested(self, benchmark):
        benchmark(marshal_nested)

    def bench_marshal_simple_with_mask(self, app, benchmark):
        benchmark(marshal_simple_with_mask, app)

    def bench_marshal_nested_with_mask(self, app, benchmark):
        benchmark(marshal_nested_with_mask, app)
