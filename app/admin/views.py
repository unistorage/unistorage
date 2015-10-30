# coding: utf-8
import functools
from datetime import timedelta

from dateutil import tz
from pytils import numeral
from bson.objectid import ObjectId
from flask.ext.principal import RoleNeed
from flask import request, redirect, url_for, render_template, flash, session, abort

import forms
import who
from . import bp
from app import db
from app.models import User, Statistics, File
from app.date_utils import get_today_utc_midnight


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
    start = get_today_utc_midnight() - timedelta(days=6)

    annotated_users = []
    for user in User.find(db):
        user_id = user.get_id()
        statistics_all_time = Statistics.get_summary(db, user_id=user_id)
        statistics_last_week = Statistics.get_summary(db, user_id=user_id, start=start)
        annotated_users.append((user, statistics_all_time, statistics_last_week))

    statistics = Statistics.get_timely(db, start=start)
    if statistics:
        statistics = fill_missing_entries_with_zeroes(statistics, start=start)
        statistics = update_timezone_to_local(statistics)

    return render_template('index.html', **{
        'annotated_users': annotated_users,
        'statistics': statistics,
        'summary': Statistics.get_summary(db, start=start),
        'numeral': numeral
    })


@bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'POST':
        form = forms.UserForm(request.form)
        _id = form.data.get('id')
        if form.validate():
            user = _id and User.get_one(db, {'_id': ObjectId(_id)}) or User()
            user.update({
                'name': form.data['name'],
                'token': form.data['token'],
                'needs': map(RoleNeed, form.data['has_access_to']),
                'domains': form.data['domains'],
                'is_aware_of_api_changes': form.data['is_aware_of_api_changes'],
                'blocked': form.data['blocked']
            })
            user.save(db)
            return redirect(url_for('.users'))
        else:
            template = _id and 'user_edit.html' or 'user_create.html'
            return render_template(template, **{
                'form': form
            })

    return render_template('users.html', **{
        'users': User.find(db)
    })


@bp.route('/users/create', methods=['GET'])
@login_required
def user_create():
    return render_template('user_create.html', **{
        'form': forms.UserForm(request.form)
    })


@bp.route('/users/<ObjectId:_id>/remove', methods=['POST'])
@login_required
def user_remove(_id):
    User.get_one(db, _id).remove(db)
    return redirect(url_for('.users'))


@bp.route('/users/<ObjectId:_id>/edit', methods=['GET'])
@login_required
def user_edit(_id):
    user = User.get_one(db, _id)
    form = forms.UserForm(request.form, obj=user)
    return render_template('user_edit.html', **{
        'form': form
    })


@bp.route('/users/<ObjectId:user_id>', methods=['GET'])
@login_required
def user_statistics(user_id):
    type_ids = Statistics.find(db, {
        'user_id': user_id,
        'type_id': {'$ne': None}
    }).distinct('type_id')

    kwargs = {
        'user_id': user_id,
        'start': get_today_utc_midnight() - timedelta(days=6)
    }
    if request.args.get('type_id'):
        kwargs['type_id'] = request.args['type_id']

    summary = Statistics.get_summary(db, **kwargs)

    statistics = Statistics.get_timely(db, **kwargs)
    if statistics:
        statistics = fill_missing_entries_with_zeroes(statistics, start=kwargs['start'])
        statistics = update_timezone_to_local(statistics)

    return render_template('user_statistics.html', **{
        'user': User.get_one(db, {'_id': user_id}),
        'type_ids': type_ids,
        'statistics': statistics,
        'summary': summary
    })


def fill_missing_entries_with_zeroes(statistics, start=None):
    today_utc_midnight = get_today_utc_midnight()

    entries = {}
    for entry in statistics:
        timestamp = entry['timestamp']
        entries[timestamp] = entry

    result = []
    entry_timestamp = start or statistics[0]['timestamp']
    while entry_timestamp <= today_utc_midnight:
        entry = entries.get(entry_timestamp, {
            'timestamp': entry_timestamp,
            'files_count': 0,
            'files_size': 0
        })
        result.append(entry)
        entry_timestamp += timedelta(days=1)

    return result


def update_timezone_to_local(statistics):
    local_zone = tz.tzlocal()
    for entry in statistics:
        entry['timestamp'] = entry['timestamp'].replace(
            tzinfo=tz.tzutc()).astimezone(local_zone)
    return statistics


@bp.route('/delete', methods=['POST', 'GET'])
@login_required
def file_delete():
    if request.method == 'POST':
        form = forms.DeleteForm(request.form)
        if form.validate():
            _id = form.data.get('id')
            recursive = form.data.get('recursive')

            file = File.get_one(db, {'_id': ObjectId(_id)})
            if not file:
                flash(u"File {} not found".format(_id), category='error')
            else:
                deleted_files_ids = file.delete(db, recursive=recursive)
                for file_id in deleted_files_ids:
                    flash(u"File {} deleted".format(file_id), category='info')

                form = forms.DeleteForm()
    else:
        form = forms.DeleteForm()

    return render_template('file_delete.html', **{
        'form': form
    })
