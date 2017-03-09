# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from flask import url_for, Blueprint
from werkzeug.routing import BuildError

import flask_restplus as restplus


class APIDocTest(object):
    def test_default_apidoc_on_root(self, app, client):
        restplus.Api(app, version='1.0')

        assert url_for('doc') == url_for('root')

        response = client.get(url_for('doc'))
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_default_apidoc_on_root_lazy(self, app, client):
        api = restplus.Api(version='1.0')
        api.init_app(app)

        assert url_for('doc') == url_for('root')

        response = client.get(url_for('doc'))
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_default_apidoc_on_root_with_blueprint(self, app, client):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        restplus.Api(blueprint, version='1.0')
        app.register_blueprint(blueprint)

        assert url_for('api.doc') == url_for('api.root')

        response = client.get(url_for('api.doc'))
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_apidoc_with_custom_validator(self, app, client):
        app.config['SWAGGER_VALIDATOR_URL'] = 'http://somewhere.com/validator'
        restplus.Api(app, version='1.0')

        response = client.get(url_for('doc'))
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'
        assert 'validatorUrl: "http://somewhere.com/validator" || null,' in str(response.data)

    def test_apidoc_doc_expansion_parameter(self, app, client):
        restplus.Api(app)

        response = client.get(url_for('doc'))
        assert 'docExpansion: "none"' in str(response.data)

        app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
        response = client.get(url_for('doc'))
        assert 'docExpansion: "list"' in str(response.data)

        app.config['SWAGGER_UI_DOC_EXPANSION'] = 'full'
        response = client.get(url_for('doc'))
        assert 'docExpansion: "full"' in str(response.data)

    def test_apidoc_doc_jsoneditor_parameter(self, app, client):
        restplus.Api(app)

        response = client.get(url_for('doc'))
        assert 'jsonEditor: false' in str(response.data)

        app.config['SWAGGER_UI_JSONEDITOR'] = False
        response = client.get(url_for('doc'))
        assert 'jsonEditor: false' in str(response.data)

        app.config['SWAGGER_UI_JSONEDITOR'] = True
        response = client.get(url_for('doc'))
        assert 'jsonEditor: true' in str(response.data)

    def test_apidoc_doc_language_parameter(self, app, client):
        restplus.Api(app)

        response = client.get(url_for('doc'))
        assert 'lang/translator.js' not in str(response.data)
        assert 'lang/en.js' not in str(response.data)
        assert 'lang/fr.js' not in str(response.data)
        assert 'window.SwaggerTranslator' not in str(response.data)

        app.config['SWAGGER_UI_LANGUAGES'] = ['en', 'fr']
        response = client.get(url_for('doc'))
        assert 'lang/translator.js' in str(response.data)
        assert 'lang/en.js' in str(response.data)
        assert 'lang/fr.js' in str(response.data)
        assert 'window.SwaggerTranslator' in str(response.data)

    def test_apidoc_doc_minified(self, app, client):
        restplus.Api(app)

        app.config['DEBUG'] = True
        response = client.get(url_for('doc'))
        assert 'swagger-ui.js' in str(response.data)

        app.config['DEBUG'] = False
        response = client.get(url_for('doc'))
        assert 'swagger-ui.min.js' in str(response.data)

    def test_custom_apidoc_url(self, app, client):
        restplus.Api(app, version='1.0', doc='/doc/')

        doc_url = url_for('doc')
        root_url = url_for('root')

        assert doc_url != root_url

        response = client.get(root_url)
        assert response.status_code == 404

        assert doc_url == '/doc/'
        response = client.get(doc_url)
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_custom_api_prefix(self, app, client):
        prefix = '/api'
        api = restplus.Api(app, prefix=prefix)
        api.namespace('resource')
        assert url_for('root') == prefix

    def test_custom_apidoc_page(self, app, client):
        api = restplus.Api(app, version='1.0')
        content = 'My Custom API Doc'

        @api.documentation
        def api_doc():
            return content

        response = client.get(url_for('doc'))
        assert response.status_code == 200
        assert response.data.decode('utf8') == content

    def test_custom_apidoc_page_lazy(self, app, client):
        blueprint = Blueprint('api', __name__, url_prefix='/api')
        api = restplus.Api(blueprint, version='1.0')
        content = 'My Custom API Doc'

        @api.documentation
        def api_doc():
            return content

        app.register_blueprint(blueprint)

        response = client.get(url_for('api.doc'))
        assert response.status_code == 200
        assert response.data.decode('utf8') == content

    def test_disabled_apidoc(self, app, client):
        restplus.Api(app, version='1.0', doc=False)

        with pytest.raises(BuildError):
            url_for('doc')

        response = client.get(url_for('root'))
        assert response.status_code == 404
