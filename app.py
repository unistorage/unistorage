import json
import functools

import magic
import gridfs
from flask import Flask, request, g
from bson.objectid import ObjectId
from pymongo import Connection, ReplicaSetConnection
from pymongo.errors import InvalidId, AutoReconnect

import settings
from fileutils import get_file_data


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
        return json.dumps({'status': 'error', 'msg': 'Login failed'}), 401
    return f

@app.route('/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def index():
    if request.method != 'POST':
        return json.dumps({'status': 'error', 'msg': 'not implemented'}), 501
    file = request.files.get('file', '')
    if file:
        file_data = get_file_data(file)
        new_file = g.fs.put(file.read(), user_id=request.user['_id'], **file_data)
        return json.dumps({'status': 'ok', 'id': str(new_file)})
    else:
        return json.dumps({'status': 'error', 'msg': 'File wasn\'t found'}), 400

@app.route('/<string:id>/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def get_file_info(id=None):
    if request.method != 'GET':
        return json.dumps({'status': 'error', 'msg': 'not implemented'}), 501
    try:
        #InvalidId
        file = g.fs.get(ObjectId(id))
        if hasattr(settings, 'GFS_PORT') and settings.GFS_PORT != 80:
            uri = 'http://%s:%s/%s' % (settings.GFS_HOST, settings.GFS_PORT, id)
        else:
            uri = 'http://%s/%s' % (settings.GFS_HOST, id)
        return json.dumps({'status': 'ok', 'information': {
                'name': file.name,
                'size': file.length,
                'mimetype': file.content_type,
                'fileinfo': file.fileinfo,
                'uri': uri}})
    except InvalidId:
        return json.dumps({'status': 'error', 'msg': 'File wasn\'t found'}), 400

@app.before_request
def before_request():
    if settings.MONGO_DB_REPL_ON:
        g.connection = ReplicaSetConnection(settings.MONGO_DB_REPL_URI,
                    replicaset=settings.MONGO_REPLICA_NAME)
    else:
        g.connection = Connection(settings.MONGO_HOST, settings.MONGO_PORT)

    g.db = g.connection[settings.MONGO_DB_NAME]
    g.fs = gridfs.GridFS(g.db)
    g.magic = magic.Magic(mime=True)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'connection'):
        g.connection.close()

if settings.DEBUG:
    app.config['PROPAGATE_EXCEPTIONS'] = True # Useful when running with uwsgi

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=settings.DEBUG)
