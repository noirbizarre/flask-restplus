# -*- coding: utf-8 -*-
__version__ = '0.5.dev'
__description__ = 'Helpers, syntaxic sugar and Swagger documentation for Flask-Restful'

try:
    from flask.ext.restful import marshal, marshal_with, abort  # noqa

    from . import fields, reqparse, apidoc
    from .api import Api  # noqa
    from .resource import Resource  # noqa
    from .exceptions import RestException, SpecsError, ValidationError
    from .swagger import Swagger

    __all__ = (
        '__version__',
        '__description__',
        'Api',
        'Resource',
        'apidoc',
        'marshal',
        'marshal_with',
        'abort',
        'fields',
        'reqparse',
        'RestException',
        'SpecsError',
        'Swagger',
        'ValidationError',
    )

except ImportError:
    pass
