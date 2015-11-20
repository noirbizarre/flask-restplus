# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from invoke import run, task

from os.path import join, abspath, dirname

ROOT = abspath(join(dirname(__file__)))


@task
def clean(docs=False, bytecode=False, extra=''):
    '''Cleanup all build artifacts'''
    patterns = ['build', 'dist', 'cover', 'docs/_build', '**/*.pyc', '*.egg-info', '.tox']
    for pattern in patterns:
        print('Removing {0}'.format(pattern))
        run('cd {0} && rm -rf {1}'.format(ROOT, pattern))


@task
def demo():
    '''Run the demo'''
    run('python {0}/examples/todo.py'.format(ROOT))


@task
def test():
    '''Run tests suite'''
    run('cd {0} && nosetests --rednose --force-color'.format(ROOT), pty=True)


@task
def cover():
    '''Run tests suite with coverage'''
    run('cd {0} && nosetests --rednose --force-color \
        --with-coverage --cover-html --cover-package=flask_restplus'.format(ROOT), pty=True)


@task
def tox():
    '''Run tests against Python versions'''
    run('tox', pty=True)


@task
def qa():
    '''Run a quality report'''
    run('flake8 {0}/flask_restplus'.format(ROOT))


@task
def doc():
    '''Build the documentation'''
    run('cd {0}/doc && make html'.format(ROOT), pty=True)


@task
def dist():
    '''Package for distribution'''
    run('cd {0} && python setup.py sdist bdist_wheel'.format(ROOT), pty=True)


@task(tox, doc, qa, dist, default=True)
def all():
    '''Run tests, reports and packaging'''
    pass
