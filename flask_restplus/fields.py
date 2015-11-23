# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, datetime

from six import iteritems, itervalues

from flask.ext.restful import fields as base_fields
from werkzeug import cached_property

from .utils import camel_to_dash, not_none


class BaseField(object):
    __schema_type__ = 'string'
    __schema_format__ = None
    __schema_example__ = None

    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('description', None)
        self.title = kwargs.pop('title', None)
        self.required = kwargs.pop('required', None)
        self.readonly = kwargs.pop('readonly', None)
        self.example = kwargs.pop('example', self.__schema_example__)
        super(BaseField, self).__init__(*args, **kwargs)

    @cached_property
    def __schema__(self):
        return not_none(self.schema())

    def schema(self):
        return {
            'type': self.__schema_type__,
            'format': self.__schema_format__,
            'title': self.title,
            'description': self.description,
            'readOnly': self.readonly,
            'default': self.default,
            'example': self.example,
        }


class StringMixin(object):
    def __init__(self, *args, **kwargs):
        self.min_length = kwargs.pop('min_length', None)
        self.max_length = kwargs.pop('max_length', None)
        self.pattern = kwargs.pop('pattern', None)
        super(StringMixin, self).__init__(*args, **kwargs)

    def schema(self):
        schema = super(StringMixin, self).schema()
        schema.update(minLength=self.min_length, maxLength=self.max_length, pattern=self.pattern)
        return schema


class MinMaxMixin(object):
    def __init__(self, *args, **kwargs):
        self.minimum = kwargs.pop('min', None)
        self.excluisveMinimum = kwargs.pop('exclusiveMin', None)
        self.maximum = kwargs.pop('max', None)
        self.exclusiveMaximum = kwargs.pop('exclusiveMax', None)
        super(MinMaxMixin, self).__init__(*args, **kwargs)

    def schema(self):
        schema = super(MinMaxMixin, self).schema()
        schema.update(minimum=self.minimum, exclusiveMinimum=self.excluisveMinimum,
                      maximum=self.maximum, exclusiveMaximum=self.exclusiveMaximum)
        return schema


class NumberMixin(MinMaxMixin):
    def __init__(self, *args, **kwargs):
        self.multiple = kwargs.pop('multiple', None)
        super(NumberMixin, self).__init__(*args, **kwargs)

    def schema(self):
        schema = super(NumberMixin, self).schema()
        schema.update(multipleOf=self.multiple)
        return schema


class String(StringMixin, BaseField, base_fields.String):
    def __init__(self, *args, **kwargs):
        self.enum = kwargs.pop('enum', None)
        self.discriminator = kwargs.pop('discriminator', None)
        super(String, self).__init__(*args, **kwargs)
        self.required = self.discriminator or self.required

    def schema(self):
        enum = self.enum() if callable(self.enum) else self.enum
        schema = super(String, self).schema()
        schema.update(enum=enum)
        if enum and schema['example'] is None:
            schema['example'] = enum[0]
        return schema


class Integer(NumberMixin, BaseField, base_fields.Integer):
    __schema_type__ = 'integer'

    def __init__(self, default=None, **kwargs):
        super(Integer, self).__init__(default=default, **kwargs)


class Float(NumberMixin, BaseField, base_fields.Float):
    __schema_type__ = 'number'


class Arbitrary(NumberMixin, BaseField, base_fields.Arbitrary):
    __schema_type__ = 'number'


class Boolean(BaseField, base_fields.Boolean):
    __schema_type__ = 'boolean'


class DateTime(MinMaxMixin, BaseField, base_fields.DateTime):
    __schema_format__ = 'date-time'

    def __init__(self, *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)
        if self.minimum and isinstance(self.minimum, (date, datetime)):
            self.minimum = self.minimum.isoformat()
        if self.maximum and isinstance(self.maximum, (date, datetime)):
            self.maximum = self.maximum.isoformat()


class Raw(BaseField, base_fields.Raw):
    __schema_type__ = 'object'


class Nested(BaseField, base_fields.Nested):
    __schema_type__ = None

    def __init__(self, model, as_list=False, **kwargs):
        self.model = model
        self.as_list = as_list
        super(Nested, self).__init__(getattr(model, 'resolved', model), **kwargs)

    def schema(self):
        schema = super(Nested, self).schema()
        ref = '#/definitions/{0}'.format(self.nested.name)

        if self.as_list:
            schema['type'] = 'array'
            schema['items'] = {'$ref': ref}
        else:
            schema['$ref'] = ref
            # if not self.allow_null and not self.readonly:
            #     schema['required'] = True

        return schema


class List(BaseField, base_fields.List):
    def __init__(self, *args, **kwargs):
        self.min_items = kwargs.pop('min_items', None)
        self.max_items = kwargs.pop('max_items', None)
        self.unique = kwargs.pop('unique', None)
        super(List, self).__init__(*args, **kwargs)

    def schema(self):
        schema = super(List, self).schema()
        schema.update(minItems=self.min_items, maxItems=self.max_items, uniqueItems=self.unique)
        schema['type'] = 'array'
        schema['items'] = self.container.__schema__
        return schema


class Url(StringMixin, BaseField, base_fields.Url):
    pass


class Fixed(NumberMixin, BaseField, base_fields.Fixed):
    __schema_type__ = 'number'


class FormattedString(StringMixin, BaseField, base_fields.FormattedString):
    pass


class ClassName(String):
    def __init__(self, dash=False, **kwargs):
        super(ClassName, self).__init__(**kwargs)
        self.dash = dash

    def output(self, key, obj):
        classname = obj.__class__.__name__
        return camel_to_dash(classname) if self.dash else classname


class Polymorph(Nested):
    def __init__(self, mapping, required=False, **kwargs):
        self.mapping = mapping
        parent = self.resolve_ancestor(list(itervalues(mapping)))
        super(Polymorph, self).__init__(parent, allow_null=not required, **kwargs)

    def output(self, key, obj):
        # Copied from upstream NestedField
        value = base_fields.get_value(key if self.attribute is None else self.attribute, obj)
        if value is None:
            if self.allow_null:
                return None
            elif self.default is not None:
                return self.default

        # Handle mappings
        if not hasattr(value, '__class__'):
            raise ValueError('Polymorph field only accept class instances')

        candidates = [fields for cls, fields in iteritems(self.mapping) if isinstance(value, cls)]

        if len(candidates) <= 0:
            raise ValueError('Unknown class: ' + value.__class__.__name__)
        elif len(candidates) > 1:
            raise ValueError('Unable to determine a candidate for: ' + value.__class__.__name__)
        else:
            return base_fields.marshal(value, candidates[0].resolved)

    def resolve_ancestor(self, fields):
        '''
        Resolve the common ancestor for all fields.

        Assume there is only one common ancestor.
        '''
        trees = [set(f.tree) for f in fields]
        candidates = set.intersection(*trees)
        if len(candidates) != 1:
            field_names = [f.name for f in fields]
            raise ValueError('Unable to determine the common ancestor for: ' + ', '.join(field_names))

        parent_name = candidates.pop()
        return fields[0].get_parent(parent_name)
