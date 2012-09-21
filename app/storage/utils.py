# -*- coding: utf-8 -*-
"""
Хелперы для storage
===================
"""

import json
import functools

from bson.objectid import ObjectId
from flask import request, Blueprint
from flask.globals import current_app


class StorageBlueprint(Blueprint):
    """Blueprint, все адреса которого по умолчанию доступны всеми методами
    (GET, POST, HEAD, PUT, DELETE, OPTIONS), а не только HEAD и GET.

    Используется в комбинации с :func:`methods_required`::

        bp = StorageBlueprint('storage')
        @methods_required(['POST'])
        def view():
            pass
    """
    def route(self, rule, **options):
        if 'methods' not in options:
            options['methods'] = ['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS']
        return super(StorageBlueprint, self).route(rule, **options)


def methods_required(methods):
    """Декоратор, ограничивающий методы до перечисленных в `methods`.

    Если ``request.methods`` не находится в `methods`, декоратор возвращает JSON
    со статусом 501 и указанием о том, что метод не реализован.

    :param methods: допустимые методы
    :type response: list
    """
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
    """Наследник стандартного :class:`JSONEncoder`, умеющий работать с 
    :class:`bson.objectid.ObjectId`."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(ObjectIdJSONEncoder, self).default(obj)


# Watch for https://github.com/mitsuhiko/flask/pull/471
def jsonify(data):
    """Замена стандартного :func:`flask.jsonify`, использующая :class:`ObjectIdJSONEncoder`."""
    return current_app.response_class(
            json.dumps(data, cls=ObjectIdJSONEncoder), mimetype='application/json')


def ok(response):
    """Добавляет к `response` поле ``'status': 'ok'``.

    :param response: данные ответа
    :type response: dict
    """
    response.update({'status': 'ok'})
    return jsonify(response)


def error(response):
    """Добавляет к `response` поле ``'status': 'error'``.

    :param response: данные ответа
    :type response: dict
    """
    response.update({'status': 'error'})
    return jsonify(response)
