# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from flask.ext import restplus

from . import TestCase


class ReqParseTestCase(TestCase):
    def setUp(self):
        super(ReqParseTestCase, self).setUp()
        self.api = restplus.Api(self.app)
        self.parser = self.api.parser()

    def post(self, url, data, status=200):
        headers = {
            'Content-Type': 'application/json'
        }

        with self.app.test_client() as client:
            response = client.post(url, data=json.dumps(data), headers=headers)
            self.assertEquals(response.status_code, status)
            return json.loads(response.data.decode('utf8'))

    def test_parse_model(self):
        fields = self.api.model('Todo', {
            'task': restplus.fields.String(required=True)
        })

        parser = self.parser
        parser.add_argument('todo', type=fields, required=True)

        @self.api.route('/reqparse', endpoint='reqparse')
        class TestApi(restplus.Resource):
            def post(self):
                args = parser.parse_args()
                return args['todo']

        data = self.post('/reqparse', {'todo': {'task': 'aaa'}})
        self.assertEqual(data, {'task': 'aaa'})

    def test_copy(self):
        parser = self.parser
        cloned = parser.copy()
