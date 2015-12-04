# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from invoke import run, task

from os.path import join, abspath, dirname

ROOT = abspath(join(dirname(__file__)))


def lrun(cmd, *args, **kwargs):
    '''Run a command ensuring cwd is project root'''
    return run('cd {0} && {1}'.format(ROOT, cmd), *args, **kwargs)


@task
def clean(docs=False, bytecode=False, extra=''):
    '''Cleanup all build artifacts'''
    patterns = ['build', 'dist', 'cover', 'docs/_build', '**/*.pyc', '*.egg-info', '.tox']
    for pattern in patterns:
        print('Removing {0}'.format(pattern))
        lrun('rm -rf {0}'.format(pattern))


@task
def demo():
    '''Run the demo'''
    lrun('python examples/todo.py')


@task
def test():
    '''Run tests suite'''
    lrun('nosetests --force-color', pty=True)


@task
def cover():
    '''Run tests suite with coverage'''
    lrun('nosetests --force-color --with-coverage --cover-html', pty=True)


@task
def tox():
    '''Run tests against Python versions'''
    run('tox', pty=True)


@task
def qa():
    '''Run a quality report'''
    lrun('flake8 flask_restplus')


@task
def doc():
    '''Build the documentation'''
    lrun('cd doc && make html', pty=True)


@task
def assets():
    '''Fetch web assets'''
    lrun('bower install')


@task
def dist():
    '''Package for distribution'''
    lrun('python setup.py sdist bdist_wheel', pty=True)


@task(tox, doc, qa, assets, dist, default=True)
def all():
    '''Run tests, reports and packaging'''
    pass
