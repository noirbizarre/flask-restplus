# -*- coding: utf-8 -*-
__version__ = '0.3.0'
__description__ = 'Helpers, syntaxic sugar and Swagger documentation for Flask-Restful'

try:
    from flask.ext.restful import marshal, marshal_with, abort  # noqa

    from . import fields, reqparse
    from .api import Api  # noqa
    from .resource import Resource  # noqa
    from .exceptions import RestException, SpecsError, ValidationError

    __all__ = (
        '__version__',
        '__description__',
        'Api',
        'Resource',
        'marshal',
        'marshal_with',
        'abort',
        'fields',
        'reqparse',
        'RestException',
        'SpecsError',
        'ValidationError',
    )

except ImportError:
    pass
