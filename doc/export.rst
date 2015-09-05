Exporting
=========

Flask-restplus provide facilities to export your API.

Export as Swagger specifications
--------------------------------

You can export the Swagger specififcations corresponding to your API.

.. code-block:: python

    from flask import json

    from myapp import api

    print(json.dumps(api.__schema__))


Export as Postman collection
----------------------------

To help you testing, you can export your API as a `Postman`_ collection.

.. code-block:: python

    from flask import json

    from myapp import api

    urlvars = False  # Build query strings in URLs
    data = api.as_postman(urlvars=urlvars)
    print(json.dumps(data))


.. _Postman: https://www.getpostman.com/
