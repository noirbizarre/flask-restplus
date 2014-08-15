# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from flask.ext.restplus import fields
from flask.ext.restplus.swagger import utils

from . import TestCase


class ExtractPathTestCase(unittest.TestCase):
    def test_extract_static_path(self):
        path = '/test'
        self.assertEqual(utils.extract_path(path), '/test')

    def test_extract_path_with_a_single_simple_parameter(self):
        path = '/test/<parameter>'
        self.assertEqual(utils.extract_path(path), '/test/{parameter}')

    def test_extract_path_with_a_single_typed_parameter(self):
        path = '/test/<string:parameter>'
        self.assertEqual(utils.extract_path(path), '/test/{parameter}')

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<string:other>/'
        self.assertEqual(utils.extract_path(path), '/test/{parameter}/{other}/')


class ExtractPathParamsTestCase(TestCase):
    def test_extract_static_path(self):
        path = '/test'
        self.assertEqual(utils.extract_path_params(path), [])

    def test_extract_single_simple_parameter(self):
        path = '/test/<parameter>'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'string',
            'paramType': 'path',
            'required': True
        }])

    def test_single_int_parameter(self):
        path = '/test/<int:parameter>'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'integer',
            'paramType': 'path',
            'required': True
        }])

    def test_single_float_parameter(self):
        path = '/test/<float:parameter>'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'number',
            'paramType': 'path',
            'required': True
        }])

    def test_extract_path_with_multiple_parameters(self):
        path = '/test/<parameter>/<int:other>/'
        self.assertEqual(utils.extract_path_params(path), [{
            'name': 'parameter',
            'type': 'string',
            'paramType': 'path',
            'required': True
        }, {
            'name': 'other',
            'type': 'integer',
            'paramType': 'path',
            'required': True
        }])

    # def test_extract_registered_converters(self):
    #     class ListConverter(BaseConverter):
    #         def to_python(self, value):
    #             return value.split(',')

    #         def to_url(self, values):
    #             return ','.join(super(ListConverter, self).to_url(value) for value in values)

    #     self.app.url_map.converters['list'] = ListConverter

    #     path = '/test/<list:parameters>'
    #     with self.context():
    #         self.assertEqual(utils.extract_path_params(path), [{
    #             'name': 'parameters',
    #             'type': 'number',
    #             'paramType': 'path',
    #             'required': True
    #         }])


class FieldToPropertyTestCase(unittest.TestCase):
    def test_unknown_field(self):
        prop = utils.field_to_property(None)
        self.assertEqual(prop, {'type': 'string'})

    def test_simple_string_field(self):
        prop = utils.field_to_property(fields.String)
        self.assertEqual(prop, {'type': 'string'})

    def test_simple_integer_field(self):
        prop = utils.field_to_property(fields.Integer)
        self.assertEqual(prop, {'type': 'integer'})

    def test_simple_boolean_field(self):
        prop = utils.field_to_property(fields.Boolean)
        self.assertEqual(prop, {'type': 'boolean'})

    def test_simple_float_field(self):
        prop = utils.field_to_property(fields.Float)
        self.assertEqual(prop, {'type': 'number'})

    def test_simple_arbitrary_field(self):
        prop = utils.field_to_property(fields.Arbitrary)
        self.assertEqual(prop, {'type': 'number'})

    def test_simple_datetime_field(self):
        prop = utils.field_to_property(fields.DateTime)
        self.assertEqual(prop, {'type': 'string', 'format': 'date-time'})
