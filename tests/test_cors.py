# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus import Api, Resource, cors

from . import TestCase


class ErrorsTest(TestCase):
    def test_crossdomain(self):
        class Foo(Resource):
            @cors.crossdomain(origin='*')
            def get(self):
                return "data"

        api = Api(self.app)
        api.add_resource(Foo, '/test/')

        res = self.get('/test/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers['Access-Control-Allow-Origin'], '*')
        self.assertEqual(res.headers['Access-Control-Max-Age'], '21600')
        self.assertIn('HEAD', res.headers['Access-Control-Allow-Methods'])
        self.assertIn('OPTIONS', res.headers['Access-Control-Allow-Methods'])
        self.assertIn('GET', res.headers['Access-Control-Allow-Methods'])

    def test_access_control_expose_headers(self):
        class Foo(Resource):
            @cors.crossdomain(origin='*',
                              expose_headers=['X-My-Header', 'X-Another-Header'])
            def get(self):
                return "data"

        api = Api(self.app)
        api.add_resource(Foo, '/test/')

        res = self.get('/test/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('X-MY-HEADER', res.headers['Access-Control-Expose-Headers'])
        self.assertIn('X-ANOTHER-HEADER', res.headers['Access-Control-Expose-Headers'])

    def test_no_crossdomain(self):
        class Foo(Resource):
            def get(self):
                return "data"

        api = Api(self.app)
        api.add_resource(Foo, '/test/')

        res = self.get('/test/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('Access-Control-Allow-Origin', res.headers)
        self.assertNotIn('Access-Control-Allow-Methods', res.headers)
        self.assertNotIn('Access-Control-Max-Age', res.headers)
