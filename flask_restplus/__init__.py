# -*- coding: utf-8 -*-
__version__ = '0.1'
__description__ = 'Helpers, syntaxic sugar and Swagger documentation for Flask-Restful'

try:
    from flask.ext.restful import marshal, marshal_with, abort, fields  # noqa

    from .api import Api  # noqa
    from .resource import Resource  # noqa
except:
    pass
