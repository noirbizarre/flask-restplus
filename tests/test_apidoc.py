# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from flask import url_for, Blueprint
from flask.ext import restplus

from . import TestCase


class APIDocTestCase(TestCase):
    def test_default_apidoc_on_root(self):
        restplus.Api(self.app, version='1.0')

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('root'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_default_apidoc_on_root_lazy(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('root'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_default_apidoc_on_root_with_blueprint(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        restplus.Api(blueprint, version='1.0')
        self.app.register_blueprint(blueprint)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('api.root'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_apidoc_with_custom_validator(self):
        self.app.config['SWAGGER_VALIDATOR_URL'] = 'http://somewhere.com/validator'
        restplus.Api(self.app, version='1.0')

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('root'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')
                self.assertIn('validatorUrl: "http://somewhere.com/validator" || null,', str(response.data))

    def test_apidoc_doc_expansion_parameter(self):
        restplus.Api(self.app)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('root'))
                self.assertIn('docExpansion: "none"', str(response.data))

        self.app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('root'))
                self.assertIn('docExpansion: "list"', str(response.data))

        self.app.config['SWAGGER_UI_DOC_EXPANSION'] = 'full'
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('root'))
                self.assertIn('docExpansion: "full"', str(response.data))

    def test_custom_apidoc_url(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint, version='1.0', ui=False)

        @blueprint.route('/doc/', endpoint='doc')
        def swagger_ui():
            return restplus.apidoc.ui_for(api)

        self.app.register_blueprint(blueprint)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('api.root'))
                self.assertEquals(response.status_code, 404)

                response = client.get(url_for('api.doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')
