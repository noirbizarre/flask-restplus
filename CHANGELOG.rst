Changelog
=========

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
