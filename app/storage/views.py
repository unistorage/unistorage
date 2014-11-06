# coding: utf-8
"""
Storage views
=============
"""
import time
import json
import logging
import random
import functools
import os.path
from datetime import datetime

import jsonschema
from flask import request, abort

import settings
from actions import templates
from actions.utils import ValidationError
from actions.handlers import apply_template, apply_action
from utils import ok, error, jsonify, methods_required
from . import bp
from app import db, fs
from app.uris import parse_file_uri, get_resource_uri_for
from app.models import (File, RegularFile, PendingFile, UpdatingPendingFile,
                        Template, ZipCollection)
from app.perms import AccessPermission
from app.aws import AWSRegularFile, get_aws_credentials


logger = logging.getLogger(__name__)


def login_required(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if not hasattr(request, 'user') or not request.user:
            abort(401)
        return func(*args, **kwargs)
    return f


@bp.route('/')
@methods_required(['POST'])
@login_required
def file_create():
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

    FileClass = RegularFile
    if request.user['s3']:
        kwargs.update({'aws_credentials': get_aws_credentials(request.user)})
        FileClass = AWSRegularFile

    file_id = FileClass.put_to_fs(db, fs, file.filename, file, **kwargs)
    return ok({
        'resource_uri': get_resource_uri_for('file', file_id)
    })


def get_pending_file(user, file):
    """Возвращает JSON-ответ с информацией о `file`.

    :param file: :term:`временный файл`
    :type file: :class:`app.models.File`
    """
    if file.can_be_served_by_unistore_nginx_serve():
        return jsonify({
            'status': 'just_uri',
            'ttl': file.ttl,
            'data': {
                'url': file.get_binary_data_url(db, through_nginx_serve=True)
            }
        })
    else:
        return jsonify({'status': 'wait', 'ttl': file.ttl})


def get_regular_file(user, file):
    """Возвращает JSON-ответ с информацией о `file`.

    :param file: :term:`обычный файл`
    :type file: :class:`app.models.File`
    """
    deviation = settings.TTL_DEVIATION
    data = {
        'status': 'ok',
        'data': {
            'name': file.filename,
            'size': file.length,
            'mimetype': file.content_type,
            'unistorage_type': file.unistorage_type,
            'url': file.get_binary_data_url(db),
            'extra': file.get('extra', {}),
        },
    }

    if not user.is_aware_of_api_changes:
        data['ttl'] = settings.TTL + random.randint(-deviation, deviation)

    if file.unistorage_type in ('video', 'audio', 'image'):
        schema_path = os.path.join(
            settings.PROJECT_PATH, './schemas/%s.json' % file.unistorage_type)
        with open(schema_path) as schema_file:
            schema = json.load(schema_file)
            # Присваиваем абсолютный URI, чтобы в схеме работали относительные $ref
            schema['id'] = 'file://%s' % schema_path
            try:
                jsonschema.validate(data, schema)
            except:
                logger.warning('Schema validation failed!', exc_info=True,
                               extra={'response': dict(data)})

    return jsonify(data)


@bp.route('/<ObjectId:_id>/')
@methods_required(['GET'])
@login_required
def file_view(_id=None):
    """Вьюшка, ответственная за три вещи:

    - Применение операции к файлу `id`, если GET-запрос содержит аргумент `action`
    - Применение шаблона к файлу `id`, если GET-запрос содержит аргумент `template`
    - Выдача информации о файле `id` во всех остальных случаях
    """
    source_file = File.get_one(db, {'_id': _id}) or \
        UpdatingPendingFile.get_one(db, {'_id': _id})

    if not source_file:
        return error({'msg': 'File wasn\'t found'}), 404
    AccessPermission(source_file).test(http_exception=403)

    try:
        action_presented = 'action' in request.args
        template_presented = 'template' in request.args

        if action_presented and template_presented:
            raise ValidationError('You can\'t specify both `action` and `template`.')

        apply_ = None
        if action_presented:
            apply_ = apply_action
        elif template_presented:
            apply_ = apply_template

        if apply_:
            target_id = apply_(source_file, request.args.to_dict())
            return ok({
                'resource_uri': get_resource_uri_for('file', target_id)
            })
    except ValidationError as e:
        return error({'msg': str(e)}), 400

    if source_file.pending:
        return get_pending_file(request.user, PendingFile(source_file))
    else:
        return get_regular_file(request.user, RegularFile(source_file))


@bp.route('/template/')
@methods_required(['POST'])
@login_required
def template_create():
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
    template_id = Template(template_data).save(db)
    return ok({
        'resource_uri': get_resource_uri_for('template', template_id)
    })


@bp.route('/template/<ObjectId:_id>/')
@methods_required(['GET'])
@login_required
def template_view(_id=None):
    """Вьюшка, показывавающая :term:`шаблон`."""
    template = Template.get_one(db, {'_id': _id})

    if not template:
        return error({'msg': 'Template wasn\'t found'}), 404
    AccessPermission(template).test(http_exception=403)

    return ok({
        'data': {
            'applicable_for': template.applicable_for,
            'action_list': template.action_list
        }
    })


@bp.route('/zip/')
@methods_required(['POST'])
@login_required
def zip_create(_id=None):
    """Вьюшка, создающая zip collection"""
    files_field = 'file[]'
    files = request.form.getlist(files_field)
    filename = request.form.get('filename')

    try:
        if not filename:
            raise ValidationError('`filename` field is required.')
        if not files:
            raise ValidationError('`%s` field is required'
                                  ' and must contain at least one file URI.' % files_field)

        try:
            file_ids = map(parse_file_uri, files)
        except ValueError:
            raise ValidationError('Not all `%s` are correct file URIs.' % files_field)

        # TODO Проверять, что файлы с указанными URI существуют и не временные?
    except ValidationError as e:
        return error({'msg': str(e)}), 400

    zip_collection = ZipCollection({
        'user_id': request.user.get_id(),
        'file_ids': file_ids,
        'filename': filename
    })
    zip_id = zip_collection.save(db)
    return ok({
        'resource_uri': get_resource_uri_for('zip', zip_id)
    })


@bp.route('/zip/<ObjectId:_id>/')
@methods_required(['GET'])
@login_required
def zip_view(_id):
    """Вьюшка, отдающая информацию о ZIP-коллекции."""
    zip_collection = ZipCollection.get_one(db, {'_id': _id})
    if not zip_collection:
        return error({'msg': 'Zip collection wasn\'t found'}), 404

    AccessPermission(zip_collection).test(http_exception=403)

    to_timestamp = lambda d: time.mktime(d.timetuple())
    will_expire_at = to_timestamp(zip_collection['created_at']) + settings.ZIP_COLLECTION_TTL
    now = to_timestamp(datetime.utcnow())

    ttl = int(will_expire_at - now)
    if ttl < 0:
        return error({'msg': 'Zip collection wasn\'t found'}), 404

    return ok({
        'ttl': ttl,
        'data': {
            'url': zip_collection.get_binary_data_url(db, through_nginx_serve=True),
            'filename': zip_collection.filename
        }
    })
