# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import request

from flask.ext import restful


class Resource(restful.Resource):

    def __init__(self, api, *args, **kwargs):
        self.api = api
        if self.validate_payload not in self.method_decorators:
            self.method_decorators.insert(0, self.validate_payload)

    def validate_payload(self, func):
        '''Perform a payload validation on expected model'''
        def wrapper(*args, **kwargs):
            # TODO: proper content negociation
            data = request.get_json()
            if hasattr(func, '__apidoc__'):
                model = func.__apidoc__.get('body')
                validate = func.__apidoc__.get('validate', False)
                if model and validate and hasattr(model, 'validate'):
                    model.validate(data, self.api.refresolver)

            return func(*args, **kwargs)
        return wrapper
