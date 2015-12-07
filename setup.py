#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import unicode_literals

import re
import sys

from setuptools import setup, find_packages

RE_REQUIREMENT = re.compile(r'^\s*-r\s*(?P<filename>.*)$')

PYPI_RST_FILTERS = (
    # Replace code-blocks
    (r'\.\.\s? code-block::\s*(\w|\+)+', '::'),
    # Remove all badges
    (r'\.\. image:: .*', ''),
    (r'\s+:target: .*', ''),
    (r'\s+:alt: .*', ''),
    # Replace Python crossreferences by simple monospace
    (r':(?:class|func|meth|mod|attr|obj|exc|data|const):`~(?:\w+\.)*(\w+)`', r'``\1``'),
    (r':(?:class|func|meth|mod|attr|obj|exc|data|const):`(.+)`', r'``\1``'),
    # replace doc references
    (r':doc:`(.+) <(.*)>`', r'`\1 <http://flask-restplus.readthedocs.org/en/stable\2.html>`_'),
)


def rst(filename):
    '''
    Load rst file and sanitize it for PyPI.
    Remove unsupported github tags:
     - code-block directive
     - all badges
    '''
    content = open(filename).read()
    for regex, replacement in PYPI_RST_FILTERS:
        content = re.sub(regex, replacement, content)
    return content


long_description = '\n'.join((
    rst('README.rst'),
    rst('CHANGELOG.rst'),
    ''
))


exec(compile(open('flask_restplus/__about__.py').read(), 'flask_restplus/__about__.py', 'exec'))

tests_require = ['nose', 'rednose', 'blinker']
install_requires = ['flask-restful >= 0.3.2', 'jsonschema', 'pytz', 'aniso8601>=0.82']
dev_requires = ['flake8', 'sphinx', 'minibench', 'tox', 'invoke']


if sys.version_info[0:2] < (2, 7):
    install_requires += ['ordereddict']
    tests_require += ['unittest2']

try:
    from unittest.mock import Mock
except:
    tests_require += ['mock']

setup(
    name='flask-restplus',
    version=__version__,
    description=__description__,
    long_description=long_description,
    url='https://github.com/noirbizarre/flask-restplus',
    author='Axel Haustant',
    author_email='axel@data.gouv.fr',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev': dev_requires,
    },
    license='MIT',
    use_2to3=True,
    zip_safe=False,
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: System :: Software Distribution',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
    ],
)
