# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# import flask

# TODO: FUL-3376
# from werkzeug.exceptions import HTTPException

__all__ = (
    # 'abort',
    'RestError',
    'ValidationError',
    'SpecsError',
)

# TODO: FUL-3376
# def abort(code=500, message=None, **kwargs):
#     '''
#     Properly abort the current request.
#
#     Raise a `HTTPException` for the given status `code`.
#     Attach any keyword arguments to the exception for later processing.
#
#     :param int code: The associated HTTP status code
#     :param str message: An optional details message
#     :param kwargs: Any additional data to pass to the error payload
#     :raise HTTPException:
#     '''
#     try:
#         flask.abort(code)
#     except HTTPException as e:
#         if message:
#             kwargs['message'] = str(message)
#         if kwargs:
#             e.data = kwargs
#         raise


class RestError(Exception):
    '''Base class for all wsgiservice-Restplus Errors'''
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ValidationError(RestError):
    '''An helper class for validation errors.'''
    pass


class SpecsError(RestError):
    '''An helper class for incoherent specifications.'''
    pass
