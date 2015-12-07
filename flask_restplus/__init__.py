# -*- coding: utf-8 -*-
from __future__ import absolute_import
from flask_restful import abort  # noqa

from . import fields, reqparse, apidoc, inputs
from .api import Api  # noqa
from .marshalling import marshal, marshal_with, marshal_with_field  # noqa
from .resource import Resource  # noqa
from .errors import RestError, SpecsError, ValidationError
from .swagger import Swagger
from .__about__ import __version__, __description__

__all__ = (
    '__version__',
    '__description__',
    'Api',
    'Resource',
    'apidoc',
    'marshal',
    'marshal_with',
    'marshal_with_field',
    'abort',
    'fields',
    'inputs',
    'reqparse',
    'RestError',
    'SpecsError',
    'Swagger',
    'ValidationError',
)
