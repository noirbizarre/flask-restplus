# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask.ext.restful import Resource


class SwaggerBaseView(Resource):
    '''
    Base Swagger view with common behavior
    '''
    def __init__(self, api=None):
        self.api = api

    def get(self):
        return {
            'apiVersion': self.api.version,
            'swaggerVersion': '1.2',
            'apis': [],
        }

    def mediatypes(self):
        return ['application/json']
