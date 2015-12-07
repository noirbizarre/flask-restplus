# -*- coding: utf-8 -*-
from __future__ import unicode_literals


__all__ = (
    'RestError',
    'ValidationError',
    'SpecsError',
)


class RestError(Exception):
    '''Base class for all Flask-Restplus Errors'''
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
