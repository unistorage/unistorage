import functools

from bson.objectid import ObjectId
from flask import request, g, jsonify, abort

import settings
from actions import templates
from file_utils import get_file_data
from actions.utils import ValidationError
from actions.handlers import apply_template, apply_action
from utils import ok, error, methods_required
from . import bp
from app.models import File


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
    file = request.files.get('file')
    if not file:
        return error({'msg': 'File wasn\'t found'}), 400
    
    kwargs = get_file_data(file)
    kwargs.update({
        'user_id': request.user['_id']
    })

    type_id = request.form.get('type_id')
    if type_id:
        if len(type_id) > 32:
            return error({'msg': '`type_id` is too long. Maximum length is 32.'}), 400
        kwargs.update({'type_id': type_id})

    f = File.put(g.db, g.fs, file.read(), kwargs)
    return ok({
        'id': str(f.get_id())
    })


@bp.route('/create_template')
@methods_required(['POST'])
@login_required
def create_template_view():
    try:
        template_data = templates.validate_and_get_template(
                request.form.get('applicable_for'),
                request.form.getlist('action[]'))
    except ValidationError as e:
        return error({'msg': str(e)}), 400
    
    template_collection = g.db[settings.MONGO_TEMPLATES_COLLECTION_NAME]
    template_data.update({
        'user_id': request.user['_id']
    })
    template_id = template_collection.insert(template_data)
    return ok({'id': str(template_id)})


@bp.route('/<ObjectId:_id>/')
@methods_required(['GET'])
@login_required
def id_view(_id=None):
    if not g.fs.exists(_id=_id):
        return error({'msg': 'File wasn\'t found'}), 400
    source_file = g.fs.get(_id)
    
    action_presented = 'action' in request.args
    template_presented = 'template' in request.args
    try:
        if action_presented and not template_presented:
            target_id = apply_action(source_file, request.args.to_dict())
            return ok({'status': 'ok', 'id': str(target_id)})
        elif template_presented and not action_presented:
            target_id = apply_template(source_file, request.args.to_dict())
            return ok({'id': str(target_id)})
        elif action_presented and template_presented:
            raise ValidationError('You can\'t specify both `action` and `template`.')
    except ValidationError as e:
        return error({'msg': str(e)}), 400

    source_file_data = g.db.fs.files.find_one(_id)
    if source_file_data.get('pending', False):
        return get_pending_file(source_file_data)
    else:
        return get_regular_file(source_file_data)


def get_gridfs_serve_url(path):
    return '%s/%s' % (settings.GRIDFS_SERVE_URL, path.lstrip('/'))


def get_unistore_nginx_serve_url(path):
    return '%s/%s' % (settings.UNISTORE_NGINX_SERVE_URL, path.lstrip('/'))


def can_unistore_serve(file_data):
    original_content_type = file_data['original_content_type']
    actions = file_data['actions']

    if not original_content_type.startswith('image') or len(actions) > 1:
        # If source file is not an image or more than one action was applied to it
        return False
    
    action_name, action_args = actions[0]
    mode, w, h = action_args
        
    if action_name != 'resize' or mode not in ('keep', 'crop'):
        return False

    return True


def get_pending_file(file_data):
    ttl = file_data['ttl']
    if hasattr(settings, 'UNISTORE_NGINX_SERVE_URL') and \
            can_unistore_serve(file_data):
        return ok({
            'ttl': ttl,
            'uri': get_unistore_nginx_serve_url(str(file_data['_id']))
        })
    else:
        return jsonify({'status': 'wait', 'ttl': file_data['ttl']})


def get_regular_file(file_data):
    return ok({
        'information': {
            'name': file_data['filename'],
            'size': file_data['length'],
            'mimetype': file_data['contentType'],
            'uri': get_gridfs_serve_url(str(file_data['_id'])),
            'fileinfo': file_data.get('fileinfo', {})
        },
        'ttl': settings.TTL
    })
