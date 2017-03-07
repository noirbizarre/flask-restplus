.. _parsing:

Request Parsing
===============

.. warning ::

    The whole request parser part of Flask-RESTPlus is slated for removal and
    will be replaced by documentation on how to integrate with other packages
    that do the input/output stuff better
    (such as `marshmallow <http://marshmallow.readthedocs.org>`_).
    This means that it will be maintained until 2.0 but consider it deprecated.
    Don't worry, if you have code using that now and wish to continue doing so,
    it's not going to go away any time too soon.

.. currentmodule:: flask_restplus

Flask-RESTPlus's request parsing interface, :mod:`reqparse`,
is modeled after the :mod:`python:argparse` interface.
It's designed to provide simple and uniform access to any variable on the
:class:`flask.request` object in Flask.

Basic Arguments
---------------

Here's a simple example of the request parser.
It looks for two arguments in the :attr:`flask.Request.values` dict: an integer and a string

.. code-block:: python

    from flask_restplus import reqparse

    parser = reqparse.RequestParser()
    parser.add_argument('rate', type=int, help='Rate cannot be converted')
    parser.add_argument('name')
    args = parser.parse_args()

.. note ::

    The default argument type is a unicode string.
    This will be ``str`` in python3 and ``unicode`` in python2.

If you specify the ``help`` value,
it will be rendered as the error message when a type error is raised while parsing it.
If you do not specify a help message,
the default behavior is to return the message from the type error itself.
See :ref:`error-messages` for more details.


.. note ::
    By default, arguments are **not** required.
    Also, arguments supplied in the request that are not part of the :class:`~reqparse.RequestParser` will be ignored.

.. note ::
    Arguments declared in your request parser but not set in the request itself will default to ``None``.

Required Arguments
------------------

To require a value be passed for an argument,
just add ``required=True`` to the call to :meth:`~reqparse.RequestParser.add_argument`.

.. code-block:: python

    parser.add_argument('name', required=True, help="Name cannot be blank!")


Multiple Values & Lists
-----------------------

If you want to accept multiple values for a key as a list, you can pass ``action='append'``:

.. code-block:: python

    parser.add_argument('name', action='append')

This will let you make queries like ::

    curl http://api.example.com -d "name=bob" -d "name=sue" -d "name=joe"

And your args will look like this :

.. code-block:: python

    args = parser.parse_args()
    args['name']    # ['bob', 'sue', 'joe']

If you expect a coma separated list, use the ``action='split'``:

.. code-block:: python

    parser.add_argument('fruits', action='split')

This will let you make queries like ::

    curl http://api.example.com -d "fruits=apple,lemon,cherry"

And your args will look like this :

.. code-block:: python

    args = parser.parse_args()
    args['fruits']    # ['apple', 'lemon', 'cherry']

Other Destinations
------------------

If for some reason you'd like your argument stored under a different name once
it's parsed, you can use the ``dest`` keyword argument. ::

    parser.add_argument('name', dest='public_name')

    args = parser.parse_args()
    args['public_name']

Argument Locations
------------------

By default, the :class:`~reqparse.RequestParser` tries to parse values from
:attr:`flask.Request.values`, and :attr:`flask.Request.json`.

Use the ``location`` argument to :meth:`~reqparse.RequestParser.add_argument`
to specify alternate locations to pull the values from. Any variable on the
:class:`flask.Request` can be used. For example: ::

    # Look only in the POST body
    parser.add_argument('name', type=int, location='form')

    # Look only in the querystring
    parser.add_argument('PageSize', type=int, location='args')

    # From the request headers
    parser.add_argument('User-Agent', location='headers')

    # From http cookies
    parser.add_argument('session_id', location='cookies')

    # From file uploads
    parser.add_argument('picture', type=werkzeug.datastructures.FileStorage, location='files')

.. note ::

    Only use ``type=list`` when ``location='json'``. `See this issue for more
    details <https://github.com/flask-restful/flask-restful/issues/380>`_

.. note ::

    Using ``location='form'`` is way to both validate form data and document you form fields.


Multiple Locations
------------------

Multiple argument locations can be specified by passing a list to ``location``::

    parser.add_argument('text', location=['headers', 'values'])


When multiple locations are specified, the arguments from all locations
specified are combined into a single :class:`~werkzeug.datastructures.MultiDict`.
The last ``location`` listed takes precedence in the result set.

If the argument location list includes the :attr:`~flask.Request.headers`
location the argument names will no longer be case insensitive and must match
their title case names (see :meth:`str.title`). Specifying
``location='headers'`` (not as a list) will retain case insensitivity.

Advanced types handling
-----------------------

