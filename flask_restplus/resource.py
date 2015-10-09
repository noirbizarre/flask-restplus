# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask.ext import restful


class Resource(restful.Resource):

    def __init__(self, api, *args, **kwargs):
        self.api = api
        self._add_validate_payload()

    def _add_validate_payload(self):
        if self.api.validate_payload not in self.method_decorators:
            self.method_decorators.insert(0, self.api.validate_payload)
