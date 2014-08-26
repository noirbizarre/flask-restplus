# -*- coding: utf-8 -*-
__version__ = '0.2.1'
__description__ = 'Helpers, syntaxic sugar and Swagger documentation for Flask-Restful'

try:
    from flask.ext.restful import marshal, marshal_with, abort  # noqa

    from . import fields, reqparse
    from .api import Api  # noqa
    from .resource import Resource  # noqa

    __all__ = ('__version__', '__description__', 'Api', 'Resource', 'marshal', 'marshal_with', 'abort', 'fields', 'reqparse')

except ImportError:
    pass
