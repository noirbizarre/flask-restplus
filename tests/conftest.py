# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest

from flask import Flask, Blueprint
from flask.testing import FlaskClient

import flask_restplus as restplus


class TestClient(FlaskClient):
    # Borrowed from https://pythonadventures.wordpress.com/2016/03/06/detect-duplicate-keys-in-a-json-file/
    # Thank you to Wordpress author @ubuntuincident, aka Jabba Laci.
    def dict_raise_on_duplicates(self, ordered_pairs):
        """Reject duplicate keys."""
        d = {}
        for k, v in ordered_pairs:
            if k in d:
                raise ValueError("duplicate key: %r" % (k,))
            else:
                d[k] = v
        return d

    def get_json(self, url, status=200, **kwargs):
        response = self.get(url, **kwargs)
        assert response.status_code == status
        assert response.content_type == 'application/json'
        return json.loads(response.data.decode('utf8'), object_pairs_hook=self.dict_raise_on_duplicates)

    def post_json(self, url, data, status=200, **kwargs):
        response = self.post(url, data=json.dumps(data),
                             headers={'content-type': 'application/json'})
        assert response.status_code == status
        assert response.content_type == 'application/json'
        return json.loads(response.data.decode('utf8'))

    def get_specs(self, prefix='', status=200, **kwargs):
        '''Get a Swagger specification for a RestPlus API'''
        return self.get_json('{0}/swagger.json'.format(prefix), status=status, **kwargs)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.test_client_class = TestClient
    yield app


@pytest.fixture
def api(request, app):
    marker = request.node.get_closest_marker('api')
    bpkwargs = {}
    kwargs = {}
    if marker:
        if 'prefix' in marker.kwargs:
            bpkwargs['url_prefix'] = marker.kwargs.pop('prefix')
        if 'subdomain' in marker.kwargs:
            bpkwargs['subdomain'] = marker.kwargs.pop('subdomain')
        kwargs = marker.kwargs
    blueprint = Blueprint('api', __name__, **bpkwargs)
    api = restplus.Api(blueprint, **kwargs)
    app.register_blueprint(blueprint)
    yield api


@pytest.fixture
def mock_app(mocker):
    app = mocker.Mock(Flask)
    # mock Flask app object doesn't have any real loggers -> mock logging
    # set up on Api object
    mocker.patch.object(restplus.Api, '_configure_namespace_logger')
    app.view_functions = {}
    app.extensions = {}
    app.config = {}
    return app


@pytest.fixture(autouse=True)
def _push_custom_request_context(request):
    app = request.getfixturevalue('app')
    options = request.node.get_closest_marker('request_context')

    if options is None:
        return

    ctx = app.test_request_context(*options.args, **options.kwargs)
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
