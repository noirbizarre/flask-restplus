Changelog
=========

.. currentmodule:: flask_restplus

Current
-------

- Nothing yet

0.11.0 (2018-05-16)
-------------------

- Add authorizations parsing to namespace (:issue:`403`)
- Add vendor extensions support (:issue:`97`)
- :class:`~reqparse.RequestParser` arguments now support the ``split`` action
- Ensure default boolean value as `False` works with :class:`~reqparse.RequestParser` (:issue:`199`)
- Schema errors are not longuer hidden by `AttributeError: Api does not have __schema__ attribute` (:issue:`194`)
- Add a new :class:`~inputs.URL` validator, more flexible and precise.
- Fix error bundling (:issue:`175`, :issue:`144`)
- Help message is now added to source error message instead of string interpolation (:issue:`147`)
- Use pytest instead of nosetests
- Upgrade to Swagger-UI 3.4.0
- Fix typo in comments
- Add an optional key argument, ``skip_none``, in :func:`marshal_with` and :func:`marshal`
- Fix masks not working correctly with Python 2.7 (:issue:`217`)
- Fixed typos in doc/scaling
- Add docs for `allow_null` and :class:`~fields.Nested`
- Add Namespace.payload
- **Breaking**: everything is unordered by default because ordering has a serious impact on performances:
    - :class:`Api` and :class:`Namespace` now accept an optionnal ``ordered`` parameter
    - :func:`marshal_with` and :func:`marshal` now accept an optionnal ``ordered`` parameter

Breaking changes
~~~~~~~~~~~~~~~~

- Drop python 2.6 support
- Improve header handling (:issue:`119`):
    - `@api.header` only document response headers on all responses
    - `@api.response` accept an optionnal `headers` argument to document response specific headers
    - request header are handled by the `@api.expect` decorator

0.10.1 (2017-03-04)
-------------------

- Fix a typo in ``__init__`` breaking ``from flask_restplus import *`` (:issue:`242`)
- Basic support for custom URL converters (:issue:`243`)
- Support custom response classes inheriting from :class:`~werkzeug.wrappers.BaseResponse` (:issue:`245`)
- Allow models to preserve order (:issue:`135`)

0.10.0 (2017-02-12)
-------------------

- Allows to specify a custom mount path on namespace registration
- Allow to express models as raw schemas
- Upgraded to Swagger-UI 2.2.6
- Support Swagger-UI translations
- Fix prefix trailing slash stripping in Postman doc generation (:issue:`232`)
- Add validation for lists in the expect decorator (:issue:`231`)

0.9.2 (2016-04-22)
------------------

- Same version but a PyPI bug force reupload.

0.9.1 (2016-04-22)
------------------

- Added some Swagger-UI Oauth configurations:
    - `SWAGGER_UI_OAUTH_CLIENT_ID`
    - `SWAGGER_UI_OAUTH_REALM`
    - `SWAGGER_UI_OAUTH_APP_NAME`
- Expose ``type: object`` in Swagger schemas (:issue:`157`)
- Fix an issue with error handlers (:issue:`141`)
- Fix an issue with Postman export when using OAuth (:issue:`151`)
- Miscellenaous code and documentation fixes
- Remove last flask-restful references (unless needed) and add missing attributions

0.9.0 (2016-02-22)
------------------

- Make :class:`Namespace` behave like :class:`~flask.Blueprint` for :class:`~flask.Flask`
- Deprecated ``parser`` and ``body`` parameters for ``expect`` in :meth:`~Namespace.doc` decorator
- Deprecated :meth:`Model.extend` in favor of :meth:`Model.clone`
- Added the :meth:`~Namespace.param` decorator
- Honour method restrictions in Swagger documentation (:issue:`93`)
- Improved documentation

0.8.6 (2015-12-26)
------------------

- Handle callable on API infos
- Handle documentation on error handlers
- Drop/merge flask_restful ``flask_restful.RequestParser``
- Handle :class:`~reqparse.RequestParser` into :meth:`~Api.expect` decorator
- Handle schema for :mod:`~inputs` parsers
- Added some inputs:
    - :class:`~inputs.email`
    - :func:`~inputs.ip`
    - :func:`~inputs.ipv4`
    - :func:`~inputs.ipv6`


0.8.5 (2015-12-12)
------------------

- Handle mask on :class:`~fields.Polymorph` field
- Handle mask on inherited models
- Replace `flask_restful.abort` by :func:`flask_restplus.errors.abort`
- Replace `flask_restful.unpack` by :func:`flask_restplus.utils.unpack`
- **Breaking changes**:
    - Renamed ``ApiModel`` into :class:`Model`
    - Renamed ``ApiNamespace`` into :class:`Namespace`


0.8.4 (2015-12-07)
------------------

- Drop/merge `flask_restful.Resource` resolving a recursion problem
- Allow any `callable` as field `default`, `min`, `max`...
- Added :class:`~fields.Date` field
- Improve error handling for inconsistent masks
- Handle model level default mask
- support colons and dashes in mask field names
- **Breaking changes**:
   - Renamed `exceptions` module into `errors`
   - Renamed `RestException` into :class:`~errors.RestError`
   - Renamed `MarshallingException` into :class:`~fields.MarshallingError`
   - :class:`~fields.DateTime` field always output datetime

