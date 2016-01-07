Postman
=======

To help you testing, you can export your API as a `Postman`_ collection.

.. code-block:: python

    from flask import json

    from myapp import api

    urlvars = False  # Build query strings in URLs
    swagger = True  # Export Swagger specifications
    data = api.as_postman(urlvars=urlvars, swagger=swagger)
    print(json.dumps(data))


.. _Postman: https://www.getpostman.com/
