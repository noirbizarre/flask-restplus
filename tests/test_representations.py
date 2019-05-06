import flask_restplus.representations as rep

from json import dumps, loads
from ujson import dumps as udumps, loads as uloads

payload = {
    'id': 1,
    'name': 'toto',
    'address': 'test',
}


def test_representations_serialization_output_correct(app):
    r = rep.output_json(payload, 200)
    assert loads(r.get_data(True)) == loads(dumps(payload))


def test_config_custom_serializer_is_module(app):
    # now reset serializer
    rep.serializer = None
    # then enforce a custom serializer
    app.config['RESTPLUS_JSON_SERIALIZER'] = 'ujson'
    r2 = rep.output_json(payload, 200)
    assert uloads(r2.get_data(True)) == uloads(udumps(payload))
    assert rep.serializer == udumps


def test_config_custom_serializer_is_function(app):
    # test other config syntax
    rep.serializer = None
    app.config['RESTPLUS_JSON_SERIALIZER'] = 'ujson.dumps'
    rep.output_json(payload, 200)
    assert rep.serializer == udumps


def test_config_custom_serializer_fallback(app):
    # test fallback
    rep.serializer = None
    app.config['RESTPLUS_JSON_SERIALIZER'] = 'ujson.lol.dumps'
    rep.output_json(payload, 200)
    assert rep.serializer == dumps