0.8.3 (2015-12-05)
------------------

- Drop/merge flask-restful fields
- Drop/merge flask-restplus inputs
- Update Swagger-UI to version 2.1.3
- Use minified version of Swagger-UI if ``DEBUG=False``
- Blueprint subdomain support (static only)
- Added support for default fields mask

0.8.2 (2015-12-01)
------------------

- Skip unknown fields in mask when applied on a model
- Added `*` token to fields mask (all remaining fields)
- Ensure generated endpoints does not collide
- Drop/merge flask-restful `Api.handler_error()`

0.8.1 (2015-11-27)
------------------

- Refactor Swagger UI handling:
    - allow to register a custom view with ``@api.documentation``
    - allow to register a custom URL with the ``doc`` parameter
    - allow to disable documentation with ``doc=False``
- Added fields mask support through header (see: :doc:`Fields Masks Documentation </mask>`)
- Expose ``flask_restful.inputs`` module on ``flask_restplus.inputs``
- Added support for some missing fields and attributes:
    - ``host`` root field (filed only if ``SERVER_NAME`` config is set)
    - custom ``tags`` root field
    - ``exclusiveMinimum`` and ``exclusiveMaximum`` number field attributes
    - ``multipleOf`` number field attribute
    - ``minLength`` and ``maxLength`` string field attributes
    - ``pattern`` string field attribute
    - ``minItems`` and ``maxItems`` list field attributes
    - ``uniqueItems`` list field attribute
- Allow to override the default error handler
- Fixes


0.8.0
-----

- Added payload validation (initial implementation based on jsonschema)
- Added ``@api.deprecated`` to mark resources or methods as deprecated
- Added ``@api.header`` decorator shortcut to document headers
- Added Postman export
- Fix compatibility with flask-restful 0.3.4
- Allow to specify an exemple a custom fields with ``__schema_example__``
- Added support for ``PATCH`` method in Swagger UI
- Upgraded to Swagger UI 2.1.2
- Handle enum as callable
- Allow to configure ``docExpansion`` with the ``SWAGGER_UI_DOC_EXPANSION`` parameter


0.7.2
-----

- Compatibility with flask-restful 0.3.3
- Fix action=append handling in RequestParser
- Upgraded to SwaggerUI 2.1.8-M1
- Miscellaneous fixes


0.7.1
-----

- Fix ``@api.marshal_with_list()`` keyword arguments handling.


0.7.0
-----

- Expose models and fields schema through the ``__schema__`` attribute
- Drop support for model as class
- Added ``@api.errorhandler()`` to register custom error handlers
- Added ``@api.response()`` shortcut decorator
- Fix list nested models missing in definitions


0.6.0
-----

- Python 2.6 support
- Experimental polymorphism support (single inheritance only)
    - Added ``Polymorph`` field
    - Added ``discriminator`` attribute support on ``String`` fields
    - Added ``api.inherit()`` method
- Added ``ClassName`` field

0.5.1
-----

- Fix for parameter with schema (do not set type=string)


0.5.0
-----

- Allow shorter syntax to set operation id: ``@api.doc('my-operation')``
- Added a shortcut to specify the expected input model: ``@api.expect(my_fields)``
- Added ``title`` attribute to fields
- Added ``@api.extend()`` to extend models
- Ensure coherence between ``required`` and ``allow_null`` for ``NestedField``
- Support list of primitive types and list of models as body
- Upgraded to latest version of Swagger UI
- Fixes


0.4.2
-----

- Rename apidoc blueprint into restplus_doc to avoid collisions


0.4.1
-----

- Added ``SWAGGER_VALIDATOR_URL`` config parameter
- Added ``readonly`` field parameter
- Upgraded to latest version of Swagger UI


0.4.0
-----

- Port to Flask-Restful 0.3+
- Use the default Blueprint/App mecanism
- Allow to hide some ressources or methods using ``@api.doc(False)`` or ``@api.hide``
- Allow to globally customize the default operationId with the ``default_id`` callable parameter

0.3.0
-----

- Switch to Swagger 2.0 (Major breakage)
    - ``notes`` documentation is now ``description``
    - ``nickname`` documentation is now ``id``
    - new responses declaration format
- Added missing ``body`` parameter to document ``body`` input
- Last release before Flask-Restful 0.3+ compatibility switch


0.2.4
-----

- Handle ``description`` and ``required`` attributes on ``fields.List``

0.2.3
-----

- Fix custom fields registeration

0.2.2
-----

- Fix model list in declaration

0.2.1
-----

- Allow to type custom fields with ``Api.model``
- Handle custom fields into ``fieds.List``

0.2
---

- Upgraded to SwaggerUI 0.2.22
- Support additional field documentation attributes: ``required``, ``description``, ``enum``, ``min``, ``max`` and ``default``
- Initial support for model in RequestParser

0.1.3
-----

- Fix ``Api.marshal()`` shortcut

0.1.2
-----

- Added ``Api.marshal_with()`` and ``Api.marshal_list_with()`` decorators
- Added ``Api.marshal()`` shortcut


0.1.1
-----

- Use ``zip_safe=False`` for proper packaging.


0.1
---

- Initial release
