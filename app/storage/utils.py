import json
import functools

from bson.objectid import ObjectId
from flask import request, Blueprint
from flask.globals import current_app


class StorageBlueprint(Blueprint):
    def route(self, rule, **options):
        # Allow all methods for routing. Check method manually
        # for each view using `methods_required`
        options['methods'] = ['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS']
        return super(StorageBlueprint, self).route(rule, **options)


def methods_required(methods):
    def wrap(func):
        @functools.wraps(func)
        def f(*args, **kwargs):
            if request.method not in methods:
                return error({'msg': 'not implemented'}), 501
            else:
                return func(*args, **kwargs)
        return f
    return wrap


class ObjectIdJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(ObjectIdJSONEncoder, self).default(obj)


# Watch for https://github.com/mitsuhiko/flask/pull/471
def jsonify(data):
    return current_app.response_class(
            json.dumps(data, cls=ObjectIdJSONEncoder), mimetype='application/json')


def ok(response):
    response.update({'status': 'ok'})
    return jsonify(response)


def error(response):
    response.update({'status': 'error'})
    return jsonify(response)
