# -*- coding: utf-8 -*-
"""
Storage views
=============
"""
import functools
import time
from datetime import datetime

from bson.objectid import ObjectId
from flask import request, g, abort, url_for
from pymongo.errors import InvalidId 

import settings
from actions import templates
from file_utils import get_file_data
from actions.utils import ValidationError
from actions.handlers import apply_template, apply_action
from utils import ok, error, jsonify, methods_required
from . import bp
from app.models import File, RegularFile, PendingFile, Template, ZipCollection
from app.perms import AccessPermission


def login_required(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if not request.user:
            abort(401)
        return func(*args, **kwargs)
    return f


@bp.route('/')
@methods_required(['POST'])
@login_required
def index_view():
    """Вьюшка, сохраняющая файл в хранилище."""
    file = request.files.get('file')
    if not file:
        return error({'msg': 'File wasn\'t found'}), 400
    
    kwargs = {
        'user_id': request.user['_id']
    }
    type_id = request.form.get('type_id')
    if type_id:
        if len(type_id) > 32:
            return error({'msg': '`type_id` is too long. Maximum length is 32.'}), 400
        kwargs.update({'type_id': type_id})

    file_id = RegularFile.put_to_fs(g.db, g.fs, file.filename, file, **kwargs)
    return ok({
        'id': file_id,
        'resource_uri': url_for('.file_view', _id=file_id)
    })


@bp.route('/create_template')
@methods_required(['POST'])
@login_required
def create_template_view():
    """Вьюшка, создающая :term:`шаблон`."""
    try:
        template_data = templates.validate_and_get_template({
            'applicable_for': request.form.get('applicable_for'),
            'actions': request.form.getlist('action[]'),
        })
    except ValidationError as e:
        return error({'msg': str(e)}), 400
    
    template_data.update({
        'user_id': request.user['_id']
    })
    template_id = Template(template_data).save(g.db)
    return ok({
        'id': template_id,
        'resource_uri': None # Шаблоны можно только создавать
    })


@bp.route('/<ObjectId:_id>/')
@methods_required(['GET'])
@login_required
def file_view(_id=None):
    """Вьюшка, ответственная за три вещи:

    - Применение операции к файлу `id`, если GET-запрос содержит аргумент `action`
    - Применение шаблона к файлу `id`, если GET-запрос содержит аргумент `template`
    - Выдача информации о файле `id` во всех остальных случаях
    """
    source_file = File.get_one(g.db, {'_id': _id})
    
    if not source_file:
        return error({'msg': 'File wasn\'t found'}), 404
    
    AccessPermission(source_file).test(http_exception=403) 

    try:
        action_presented = 'action' in request.args
        template_presented = 'template' in request.args
        
        apply_ = None
        if action_presented and not template_presented:
            apply_ = apply_action
        elif template_presented and not action_presented:
            apply_ = apply_template
        elif action_presented and template_presented:
            raise ValidationError('You can\'t specify both `action` and `template`.')
        
        if apply_:
            target_id = apply_(source_file, request.args.to_dict())
            return ok({
                'id': target_id,
                'resource_uri': url_for('.file_view', _id=target_id)
            })
    except ValidationError as e:
        return error({'msg': str(e)}), 400

    if source_file.pending:
        return get_pending_file(PendingFile(source_file))
    else:
        return get_regular_file(RegularFile(source_file))


@bp.route('/zip')
@methods_required(['POST'])
@login_required
def create_zip_view(_id=None):
    """Вьюшка, создающая zip collection"""
    file_ids = request.form.getlist('file_id')
    filename = request.form.get('filename')
    
    try:
        if not filename:
            raise ValidationError('`filename` field is required.')
        if not file_ids:
            raise ValidationError('`file_id[]` field is required and must contain at least one id.')

        try:
            file_ids = map(ObjectId, file_ids)
        except InvalidId:
            raise ValidationError('Not all `file_id[]` are correct identifiers.')

        # TODO Проверять, что файлы с указанными айдишниками существуют и не временные?
    except ValidationError as e:
        return error({'msg': str(e)}), 400

    zip_collection = ZipCollection({
        'user_id': request.user.get_id(),
        'file_ids': file_ids,
        'filename': filename
    })
    zip_id = zip_collection.save(g.db)
    return ok({
        'id': zip_id,
        'resource_uri': url_for('.zip_view', _id=zip_id)
    })


@bp.route('/zip/<ObjectId:_id>/')
@methods_required(['GET'])
@login_required
def zip_view(_id):
    """Вьюшка, отдающая информацию о zip collection"""
    zip_collection = ZipCollection.get_one(g.db, {'_id': _id})
    if not zip_collection:
        return error({'msg': 'Zip collection wasn\'t found'}), 404

    AccessPermission(zip_collection).test(http_exception=403) 

    to_timestamp = lambda td: time.mktime(td.timetuple())
    will_expire_at = to_timestamp(zip_collection['created_at'] + settings.ZIP_COLLECTION_TTL)
    now = to_timestamp(datetime.utcnow())
    
    ttl = will_expire_at - now
    if ttl < 0:
        return error({'msg': 'Zip collection wasn\'t found'}), 404

    if hasattr(settings, 'UNISTORE_NGINX_SERVE_URL'):
        return ok({
            'ttl': ttl,
            'uri': get_unistore_nginx_serve_url(str(zip_collection.get_id()))
        })
    else:
        return error(), 503


def get_gridfs_serve_url(path):
    """Возвращает путь к gridfs-serve (`path` становится постфиксом ``settings.GRIDFS_SERVE_URL``).

    :param path: путь
    :type path: basestring
    """
    return '%s/%s' % (settings.GRIDFS_SERVE_URL, path.lstrip('/'))


def get_unistore_nginx_serve_url(path):
    """Возвращает путь к unistore-nginx-serve
    (`path` становится постфиксом ``settings.UNISTORE_NGINX_SERVE_URL``).

    Предполагает, что :class:`settings` имеет атрибут ``UNISTORE_NGINX_SERVE_URL``
    (он опционален).

    :param path: путь
    :type path: basestring
    """
    return '%s/%s' % (settings.UNISTORE_NGINX_SERVE_URL, path.lstrip('/'))


def can_unistore_serve(file):
    """Возвращает True, если `file` может быть отдан с помощью unistore-nginx-serve (например, в
    случае, если `file` -- картинка, для которой заказан ресайз).

    :param file: :term:`временный файл`
    :type file: :class:`app.models.File`
    """
    original_content_type = file.original_content_type
    actions = file.actions

    supported_types = ('image/gif', 'image/png', 'image/jpeg')
    if not original_content_type in supported_types or len(actions) > 1:
        return False
    
    action_name, action_args = actions[0]
    if action_name == 'resize':
        mode, w, h = action_args
        if mode in ('keep', 'crop'):
            return True
    elif action_name == 'rotate':
        return True

    return False


def get_pending_file(file):
    """Возвращает JSON-строку с информацией о `file`.
    
    :param file: :term:`временный файл`
    :type file: :class:`app.models.File` 
    """
    ttl = file.ttl
    if hasattr(settings, 'UNISTORE_NGINX_SERVE_URL') and can_unistore_serve(file):
        return ok({
            'ttl': ttl,
            'uri': get_unistore_nginx_serve_url(str(file.get_id()))
        })
    else:
        return jsonify({'status': 'wait', 'ttl': ttl})


def get_regular_file(file):
    """Возвращает JSON-строку с информацией о `file`.
    
    :param file: :term:`обычный файл`
    :type file: :class:`app.models.File` 
    """
    return ok({
        'information': {
            'name': file.filename,
            'size': file.length,
            'mimetype': file.content_type,
            'uri': get_gridfs_serve_url(str(file.get_id())),
            'fileinfo': file.get('fileinfo', {})
        },
        'ttl': settings.TTL
    })
