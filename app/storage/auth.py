import functools

from flask import request, g, jsonify

import settings


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
