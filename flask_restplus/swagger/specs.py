# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for
from .base import SwaggerBaseView


class ApiSpecs(SwaggerBaseView):
    def get(self):
        response = super(ApiSpecs, self).get()
        infos = {}
        if self.api.title:
            infos['title'] = self.api.title
        if self.api.description:
            infos['description'] = self.api.description
        if self.api.terms_url:
            infos['termsOfServiceUrl'] = self.api.terms_url
        if self.api.contact:
            infos['contact'] = self.api.contact
        if self.api.license:
            infos['license'] = self.api.license
        if self.api.license_url:
            infos['licenseUrl'] = self.api.license_url
        if infos:
            response['infos'] = infos
        if self.api.authorizations:
            response['authorizations'] = self.api.authorizations
        for ns in self.api.namespaces:
            if len(ns.resources):
                response['apis'].append(self.serialize_namespace(ns))
        return response

    def serialize_namespace(self, namespace):
        return {
            'path': url_for(namespace.full_endpoint, _external=True),
            'description': namespace.description,
        }
