import functools

from flask import g, request, redirect, url_for, render_template, flash, session, abort

import forms
import who
from . import bp


def login_required(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if not request.user:
            abort(401)
        return func(*args, **kwargs)
    return f


@bp.route('/login', methods=['GET', 'POST'])
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


@bp.route('/logout', methods=['GET'])
def logout():
    who_api = who.get_api(request.environ)
    headers = who_api.forget()
    session.clear()
    response = redirect(url_for('admin.index'))
    response.headers.extend(headers)
    return response


@bp.route('/', methods=['GET'])
@login_required
def index():
    return 'Index!'
