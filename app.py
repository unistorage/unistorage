import functools
from datetime import datetime

import gridfs
from flask import Flask, request, g, jsonify
from bson.objectid import ObjectId
from pymongo import Connection, ReplicaSetConnection
from pymongo.errors import InvalidId, AutoReconnect
from redis import Redis
from rq import Queue

import settings
import image_actions
from fileutils import get_file_data
from actions import handle_action_request, ValidationError


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

    users = g.db['test_users']
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
    file = request.files.get('file', '')
    if file:
        file_data = get_file_data(file)
        new_file = g.fs.put(file.read(), user_id=request.user['_id'], **file_data)
        return jsonify({'status': 'ok', 'id': str(new_file)})
    else:
        return jsonify({'status': 'error', 'msg': 'File wasn\'t found'}), 400


def handle_get_file_info(file):
    _id = file._id
    if hasattr(file, 'finish_time'):
        finish_time = file.finish_time
        if finish_time < datetime.now():
            finish_time = datetime.now() + (finish_time - file.uploadDate)
            finish_time = finish_time.replace(microsecond=0)
            g.db.fs.files.update({'_id': _id}, {'$set': {'finish_time': finish_time}})
        return jsonify({'status': 'wait', 'finish_time': str(finish_time)})

    if hasattr(settings, 'GFS_PORT') and settings.GFS_PORT != 80:
        uri = 'http://%s:%s/%s' % (settings.GFS_HOST, settings.GFS_PORT, _id)
    else:
        uri = 'http://%s/%s' % (settings.GFS_HOST, _id)
    information = {
        'name': file.name,
        'size': file.length,
        'mimetype': file.content_type,
        'uri': uri
    }
    if hasattr(file, 'fileinfo'):
        information['fileinfo'] = file.fileinfo
    return jsonify({'status': 'ok', 'information': information})

@app.route('/<string:_id>/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def get_file_info(_id=None):
    if request.method != 'GET':
        return jsonify({'status': 'error', 'msg': 'not implemented'}), 501

    _id = ObjectId(_id)
    try:
        file = g.fs.get(_id)
    except InvalidId:
        return jsonify({'status': 'error', 'msg': 'File wasn\'t found'}), 400
    
    if request.args and 'action' in request.args:
        try:
            target_id = handle_action_request(file, request)
            return jsonify({'status': 'ok', 'id': str(target_id)})
        except ValidationError as e:
            return jsonify({'status': 'error', 'msg': str(e)}), 400
    else:
        return handle_get_file_info(file)

def get_mongodb_connection():
    if settings.MONGO_DB_REPL_ON:
        return ReplicaSetConnection(settings.MONGO_DB_REPL_URI,
                    replicaset=settings.MONGO_REPLICA_NAME)
    else:
        return Connection(settings.MONGO_HOST, settings.MONGO_PORT)

def get_redis_connection():
    return Redis()

@app.before_request
def before_request():
    g.connection = get_mongodb_connection()
    g.db = g.connection[settings.MONGO_DB_NAME]
    g.fs = gridfs.GridFS(g.db)
    g.q = Queue(connection=get_redis_connection())

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'connection'):
        g.connection.close()

if settings.DEBUG:
    app.config['PROPAGATE_EXCEPTIONS'] = True # Useful when running with uwsgi

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=settings.DEBUG)
