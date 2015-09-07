# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint
from flask.ext.restplus import fields, Api

from . import TestCase


class ModelTestCase(TestCase):
    def setUp(self):
        super(ModelTestCase, self).setUp()
        blueprint = Blueprint('api', __name__)
        self.api = Api(blueprint)
        self.app.register_blueprint(blueprint)

    def test_model_as_flat_dict(self):
        model = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            }
        })

    def test_model_as_nested_dict(self):
        address = self.api.model('Address', {
            'road': fields.String,
        })

        person = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
            'address': fields.Nested(address)
        })

        self.assertEqual(person.__schema__, {
            # 'required': ['address'],
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                },
                'address': {
                    '$ref': '#/definitions/Address',
                }
            }
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            }
        })

    def test_model_as_dict_with_list(self):
        model = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
            'tags': fields.List(fields.String),
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'tags': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            }
        })

    def test_model_as_nested_dict_with_list(self):
        address = self.api.model('Address', {
            'road': fields.String,
        })

        person = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
            'addresses': fields.List(fields.Nested(address))
        })

        self.assertEqual(person.__schema__, {
            # 'required': ['address'],
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                },
                'addresses': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/Address',
                    }
                }
            }
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            }
        })

    def test_model_with_required(self):
        model = self.api.model('Person', {
            'name': fields.String(required=True),
            'age': fields.Integer,
            'birthdate': fields.DateTime(required=True),
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                }
            },
            'required': ['birthdate', 'name']
        })

    def test_model_as_nested_dict_and_required(self):
        address = self.api.model('Address', {
            'road': fields.String,
        })

        person = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
            'address': fields.Nested(address, required=True)
        })

        self.assertEqual(person.__schema__, {
            'required': ['address'],
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                },
                'address': {
                    '$ref': '#/definitions/Address',
                }
            }
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            }
        })

    def test_model_with_discriminator(self):
        model = self.api.model('Person', {
            'name': fields.String(discriminator=True),
            'age': fields.Integer,
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name']
        })

    def test_model_with_discriminator_override_require(self):
        model = self.api.model('Person', {
            'name': fields.String(discriminator=True, required=False),
            'age': fields.Integer,
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name']
        })

    def test_extend(self):
        parent = self.api.model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        child = self.api.extend('Child', parent, {
            'extra': fields.String,
        })

        self.assertEqual(child.__schema__, {
            'properties': {
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                },
                'extra': {
                    'type': 'string'
                }
            }
        })

        self.assertIn('Parent', self.api.models)
        self.assertIn('Child', self.api.models)

    def test_extend_with_multiple_parents(self):
        grand_parent = self.api.model('GrandParent', {
            'grand_parent': fields.String,
        })

        parent = self.api.model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        child = self.api.extend('Child', [grand_parent, parent], {
            'extra': fields.String,
        })

        self.assertEqual(child.__schema__, {
            'properties': {
                'grand_parent': {
                    'type': 'string'
                },
                'name': {
                    'type': 'string'
                },
                'age': {
                    'type': 'integer'
                },
                'birthdate': {
                    'type': 'string',
                    'format': 'date-time'
                },
                'extra': {
                    'type': 'string'
                }
            }
        })

        self.assertIn('GrandParent', self.api.models)
        self.assertIn('Parent', self.api.models)
        self.assertIn('Child', self.api.models)

    def test_inherit(self):
        parent = self.api.model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = self.api.inherit('Child', parent, {
            'extra': fields.String,
        })

        self.assertEqual(parent.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            }
        })
        self.assertEqual(child.__schema__, {
            'allOf': [{
                    '$ref': '#/definitions/Parent'
                }, {
                    'properties': {
                        'extra': {'type': 'string'}
                    }
                }
            ]
        })

        self.assertIn('Parent', self.api.models)
        self.assertIn('Child', self.api.models)

    def test_inherit_inline(self):
        parent = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = self.api.inherit('Child', parent, {
            'extra': fields.String,
        })

        self.api.model('Output', {
            'child': fields.Nested(child),
            'children': fields.List(fields.Nested(child))
        })

        self.assertIn('Person', self.api.models)
        self.assertIn('Child', self.api.models)

    def test_polymorph_inherit_common_ancestor(self):
        class Child1:
            pass

        class Child2:
            pass

        parent = self.api.model('Person', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child1 = self.api.inherit('Child1', parent, {
            'extra1': fields.String,
        })

        child2 = self.api.inherit('Child2', parent, {
            'extra2': fields.String,
        })

        mapping = {
            Child1: child1,
            Child2: child2,
        }

        output = self.api.model('Output', {
            'child': fields.Polymorph(mapping)
        })

        # Should use the common ancestor
        self.assertEqual(output.__schema__, {
            'properties': {
                'child': {'$ref': '#/definitions/Person'},
            }
        })
