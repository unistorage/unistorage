import functools
import logging.config
from datetime import datetime

import yaml
from bson.objectid import ObjectId
from pymongo.errors import InvalidId, AutoReconnect
from gridfs import GridFS
from flask import Flask, request, g, jsonify
from rq import Queue

import settings
from fileutils import get_file_data
from connections import get_redis_connection, get_mongodb_connection
from actions.handlers import handle_apply_action, handle_create_template, \
        handle_apply_template


config = yaml.load(open('logging.conf'))
logging.config.dictConfig(config)

app = Flask(__name__)


def get_or_create_user(token):
    def check_token(token):
        def check_format(token):
            #checking token format
            #It's just 32 digits required now
            return len(token) == 32

        def allow_token(token):
            #some tests to allow token..
            if hasattr(settings, 'TOKENS') and token in settings.TOKENS:
                return 1

        try:
            token = str(token)
        except BaseException:
            return 0

        return check_format(token) and allow_token(token)

    users = g.db[settings.MONGO_USERS_COLLECTION_NAME]
    #return False if token is not allowed
    return check_token(token) and (users.find_one({'token': token}) or
            users.find_one({'_id': users.insert({'token': token})}))


def login_required(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if request:
            token = request.headers.get('Token', '')
            user = get_or_create_user(token)
            if user:
                request.user = user
                return func(*args, **kwargs)
        return jsonify({'status': 'error', 'msg': 'Login failed'}), 401
    return f


@app.route('/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def index():
    if request.method != 'POST':
        return jsonify({'status': 'error', 'msg': 'not implemented'}), 501
    file = request.files.get('file')
    if file:
        file_data = get_file_data(file)
        new_file = g.fs.put(file.read(), user_id=request.user['_id'], **file_data)
        return jsonify({'status': 'ok', 'id': str(new_file)})
    else:
        return jsonify({'status': 'error', 'msg': 'File wasn\'t found'}), 400


def get_gridfs_serve_url(path):
    return '%s/%s' % (settings.GRIDFS_SERVE_URL, path.lstrip('/'))


def get_unistore_nginx_serve_url(path):
    return '%s/%s' % (settings.UNISTORE_NGINX_SERVE_URL, path.lstrip('/'))


def can_unistore_serve(file_data):
    original_content_type = file_data['original_content_type']
    actions = file_data['actions']

    if not original_content_type.startswith('image'):
        return False

    if len(actions) > 1:
        return False
    action_name, action_args = actions[0]
        
    if action_name != 'resize':
        return False

    mode, w, h = action_args
    if mode not in ('keep', 'crop'):
        return False

    return True


@app.route('/create_template', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def create_template():
    if request.method != 'POST':
        return jsonify({'status': 'error', 'msg': 'not implemented'}), 501
    return handle_create_template()


def handle_get_file_info(_id):
    file_data = g.db.fs.files.find_one(_id)
    
    if file_data.get('pending', False):
        if hasattr(settings, 'UNISTORE_NGINX_SERVE_URL') and can_unistore_serve(file_data):
            return jsonify({
                'status': 'ok',
                'ttl': file_data['ttl'],
                'uri': get_unistore_nginx_serve_url(str(_id))
            })
        else:
            return jsonify({
                'status': 'wait',
                'ttl': file_data['ttl']
            })
    else:
        information = {
            'name': file_data['filename'],
            'size': file_data['length'],
            'mimetype': file_data['contentType'],
            'uri': get_gridfs_serve_url(str(_id))
        }
        if 'fileinfo' in file_data:
            information['fileinfo'] = file_data['fileinfo']
        return jsonify({
            'status': 'ok',
            'information': information,
            'ttl': settings.TTL
        })


@app.route('/<string:_id>/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def get_file(_id=None):
    if request.method != 'GET':
        return jsonify({'status': 'error', 'msg': 'not implemented'}), 501

    _id = ObjectId(_id)
    if not g.fs.exists(_id=_id):
        return jsonify({'status': 'error', 'msg': 'File wasn\'t found'}), 400
    
    if 'action' in request.args:
        return handle_apply_action(_id)
    elif 'template' in request.args:
        return handle_apply_template(_id)
    else:
        return handle_get_file_info(_id)


@app.before_request
def before_request():
    g.connection = get_mongodb_connection()
    g.db = g.connection[settings.MONGO_DB_NAME]
    g.fs = GridFS(g.db)
    g.q = Queue(connection=get_redis_connection())


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'connection'):
        g.connection.close()


if settings.DEBUG:
    app.config['PROPAGATE_EXCEPTIONS'] = True # Useful when running with uwsgi

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=settings.DEBUG)
