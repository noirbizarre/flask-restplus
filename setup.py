#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from setuptools import setup, find_packages

RE_REQUIREMENT = re.compile(r'^\s*-r\s*(?P<filename>.*)$')

PYPI_RST_FILTERS = (
    # Replace code-blocks
    (r'\.\.\s? code-block::\s*(\w|\+)+',  '::'),
    # Remove all badges
    (r'\.\. image:: .*', ''),
    (r'    :target: .*', ''),
    (r'    :alt: .*', ''),
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

tests_require = ['nose', 'rednose']

setup(
    name='flask-restplus',
    version=__import__('flask_restplus').__version__,
    description=__import__('flask_restplus').__description__,
    long_description=long_description,
    url='https://github.com/noirbizarre/flask-restplus',
    download_url='http://pypi.python.org/pypi/flask-restplus',
    author='Axel Haustant',
    author_email='axel@data.gouv.fr',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['flask-restful'],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
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
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
    ],
)
