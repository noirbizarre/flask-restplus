# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask_restplus import (marshal_as_stream_with, fields, Api, Resource)


# Add a dummy Resource to verify that the app is properly set.
class HelloWorld(Resource):
    def get(self):
        return {}


class StreamMarshallingTest(object):

    def test_stream_marshalled_decorator(self, app, client):
        api = Api(app)

        class FooResource(Resource):

            fields = {'foo': fields.Float}

            @marshal_as_stream_with(fields)
            def get(self):
                def generate():
                    yield {"foo": 3.0}
                return generate()

        api.add_resource(FooResource, '/api')

        resp = client.get('/api')
        assert resp.status_code == 200
        assert resp.data.decode('utf-8') == '[{"foo": 3.0}]'

    def test_stream_marshalled_mult(self, app, client):
        api = Api(app)

        class FooResource(Resource):
            fields = {'foo': fields.Float}

            @marshal_as_stream_with(fields)
            def get(self):
                def generate():
                    for i in range(3):
                        yield {"foo": i + 1}
                return generate()

        api.add_resource(FooResource, '/api')

        resp = client.get('/api')
        assert resp.status_code == 200
        assert resp.data.decode('utf-8') == '[{"foo": 1.0},{"foo": 2.0},{"foo": 3.0}]'

    def test_no_stream_also_marshalled(self, app, client):
        api = Api(app)

        class FooResource(Resource):
            fields = {'foo': fields.Float}

            @marshal_as_stream_with(fields)
            def get(self):
                return {"foo": 6.0}

        api.add_resource(FooResource, '/api')

        resp = client.get('/api')
        assert resp.status_code == 200
        assert resp.data.decode('utf-8') == '{"foo": 6.0}\n'
