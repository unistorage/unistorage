# -*- coding: utf-8 -*-
import logging
import os.path
from StringIO import StringIO
from tempfile import NamedTemporaryFile

from gridfs import GridFS
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, g, abort, current_app, _app_ctx_stack
from flask.wrappers import Request
from flask.ext.assets import Environment, Bundle
from werkzeug.local import LocalProxy
from werkzeug.routing import BaseConverter, ValidationError

import settings
import connections


def parse_resource_uri(uri):
    endpoint = None
    endpoint_args = {}
    try:
        endpoint, endpoint_args = current_app.url_map.bind('/').match(uri)
    except:
        pass
    return endpoint, endpoint_args


def parse_file_uri(uri):
    endpoint, args = parse_resource_uri(uri)
    if endpoint != 'storage.file_view' or '_id' not in args:
        raise ValueError('%s is not a file URI.' % uri)
    return args['_id']


def parse_template_uri(uri):
    endpoint, args = parse_resource_uri(uri)
    if endpoint != 'storage.template_view' or '_id' not in args:
        raise ValueError('%s is not a template URI.' % uri)
    return args['_id']


class ObjectIdConverter(BaseConverter):
    def to_python(self, value):
        try:
            return ObjectId(value)
        except InvalidId:
            raise ValidationError()

    def to_url(self, value):
        return str(value)


def get_db():
    ctx = _app_ctx_stack.top
    connection = getattr(ctx, 'mongo_connection', None)
    if connection is None:
        connection = connections.get_mongodb_connection()
        ctx.mongo_connection = connection
    return connection[settings.MONGO_DB_NAME]


def close_database_connection(error=None):
    connection = getattr(_app_ctx_stack.top, 'mongo_connection', None)
    if connection is not None:
        connection.close()

db = LocalProxy(get_db)
fs = LocalProxy(lambda: GridFS(get_db()))


def create_app():
    app = Flask(__name__)
    app.url_map.converters['ObjectId'] = ObjectIdConverter
    app.secret_key = settings.SECRET_KEY
    app.teardown_appcontext(close_database_connection)
    app.request_class = CustomRequest

    import admin
    import storage
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(storage.bp)

    @app.errorhandler(404)
    def not_found_error_handler(e):
        return storage.utils.error(
            {'msg': 'The requested URL was not found on the server'}), 404

    @app.errorhandler(500)
    def server_error_handler(e):
        return storage.utils.error({'msg': 'Something is wrong. We are working on it'}), 500

    if settings.DEBUG or True:
        app.config['PROPAGATE_EXCEPTIONS'] = True
        for handler in logging.getLogger('app_error_logger').handlers:
            app.logger.addHandler(handler)

    bootstrap = Bundle('less/bootstrap/bootstrap.less', 'less/bootstrap-chosen.less',
            filters='less', output='gen/bootstrap.css')
    css = Bundle('css/layout.css', output='gen/style.css')

    jquery = Bundle('js/libs/jquery.min.js', output='gen/jquery.js')
    common_js = Bundle('js/libs/chosen.jquery.js', output='gen/common.js')
    statistics_js = Bundle('js/statistics.js', 'js/libs/moment.min.js',
            output='gen/statistics-js.js')

    assets = Environment(app)
    assets.register('bootstrap', bootstrap)
    assets.register('jquery', jquery)
    assets.register('css', css)
    assets.register('common_js', common_js)
    assets.register('statistics_js', statistics_js)
    return app


def stream_factory(total_content_length, content_type, filename='', content_length=None):
    """Замена :func:`werkzeug.formparser.default_stream_factory`. Возвращает NamedTemporaryFile,
    а не TemporaryFile, что позволяет передать файл на вход avconv-у без копирования.
    """
    name, extension = os.path.splitext(filename)
    if total_content_length > 1024 * 500:
        return NamedTemporaryFile('wb+', suffix=extension)
    return StringIO()


class CustomRequest(Request):
    """Наследник :class:`flask.wrappers.Request`, использующий :func:`stream_factory`."""
    def _get_file_stream(self, total_content_length, content_type,
                         filename=None, content_length=None):
        return stream_factory(total_content_length, content_type,
                              filename=filename, content_length=content_length)