Sometimes, you need more than a primitive type to handle input validation.
The :mod:`~flask_restplus.inputs` module provides some common type handling like:

- :func:`~inputs.boolean` for wider boolean handling
- :func:`~inputs.ipv4` and :func:`~inputs.ipv6` for IP adresses
- :func:`~inputs.date_from_iso8601` and :func:`~inputs.datetime_from_iso8601` for ISO8601 date and dateime handling

You just have to use them as `type` argument:

.. code-block:: python

    parser.add_argument('flag', type=inputs.boolean)

See the :mod:`~flask_restplus.inputs` documentation for full list of available inputs.

You can also write your own:

.. code-block:: python

    def my_type(value):
        '''Parse my type'''
        if not condition:
            raise ValueError('This is not my type')
        return parse(value)

    # Swagger documntation
    my_type.__schema__ = {'type': 'string', 'format': 'my-custom-format'}


Parser Inheritance
------------------

Often you will make a different parser for each resource you write. The problem
with this is if parsers have arguments in common. Instead of rewriting
arguments you can write a parent parser containing all the shared arguments and
then extend the parser with :meth:`~reqparse.RequestParser.copy`. You can
also overwrite any argument in the parent with
:meth:`~reqparse.RequestParser.replace_argument`, or remove it completely
with :meth:`~reqparse.RequestParser.remove_argument`. For example: ::

    from flask_restplus import reqparse

    parser = reqparse.RequestParser()
    parser.add_argument('foo', type=int)

    parser_copy = parser.copy()
    parser_copy.add_argument('bar', type=int)

    # parser_copy has both 'foo' and 'bar'

    parser_copy.replace_argument('foo', required=True, location='json')
    # 'foo' is now a required str located in json, not an int as defined
    #  by original parser

    parser_copy.remove_argument('foo')
    # parser_copy no longer has 'foo' argument

File Upload
-----------

To handle file upload with the :class:`~reqparse.RequestParser`,
you need to use the `files` location
and to set the type to :class:`~werkzeug.datastructures.FileStorage`.

.. code-block:: python

    from werkzeug.datastructures import FileStorage

    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files',
                               type=FileStorage, required=True)


    @api.route('/upload/')
    @api.expect(upload_parser)
    class Upload(Resource):
        def post(self):
            uploaded_file = args['file']  # This is FileStorage instance
            url = do_something_with_file(uploaded_file)
            return {'url': url}, 201

See the `dedicated Flask documentation section <http://flask.pocoo.org/docs/0.10/patterns/fileuploads/>`_.


Error Handling
--------------

The default way errors are handled by the RequestParser is to abort on the
first error that occurred. This can be beneficial when you have arguments that
might take some time to process. However, often it is nice to have the errors
bundled together and sent back to the client all at once. This behavior can be
specified either at the Flask application level or on the specific
RequestParser instance. To invoke a RequestParser with the bundling errors
option, pass in the argument ``bundle_errors``. For example ::

    from flask_restplus import reqparse

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('foo', type=int, required=True)
    parser.add_argument('bar', type=int, required=True)

    # If a request comes in not containing both 'foo' and 'bar', the error that
    # will come back will look something like this.

    {
        "message":  {
            "foo": "foo error message",
            "bar": "bar error message"
        }
    }

    # The default behavior would only return the first error

    parser = RequestParser()
    parser.add_argument('foo', type=int, required=True)
    parser.add_argument('bar', type=int, required=True)

    {
        "message":  {
            "foo": "foo error message"
        }
    }

The application configuration key is "BUNDLE_ERRORS". For example ::

    from flask import Flask

    app = Flask(__name__)
    app.config['BUNDLE_ERRORS'] = True

.. warning ::

    ``BUNDLE_ERRORS`` is a global setting that overrides the ``bundle_errors``
    option in individual :class:`~reqparse.RequestParser` instances.


.. _error-messages:

Error Messages
--------------

Error messages for each field may be customized using the ``help`` parameter
to ``Argument`` (and also ``RequestParser.add_argument``).

If no help parameter is provided, the error message for the field will be
the string representation of the type error itself. If ``help`` is provided,
then the error message will be the value of ``help``.

``help`` may include an interpolation token, ``{error_msg}``, that will be
replaced with the string representation of the type error. This allows the
message to be customized while preserving the original error::

    from flask_restplus import reqparse


    parser = reqparse.RequestParser()
    parser.add_argument(
        'foo',
        choices=('one', 'two'),
        help='Bad choice: {error_msg}'
    )

    # If a request comes in with a value of "three" for `foo`:

    {
        "message":  {
            "foo": "Bad choice: three is not a valid choice",
        }
    }
