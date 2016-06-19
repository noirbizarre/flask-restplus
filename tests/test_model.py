# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_restplus import fields, Model, SchemaModel

from . import TestCase


class ModelTestCase(TestCase):
    def test_model_as_flat_dict(self):
        model = Model('Person', {
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
            },
            'type': 'object'
        })

    def test_model_as_nested_dict(self):
        address = Model('Address', {
            'road': fields.String,
        })

        person = Model('Person', {
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
            },
            'type': 'object'
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        })

    def test_model_as_dict_with_list(self):
        model = Model('Person', {
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
            },
            'type': 'object'
        })

    def test_model_as_nested_dict_with_list(self):
        address = Model('Address', {
            'road': fields.String,
        })

        person = Model('Person', {
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
            },
            'type': 'object'
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        })

    def test_model_with_required(self):
        model = Model('Person', {
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
            'required': ['birthdate', 'name'],
            'type': 'object'
        })

    def test_model_as_nested_dict_and_required(self):
        address = Model('Address', {
            'road': fields.String,
        })

        person = Model('Person', {
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
            },
            'type': 'object'
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        })

    def test_model_with_discriminator(self):
        model = Model('Person', {
            'name': fields.String(discriminator=True),
            'age': fields.Integer,
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name'],
            'type': 'object'
        })

    def test_model_with_discriminator_override_require(self):
        model = Model('Person', {
            'name': fields.String(discriminator=True, required=False),
            'age': fields.Integer,
        })

        self.assertEqual(model.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'discriminator': 'name',
            'required': ['name'],
            'type': 'object'
        })

    def test_clone_from_instance(self):
        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        child = parent.clone('Child', {
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
            },
            'type': 'object'
        })

    def test_clone_from_class(self):
        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        child = Model.clone('Child', parent, {
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
            },
            'type': 'object'
        })

    def test_clone_from_instance_with_multiple_parents(self):
        grand_parent = Model('GrandParent', {
            'grand_parent': fields.String,
        })

        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        child = grand_parent.clone('Child', parent, {
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
            },
            'type': 'object'
        })

    def test_clone_from_class_with_multiple_parents(self):
        grand_parent = Model('GrandParent', {
            'grand_parent': fields.String,
        })

        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        child = Model.clone('Child', grand_parent, parent, {
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
            },
            'type': 'object'
        })

    def test_inherit_from_instance(self):
        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = parent.inherit('Child', {
            'extra': fields.String,
        })

        self.assertEqual(parent.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'type': 'object'
        })
        self.assertEqual(child.__schema__, {
            'allOf': [
                {'$ref': '#/definitions/Parent'},
                {
                    'properties': {
                        'extra': {'type': 'string'}
                    },
                    'type': 'object'
                }
            ]
        })

    def test_inherit_from_class(self):
        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = Model.inherit('Child', parent, {
            'extra': fields.String,
        })

        self.assertEqual(parent.__schema__, {
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'type': 'object'
        })
        self.assertEqual(child.__schema__, {
            'allOf': [
                {'$ref': '#/definitions/Parent'},
                {
                    'properties': {
                        'extra': {'type': 'string'}
                    },
                    'type': 'object'
                }
            ]
        })

    def test_inherit_from_class_from_multiple_parents(self):
        grand_parent = Model('GrandParent', {
            'grand_parent': fields.String,
        })

        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = Model.inherit('Child', grand_parent, parent, {
            'extra': fields.String,
        })

        self.assertEqual(child.__schema__, {
            'allOf': [
                {'$ref': '#/definitions/GrandParent'},
                {'$ref': '#/definitions/Parent'},
                {
                    'properties': {
                        'extra': {'type': 'string'}
                    },
                    'type': 'object'
                }
            ]
        })

    def test_inherit_from_instance_from_multiple_parents(self):
        grand_parent = Model('GrandParent', {
            'grand_parent': fields.String,
        })

        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child = grand_parent.inherit('Child', parent, {
            'extra': fields.String,
        })

        self.assertEqual(child.__schema__, {
            'allOf': [
                {'$ref': '#/definitions/GrandParent'},
                {'$ref': '#/definitions/Parent'},
                {
                    'properties': {
                        'extra': {'type': 'string'}
                    },
                    'type': 'object'
                }
            ]
        })

    # def test_inherit_inline(self):
    #     parent = Model('Person', {
    #         'name': fields.String,
    #         'age': fields.Integer,
    #     })
    #
    #     child = self.api.inherit('Child', parent, {
    #         'extra': fields.String,
    #     })
    #
    #     Model('Output', {
    #         'child': fields.Nested(child),
    #         'children': fields.List(fields.Nested(child))
    #     })
    #
    #     self.assertIn('Person', Models)
    #     self.assertIn('Child', Models)

    def test_polymorph_inherit_common_ancestor(self):
        class Child1:
            pass

        class Child2:
            pass

        parent = Model('Person', {
            'name': fields.String,
            'age': fields.Integer,
        })

        child1 = parent.inherit('Child1', {
            'extra1': fields.String,
        })

        child2 = parent.inherit('Child2', {
            'extra2': fields.String,
        })

        mapping = {
            Child1: child1,
            Child2: child2,
        }

        output = Model('Output', {
            'child': fields.Polymorph(mapping)
        })

        # Should use the common ancestor
        self.assertEqual(output.__schema__, {
            'properties': {
                'child': {'$ref': '#/definitions/Person'},
            },
            'type': 'object'
        })

    def test_validate(self):
        from jsonschema import FormatChecker
        from werkzeug.exceptions import BadRequest

        class IPAddress(fields.Raw):
            __schema_type__ = 'string'
            __schema_format__ = 'ipv4'

        data = {'ip': '192.168.1'}
        model = Model('MyModel', {'ip': IPAddress()})

        # Test that validate without a FormatChecker does not check if a
        # primitive type conforms to the defined format property
        self.assertIsNone(model.validate(data))

        # Test that validate with a FormatChecker enforces the check of the
        # format property and throws an error if invalid
        with self.assertRaises(BadRequest):
            model.validate(data, format_checker=FormatChecker())


class ModelSchemaTestCase(TestCase):
    def test_model_schema(self):
        address = SchemaModel('Address', {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        })

        person = SchemaModel('Person', {
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
            },
            'type': 'object'
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
            },
            'type': 'object'
        })

        self.assertEqual(address.__schema__, {
            'properties': {
                'road': {
                    'type': 'string'
                },
            },
            'type': 'object'
        })


class ModelDeprecattionsTest(TestCase):
    def test_extend_is_deprecated(self):
        parent = Model('Parent', {
            'name': fields.String,
            'age': fields.Integer,
            'birthdate': fields.DateTime,
        })

        with self.assert_warning(DeprecationWarning):
            child = parent.extend('Child', {
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
            },
            'type': 'object'
        })
