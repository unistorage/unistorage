import functools

from flask import g, request, redirect, url_for, render_template, flash, session, abort

import forms
import who
from . import admin


@admin.record
def configure(state):
    app = state.app
    app.who_api_factory = who.make_repoze_who_api_factory()

    @app.errorhandler(401)
    def unauthorized_error_handler(error):
        who_api = app.who_api_factory(request.environ)
        return who_api.challenge()

    @admin.before_request
    def restrict_to_admins():
        who_api = app.who_api_factory(request.environ)
        g.user = who_api.authenticate()


def login_required(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if not g.user:
            abort(401)
        return func(*args, **kwargs)
    return f


@admin.route('/login', methods=['GET', 'POST'])
def login():
    who_api = who.get_api(request.environ)
    form = forms.LoginForm(request.form)
    
    if request.method == 'POST' and form.validate():
        authenticated, headers = who_api.login(form.data)
        if authenticated:
            location = request.values.get('came_from')
            response = redirect(location or '/')
            response.headers.extend(headers)
            return response
        flash(u'Wrong username or password', 'error')
    return render_template('login.html', form=form)


@admin.route('/logout', methods=['GET'])
def logout():
    who_api = who.get_api(request.environ)
    headers = who_api.forget()
    session.clear()
    response = redirect(url_for('admin.index'))
    response.headers.extend(headers)
    return response


@admin.route('/', methods=['GET'])
@login_required
def index():
    return 'Index!'
