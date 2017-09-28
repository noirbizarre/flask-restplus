# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from datetime import datetime

from invoke import run, task

from os.path import join, abspath, dirname

ROOT = abspath(join(dirname(__file__)))


def lrun(cmd, *args, **kwargs):
    '''Run a command ensuring cwd is project root'''
    return run('cd {0} && {1}'.format(ROOT, cmd), *args, **kwargs)


def build_args(*args):
    return ' '.join(a for a in args if a)


@task
def clean(ctx, docs=False, bytecode=False, extra=''):
    '''Cleanup all build artifacts'''
    patterns = ['build', 'dist', 'cover', 'docs/_build', '**/*.pyc', '*.egg-info', '.tox', '**/__pycache__']
    for pattern in patterns:
        print('Removing {0}'.format(pattern))
        lrun('rm -rf {0}'.format(pattern))


@task
def demo(ctx):
    '''Run the demo'''
    lrun('python examples/todo.py')


@task
def test(ctx, profile=False):
    '''Run tests suite'''
    kwargs = build_args(
        '--benchmark-skip',
        '--profile' if profile else None,
    )
    lrun('pytest {0}'.format(kwargs), pty=True)


@task
def benchmark(ctx, max_time=2, save=False, compare=False, histogram=False, profile=False, tox=False):
    '''Run benchmarks'''
    ts = datetime.now()
    kwargs = build_args(
        '--benchmark-max-time={0}'.format(max_time),
        '--benchmark-autosave' if save else None,
        '--benchmark-compare' if compare else None,
        '--benchmark-histogram=histograms/{0:%Y%m%d-%H%M%S}'.format(ts) if histogram else None,
        '--benchmark-cprofile=tottime' if profile else None,
    )
    cmd = 'pytest tests/benchmarks {0}'.format(kwargs)
    if tox:
        envs = lrun('tox -l', hide=True).stdout.splitlines()
        envs = ','.join(e for e in envs if e != 'doc')
        cmd = 'tox -e {envs} -- {cmd}'.format(envs=envs, cmd=cmd)
    lrun(cmd, pty=True)


@task
def cover(ctx, html=False):
    '''Run tests suite with coverage'''
    extra = '--cov-report html' if html else ''
    lrun('pytest --benchmark-skip --cov flask_restplus --cov-report term {0}'.format(extra), pty=True)


@task
def tox(ctx):
    '''Run tests against Python versions'''
    run('tox', pty=True)


@task
def qa(ctx):
    '''Run a quality report'''
    lrun('flake8 flask_restplus tests')


@task
def doc(ctx):
    '''Build the documentation'''
    lrun('cd doc && make html', pty=True)


@task
def assets(ctx):
    '''Fetch web assets'''
    lrun('bower install')


@task
def dist(ctx):
    '''Package for distribution'''
    lrun('python setup.py sdist bdist_wheel', pty=True)


@task(tox, doc, qa, assets, dist, default=True)
def all(ctx):
    '''Run tests, reports and packaging'''
    pass
