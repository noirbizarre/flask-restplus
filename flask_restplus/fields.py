# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask.ext.restful import fields as base_fields

from .utils import camel_to_dash


class DetailsMixin(object):
    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('description', None)
        self.title = kwargs.pop('title', None)
        self.required = kwargs.pop('required', None)
        self.readonly = kwargs.pop('readonly', None)
        super(DetailsMixin, self).__init__(*args, **kwargs)


class MinMaxMixin(object):
    def __init__(self, *args, **kwargs):
        self.minimum = kwargs.pop('min', None)
        self.maximum = kwargs.pop('max', None)
        super(MinMaxMixin, self).__init__(*args, **kwargs)


class String(DetailsMixin, base_fields.String):
    def __init__(self, *args, **kwargs):
        self.enum = kwargs.pop('enum', None)
        self.discriminator = kwargs.pop('discriminator', None)
        super(String, self).__init__(*args, **kwargs)


class Integer(DetailsMixin, MinMaxMixin, base_fields.Integer):
    pass


class Float(DetailsMixin, MinMaxMixin, base_fields.Float):
    pass


class Arbitrary(DetailsMixin, MinMaxMixin, base_fields.Arbitrary):
    pass


class Boolean(DetailsMixin, base_fields.Boolean):
    pass


class DateTime(DetailsMixin, base_fields.DateTime):
    pass


class Raw(DetailsMixin, base_fields.Raw):
    pass


class Nested(DetailsMixin, base_fields.Nested):
    pass


class List(DetailsMixin, base_fields.List):
    pass


class Url(DetailsMixin, base_fields.Url):
    pass


class Fixed(DetailsMixin, MinMaxMixin, base_fields.Fixed):
    pass


class FormattedString(DetailsMixin, base_fields.FormattedString):
    pass


class ClassName(String):
    def __init__(self, dash=False, **kwargs):
        super(ClassName, self).__init__(**kwargs)
        self.dash = dash

    def output(self, key, obj):
        classname = obj.__class__.__name__
        return camel_to_dash(classname) if self.dash else classname
