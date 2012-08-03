from flask import Flask, request
from bson.objectid import ObjectId
from pymongo import Connection
import gridfs
from hashlib import sha1
from settings import TOKENS

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


@app.route('/file/', methods=['GET', 'POST'])
def file():
    def convert_to_filename(name):
        import string
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in name if c in valid_chars)

    token = request.headers.get("Token", "")
    user = get_or_create_user(token)
    if not user:
        return 'Permission denied', 401

    if request.method == 'POST':
        file = request.files['file']
        filename = convert_to_filename(file.filename)
        if file:
            new_file = fs.put(file.read(), user_id=user["_id"],
                filename=filename)
            return '%s' % new_file
        else:
            return 'Empty request', 400

    #if GET method than return the list of all files id and links for this user
    answer = '['
    for file in db["fs.files"].find({"user_id": ObjectId(user["_id"])}):
        answer += ('{%s,' % (file["_id"]) +
            "u'link': /file/%s/%s}," % (sha1(token).hexdigest(), file["_id"]))
    answer = answer[:-1] + ']'
    return answer


@app.route('/file/<hash_token>/<id_file>')
def get_file(hash_token, id_file):
    token = request.headers.get("Token", "")
    user = get_or_create_user(token)
    file = fs.get(ObjectId(id_file))
    if sha1(token).hexdigest() == hash_token and file.user_id == user["_id"]:
        return '%s' % file.filename
    return 'Permission denied', 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
