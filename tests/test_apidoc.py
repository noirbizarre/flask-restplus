# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from flask import url_for, Blueprint
from werkzeug.routing import BuildError

import flask_restplus as restplus

from . import TestCase


class APIDocTestCase(TestCase):
    def test_default_apidoc_on_root(self):
        restplus.Api(self.app, version='1.0')

        with self.context():
            self.assertEqual(url_for('doc'), url_for('root'))
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_default_apidoc_on_root_lazy(self):
        api = restplus.Api(version='1.0')
        api.init_app(self.app)

        with self.context():
            self.assertEqual(url_for('doc'), url_for('root'))
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_default_apidoc_on_root_with_blueprint(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        restplus.Api(blueprint, version='1.0')
        self.app.register_blueprint(blueprint)

        with self.context():
            self.assertEqual(url_for('api.doc'), url_for('api.root'))
            with self.app.test_client() as client:
                response = client.get(url_for('api.doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_apidoc_with_custom_validator(self):
        self.app.config['SWAGGER_VALIDATOR_URL'] = 'http://somewhere.com/validator'
        restplus.Api(self.app, version='1.0')

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')
                self.assertIn('validatorUrl: "http://somewhere.com/validator" || null,', str(response.data))

    def test_apidoc_doc_expansion_parameter(self):
        restplus.Api(self.app)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('docExpansion: "none"', str(response.data))

        self.app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('docExpansion: "list"', str(response.data))

        self.app.config['SWAGGER_UI_DOC_EXPANSION'] = 'full'
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('docExpansion: "full"', str(response.data))

    def test_apidoc_doc_jsoneditor_parameter(self):
        restplus.Api(self.app)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('jsonEditor: false', str(response.data))

        self.app.config['SWAGGER_UI_JSONEDITOR'] = False
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('jsonEditor: false', str(response.data))

        self.app.config['SWAGGER_UI_JSONEDITOR'] = True
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('jsonEditor: true', str(response.data))

    def test_apidoc_doc_minified(self):
        restplus.Api(self.app)

        self.app.config['DEBUG'] = True
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('swagger-ui.js', str(response.data))

        self.app.config['DEBUG'] = False
        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertIn('swagger-ui.min.js', str(response.data))

    def test_custom_apidoc_url(self):
        restplus.Api(self.app, version='1.0', doc='/doc/')

        with self.context():
            with self.app.test_client() as client:
                doc_url = url_for('doc')
                root_url = url_for('root')

                self.assertNotEqual(doc_url, root_url)

                response = client.get(root_url)
                self.assertEquals(response.status_code, 404)

                self.assertEqual(doc_url, '/doc/')
                response = client.get(doc_url)
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.content_type, 'text/html; charset=utf-8')

    def test_custom_api_prefix(self):
        prefix = '/api'
        api = restplus.Api(self.app, prefix=prefix)
        api.namespace('resource')
        with self.context():
            root_url = url_for('root')
            self.assertEqual(root_url, prefix)

    def test_custom_apidoc_page(self):
        api = restplus.Api(self.app, version='1.0')
        content = 'My Custom API Doc'

        @api.documentation
        def api_doc():
            return content

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.data.decode('utf8'), content)

    def test_custom_apidoc_page_lazy(self):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint, version='1.0')
        content = 'My Custom API Doc'

        @api.documentation
        def api_doc():
            return content

        self.app.register_blueprint(blueprint)

        with self.context():
            with self.app.test_client() as client:
                response = client.get(url_for('api.doc'))
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.data.decode('utf8'), content)

    def test_disabled_apidoc(self):
        restplus.Api(self.app, version='1.0', doc=False)

        with self.context():
            with self.app.test_client() as client:
                with self.assertRaises(BuildError):
                    url_for('doc')

                response = client.get(url_for('root'))
                self.assertEquals(response.status_code, 404)
