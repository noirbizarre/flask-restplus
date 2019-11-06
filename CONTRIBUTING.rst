Contributing
============

flask-restplus is open-source and very open to contributions. 

If you're part of a corporation with an NDA, and you may require updating the license. 
See Updating Copyright below

Submitting issues
-----------------

Issues are contributions in a way so don't hesitate
to submit reports on the `official bugtracker`_.

Provide as much informations as possible to specify the issues:

- the flask-restplus version used
- a stacktrace
- installed applications list
- a code sample to reproduce the issue
- ...


Submitting patches (bugfix, features, ...)
------------------------------------------

If you want to contribute some code:

1. fork the `official flask-restplus repository`_
2. Ensure an issue is opened for your feature or bug
3. create a branch with an explicit name (like ``my-new-feature`` or ``issue-XX``)
4. do your work in it
5. Commit your changes. Ensure the commit message includes the issue. Also, if contributing from a corporation, be sure to add a comment with the Copyright information
6. rebase it on the master branch from the official repository (cleanup your history by performing an interactive rebase)
7. add your change to the changelog
8. submit your pull-request
9. 2 Maintainers should review the code for bugfix and features. 1 maintainer for minor changes (such as docs)
10. After review, a maintainer a will merge the PR. Maintainers should not merge their own PRs 

There are some rules to follow:

- your contribution should be documented (if needed)
- your contribution should be tested and the test suite should pass successfully
- your code should be mostly PEP8 compatible with a 120 characters line length
- your contribution should support both Python 2 and 3 (use ``tox`` to test)

You need to install some dependencies to develop on flask-restplus:

.. code-block:: console

    $ pip install -e .[dev]

An Invoke ``tasks.py`` is provided to simplify the common tasks:

.. code-block:: console

    $ inv -l
    Available tasks:

      all      Run tests, reports and packaging
      assets   Fetch web assets -- Swagger. Requires NPM (see below)
      clean    Cleanup all build artifacts
      cover    Run tests suite with coverage
      demo     Run the demo
      dist     Package for distribution
      doc      Build the documentation
      qa       Run a quality report
      test     Run tests suite
      tox      Run tests against Python versions

To ensure everything is fine before submission, use ``tox``.
It will run the test suite on all the supported Python version
and ensure the documentation is generating.

.. code-block:: console

    $ tox

You also need to ensure your code is compliant with the flask-restplus coding standards:

.. code-block:: console

    $ inv qa

To ensure everything is fine before commiting, you can launch the all in one command:

.. code-block:: console

    $ inv qa tox

It will ensure the code meet the coding conventions, runs on every version on python
and the documentation is properly generating.

.. _official flask-restplus repository: https://github.com/noirbizarre/flask-restplus
.. _official bugtracker: https://github.com/noirbizarre/flask-restplus/issues

Running a local Swagger Server
------------------------------

For local development, you may wish to run a local server. running the following will install a swagger server

.. code-block:: console

    $ inv assets

NOTE: You'll need `NPM <https://docs.npmjs.com/getting-started/>`_ installed to do this. 
If you're new to NPM, also check out `nvm <https://github.com/creationix/nvm/blob/master/README.md>`_


Updating Copyright
------------------

If you're a part of a corporation with an NDA, you may be required to update the LICENSE.

1. Check with your legal department first.
2. Add an appropriate line to the LICENSE file. See the Akamai entry for an example
3. When making a commit, add the specific copyright notice.

Double check with your legal department about their regulations. Not all changes
constitute new or unique work.
