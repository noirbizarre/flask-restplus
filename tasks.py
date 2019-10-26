# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import sys

from datetime import datetime

from invoke import task

ROOT = os.path.dirname(__file__)

CLEAN_PATTERNS = [
    'build',
    'dist',
    'cover',
    'docs/_build',
    '**/*.pyc',
    '.tox',
    '**/__pycache__',
    'reports',
    '*.egg-info',
]


def color(code):
    '''A simple ANSI color wrapper factory'''
    return lambda t: '\033[{0}{1}\033[0;m'.format(code, t)


green = color('1;32m')
red = color('1;31m')
blue = color('1;30m')
cyan = color('1;36m')
purple = color('1;35m')
white = color('1;39m')


def header(text):
    '''Display an header'''
    print(' '.join((blue('>>'), cyan(text))))
    sys.stdout.flush()


def info(text, *args, **kwargs):
    '''Display informations'''
    text = text.format(*args, **kwargs)
    print(' '.join((purple('>>>'), text)))
    sys.stdout.flush()


def success(text):
    '''Display a success message'''
    print(' '.join((green('>>'), white(text))))
    sys.stdout.flush()


def error(text):
    '''Display an error message'''
    print(red('✘ {0}'.format(text)))
    sys.stdout.flush()


def exit(text=None, code=-1):
    if text:
        error(text)
    sys.exit(-1)


def build_args(*args):
    return ' '.join(a for a in args if a)


@task
def clean(ctx):
    '''Cleanup all build artifacts'''
    header(clean.__doc__)
    with ctx.cd(ROOT):
        for pattern in CLEAN_PATTERNS:
            info('Removing {0}', pattern)
            ctx.run('rm -rf {0}'.format(pattern))


@task
def deps(ctx):
    '''Install or update development dependencies'''
    header(deps.__doc__)
    with ctx.cd(ROOT):
        ctx.run('pip install -r requirements/develop.pip -r requirements/doc.pip', pty=True)


@task
def demo(ctx):
    '''Run the demo'''
    header(demo.__doc__)
    with ctx.cd(ROOT):
        ctx.run('python examples/todo.py')


@task
def test(ctx, profile=False):
    '''Run tests suite'''
    header(test.__doc__)
    kwargs = build_args(
        '--benchmark-skip',
        '--profile' if profile else None,
    )
    with ctx.cd(ROOT):
        ctx.run('pytest {0}'.format(kwargs), pty=True)


@task
def benchmark(ctx, max_time=2, save=False, compare=False, histogram=False, profile=False, tox=False):
    '''Run benchmarks'''
    header(benchmark.__doc__)
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
        envs = ctx.run('tox -l', hide=True).stdout.splitlines()
        envs = ','.join(e for e in envs if e != 'doc')
        cmd = 'tox -e {envs} -- {cmd}'.format(envs=envs, cmd=cmd)
    ctx.run(cmd, pty=True)


@task
def cover(ctx, html=False):
    '''Run tests suite with coverage'''
    header(cover.__doc__)
    extra = '--cov-report html' if html else ''
    with ctx.cd(ROOT):
        ctx.run('pytest --benchmark-skip --cov flask_restplus --cov-report term {0}'.format(extra), pty=True)


@task
def tox(ctx):
    '''Run tests against Python versions'''
    header(tox.__doc__)
    ctx.run('tox', pty=True)


@task
def qa(ctx):
    '''Run a quality report'''
    header(qa.__doc__)
    with ctx.cd(ROOT):
        info('Python Static Analysis')
        flake8_results = ctx.run('flake8 flask_restplus tests', pty=True, warn=True)
        if flake8_results.failed:
            error('There is some lints to fix')
        else:
            success('No linter errors')
        info('Ensure PyPI can render README and CHANGELOG')
        readme_results = ctx.run('python setup.py check -r -s', pty=True, warn=True, hide=True)
        if readme_results.failed:
            print(readme_results.stdout)
            error('README and/or CHANGELOG is not renderable by PyPI')
        else:
            success('README and CHANGELOG are renderable by PyPI')
    if flake8_results.failed or readme_results.failed:
        exit('Quality check failed', flake8_results.return_code or readme_results.return_code)
    success('Quality check OK')


@task
def doc(ctx):
    '''Build the documentation'''
    header(doc.__doc__)
    with ctx.cd(os.path.join(ROOT, 'doc')):
        ctx.run('make html', pty=True)


@task
def assets(ctx):
    '''Fetch web assets'''
    header(assets.__doc__)
    with ctx.cd(ROOT):
        ctx.run('npm install')
        ctx.run('mkdir -p flask_restplus/static')
        ctx.run('cp node_modules/swagger-ui-dist/{swagger-ui*.{css,js}{,.map},favicon*.png,oauth2-redirect.html} flask_restplus/static')
        # Until next release we need to install droid sans separately
        ctx.run('cp node_modules/typeface-droid-sans/index.css flask_restplus/static/droid-sans.css')
        ctx.run('cp -R node_modules/typeface-droid-sans/files flask_restplus/static/')


@task
def dist(ctx):
    '''Package for distribution'''
    header(dist.__doc__)
    with ctx.cd(ROOT):
        ctx.run('python setup.py bdist_wheel', pty=True)


@task(clean, deps, test, doc, qa, assets, dist, default=True)
def all(ctx):
    '''Run tests, reports and packaging'''
    pass
