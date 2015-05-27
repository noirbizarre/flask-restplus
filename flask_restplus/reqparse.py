# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask.ext.restful import marshal, reqparse

from .model import ApiModel


class Argument(reqparse.Argument):
    def convert(self, value, op):
        if isinstance(self.type, ApiModel) and isinstance(value, dict):
            return marshal(value, self.type)
        return super(Argument, self).convert(value, op)


class RequestParser(reqparse.RequestParser):
    def __init__(self, argument_class=Argument, *args, **kwargs):
        super(RequestParser, self).__init__(argument_class, *args, **kwargs)
