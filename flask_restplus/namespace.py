# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class ApiNamespace(object):
    def __init__(self, api, name, description=None, endpoint=None, json_path=None, **kwargs):
        self.api = api
        self.name = name
        self.path = '/' + name
        self.description = description
        self.resources = []
        self.models = []
        self.endpoint = str(endpoint or 'ns-{0}'.format(self.name.lower().replace(' ', '-')))
        self.json_path = json_path or '{0}.json'.format(self.path)

    @property
    def full_endpoint(self):
        return '{0}.{1}'.format(self.api.endpoint, self.endpoint)

    def add_resource(self, resource, *urls, **kwargs):
        self.resources.append((resource, urls, kwargs))
        self.api.add_resource(resource, *urls, namespace=self, **kwargs)

    def add_model(self, model):
        self.models.append(model)

    def route(self, *urls, **kwargs):
        def wrapper(cls):
            doc = kwargs.pop('doc', None)
            if doc:
                self.api._handle_api_doc(cls, doc)
            self.add_resource(cls, *[self.path + url for url in urls], **kwargs)
            return cls
        return wrapper
