# -*- coding: utf-8 -*-
import functools
from datetime import timedelta, datetime

from dateutil import tz
from flask import (g, request, redirect, url_for,
        render_template, flash, session, abort)

import settings
import forms
import who
from . import bp
from app.models import User, Statistics


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
            response = redirect(location or url_for('.index'))
            response.headers.extend(headers)
            return response
        flash(u'Неверный логин или пароль', 'error')
    return render_template('login.html', form=form)


@bp.route('/logout', methods=['GET'])
def logout():
    who_api = who.get_api(request.environ)
    headers = who_api.forget()
    session.clear()
    response = redirect(url_for('.index'))
    response.headers.extend(headers)
    return response


@bp.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html')


@bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'POST':
        form = forms.UserForm(request.form)
        if form.validate():
            user = User({
                'name': form.data['name'],
                'token': form.data['token']
            })
            user.save(g.db)
            return redirect(url_for('.users'))
        else:
            return render_template('user_create.html', **{
                'form': form
            })

    return render_template('users.html', **{
        'users': User.find(g.db)
    })


@bp.route('/users/create', methods=['GET'])
@login_required
def user_create():
    return render_template('user_create.html', **{
        'form': forms.UserForm(request.form)
    })


@bp.route('/users/<ObjectId:_id>/remove', methods=['GET'])
@login_required
def user_remove(_id):
    User.get_one(g.db, _id).remove(g.db)
    return redirect(url_for('.users'))


def get_utc_today():
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


@bp.route('/users/<ObjectId:user_id>', methods=['GET'])
@login_required
def user_statistics(user_id):
    type_ids = Statistics.find(g.db, {
        'user_id': user_id,
        'type_id': {'$ne':None}
    }).distinct('type_id')
    
    args = [user_id]
    kwargs = {}
    if request.args.get('type_id'):
        kwargs['type_id'] = request.args['type_id']
    
    statistics = Statistics.get_timely(g.db, *args, **kwargs)
    summary = Statistics.get_summary(g.db, *args, **kwargs)

    local_zone = tz.tzlocal()
    for entry in statistics:
        entry['timestamp'] = entry['timestamp'] \
                .replace(tzinfo=tz.tzutc()).astimezone(local_zone)
    
    return render_template('statistics.html', **{
        'user': User.get_one(g.db, {'_id': user_id}),
        'type_ids': type_ids,
        'statistics': statistics,
        'summary': summary
    })
