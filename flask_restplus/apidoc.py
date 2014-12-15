# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for, Blueprint, render_template

apidoc = Blueprint('apidoc', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/swaggerui',
)


@apidoc.add_app_template_global
def swagger_static(filename):
    return url_for('apidoc.static', filename='bower/swagger-ui/dist/{0}'.format(filename))


def ui_for(api):
    '''Render a SwaggerUI for a given API'''
    return render_template('swagger-ui.html', specs_url=api.specs_url)


def init_app(app):
    app.register_blueprint(apidoc)
