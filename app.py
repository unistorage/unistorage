import gridfs
import json
import functools
from flask import Flask, request
from bson.objectid import ObjectId
from pymongo import Connection
from pymongo.errors import InvalidId


from settings import TOKENS, GFS_HOST, GFS_PORT


app = Flask(__name__)
db = Connection('localhost', 27017)['test_base']
fs = gridfs.GridFS(db)


def get_or_create_user(token):
    def check_token(token):
        def check_format(token):
            #checking token format
            #It's just 32 digits required now
            return len(token) == 32

        def allow_token(token):
            #some tests to allow token..
            if token in TOKENS:
                return 1

        try:
            token = str(token)
        except BaseException:
            return 0

        return check_format(token) and allow_token(token)

    users = db['test_users']
    #return False if token is not allowed
    return check_token(token) and (users.find_one({"token": token}) or
        users.find_one({"_id": users.insert({"token": token})}))

def login_required(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if request:
            token = request.headers.get("Token", "")
            user = get_or_create_user(token)
            if user:
                request.user = user
                return func(*args, **kwargs)
        return json.dumps({'status': 'error', 'msg': 'Login failed'}), 401
    return f

@app.route('/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def index():
    def convert_to_filename(name):
        import string
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in name if c in valid_chars)

    if request.method != 'POST':
        return json.dumps({'status': 'error', 'msg': 'not implemented'}), 501
    file = request.files.get('file', '')
    if file:
        filename = convert_to_filename(file.filename)
        new_file = fs.put(file.read(), user_id=request.user["_id"],
            filename=filename, content_type=file.content_type)
        return json.dumps({'status': 'ok', 'id': new_file.__repr__()})
    else:
        return json.dumps({'status': 'error', 'msg': 'File wasn\'t found'}), 400


@app.route('/<string:id>/', methods=['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'])
@login_required
def get_file_info(id=None):
    if request.method != 'GET':
        return json.dumps({'status': 'error', 'msg': 'not implemented'}), 501
    try:
        #InvalidId
        file = fs.get(ObjectId(id))
        return json.dumps({'status': 'ok', 'information': {'name': file.name,
            'size': file.length, 'mimetype': file.content_type,
            'uri': 'http://%s:%s/%s' % (GFS_HOST, GFS_PORT, id)}})
    except InvalidId:
        return json.dumps({'status': 'error', 'msg': 'File wasn\'t found'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
