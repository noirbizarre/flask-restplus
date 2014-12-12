# -*- coding: utf-8 -*-
from __future__ import unicode_literals


__all__ = (
    'RestException',
    'ValidationError',
    'SpecsError',
)


class RestException(Exception):
    '''Base class for all Flask-Restplus Exceptions'''
    def __init__(self, msg):
        self.msg = msg


class ValidationError(RestException):
    '''An helper class for validation errors.'''
    pass


class SpecsError(RestException):
    '''An helper class for incoherent specifications.'''
    pass
