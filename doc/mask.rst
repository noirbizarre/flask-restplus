Fields masks
============

Flask-Restplus support partial object fetching (aka. fields mask)
by suppling a custom header in the request.

By default the header is ``X-Fields``
but it ca be changed with the ``RESTPLUS_MASK_HEADER`` parameter.

Syntax
------

The syntax is actually quite simple.
You just provide a coma separated list of field names,
optionaly wrapped in brackets.

.. code-block:: python

    # These two mask are equivalents
    mask = '{name,age}'
    # or
    mask = 'name,age'
    data = requests.get('/some/url/', headers={'X-Fields': mask})
    assert len(data) == 2
    assert 'name' in data
    assert 'age' in data

To specify a nested fields mask,
simply provide it in bracket following the field name:

.. code-block:: python

    mask = '{name, age, pet{name}}'

Nesting specification works with nested object or list of objects:

.. code-block:: python

    # Will apply the mask {name} to each pet
    # in the pets list.
    mask = '{name, age, pets{name}}'
