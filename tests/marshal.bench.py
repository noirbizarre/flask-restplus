from minibench import Benchmark

from faker import Faker

from flask import Flask
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


class MarshalBenchmark(Benchmark):
    times = 100

    def before_class(self):
        self.app = Flask(__name__)
        self.app.config.setdefault('RESTPLUS_MASK_HEADER', 'X-Fields')

    def bench_marshal_simple(self):
        return marshal(person(), person_fields)

    def bench_marshal_nested(self):
        return marshal(family(), family_fields)

    def bench_marshal_simple_with_mask(self):
        with self.app.test_request_context('/', headers={'X-Fields': 'name'}):
            return marshal(person(), person_fields)

    def bench_marshal_nested_with_mask(self):
        with self.app.test_request_context('/', headers={'X-Fields': 'father,children{name}'}):
            return marshal(family(), family_fields)
