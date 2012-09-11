import functools

from flask import request, Blueprint, jsonify


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
                return jsonify({'status': 'error', 'msg': 'not implemented'}), 501
            else:
                return func(*args, **kwargs)
        return f
    return wrap


def ok(response):
    response.update({'status': 'ok'})
    return jsonify(response)


def error(response):
    response.update({'status': 'error'})
    return jsonify(response)
