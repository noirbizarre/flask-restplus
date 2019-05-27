import pytest

import flask_restplus.representations as rep
from flask_restplus.utils import preload_serializer

from json import dumps, loads
from ujson import dumps as udumps, loads as uloads

payload = {
    'id': 1,
    'name': 'toto',
    'address': 'test',
}


def test_representations_serialization_output_correct(app):
    print(app.config)
    r = rep.output_json(payload, 200)
    assert loads(r.get_data(True)) == loads(dumps(payload))


def test_config_custom_serializer_is_module(app, api):
    # enforce a custom serializer
    app.config['RESTPLUS_JSON_SERIALIZER'] = 'ujson'
    # now reset serializer
    preload_serializer(app)
    r2 = rep.output_json(payload, 200)
    assert uloads(r2.get_data(True)) == uloads(udumps(payload))
    assert app.config.get('RESTPLUS_CACHED_SERIALIZER') == udumps


def test_config_custom_serializer_is_function(app, api):
    # test other config syntax
    app.config['RESTPLUS_JSON_SERIALIZER'] = 'ujson.dumps'
    preload_serializer(app)
    rep.output_json(payload, 200)
    assert app.config.get('RESTPLUS_CACHED_SERIALIZER') == udumps


def test_config_custom_serializer_fallback(app, api):
    # test fallback
    app.config['RESTPLUS_JSON_SERIALIZER'] = 'ujson.lol.dumps'
    with pytest.warns(UserWarning):
        preload_serializer(app)
    rep.output_json(payload, 200)
    assert app.config.get('RESTPLUS_CACHED_SERIALIZER') == dumps
