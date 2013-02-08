# coding: utf-8
from gridfs import GridFS
from werkzeug.local import LocalProxy
from flask import Flask, _app_ctx_stack
from flask.ext.pymongo import PyMongo
from flask.ext.assets import Environment, Bundle
from raven.contrib.flask import Sentry

import settings
import connections
from utils import ObjectIdConverter, CustomRequest


mongo = PyMongo()
db = LocalProxy(lambda: mongo.db)
fs = LocalProxy(lambda: GridFS(mongo.db))


def create_app():
    app = Flask(__name__)

    configure_app(app)
    register_blueprints(app)
    register_bundles(app)

    import storage  # Ибо циклический импорт

    @app.errorhandler(404)
    def not_found_error_handler(e):
        return storage.utils.error(
            {'msg': 'The requested URL was not found on the server'}), 404

    @app.errorhandler(500)
    def server_error_handler(e):
        return storage.utils.error(
            {'msg': 'Something is wrong. We are working on it'}), 500

    return app


def configure_app(app):
    app.url_map.converters['ObjectId'] = ObjectIdConverter
    app.secret_key = settings.SECRET_KEY
    #app.teardown_appcontext(close_database_connection)
    app.request_class = CustomRequest
    app.config['PROPAGATE_EXCEPTIONS'] = settings.DEBUG

    app.config.update({
        'MONGO_HOST': 'localhost',
        'MONGO_PORT': 27017,
        'MONGO_DBNAME': settings.MONGO_DB_NAME,
    })
    mongo.init_app(app)
    
    sentry_dsn = getattr(settings, 'SENTRY_DSN', False)
    if sentry_dsn:
        Sentry(app, dsn=sentry_dsn)


def register_blueprints(app):
    import admin
    import storage
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(storage.bp)


def register_bundles(app):
    assets = Environment(app)

    bootstrap = Bundle(
        'less/bootstrap/bootstrap.less',
        'less/bootstrap-chosen.less',
        filters='less', output='gen/bootstrap.css')
    assets.register('bootstrap', bootstrap)

    css = Bundle(
        'css/layout.css',
        output='gen/style.css')
    assets.register('css', css)

    jquery = Bundle(
        'js/libs/jquery.min.js',
        output='gen/jquery.js')
    assets.register('jquery', jquery)
    
    common_js = Bundle(
        'js/libs/chosen.jquery.js',
        output='gen/common.js')
    assets.register('common_js', common_js)
    
    statistics_js = Bundle(
        'js/statistics.js',
        'js/libs/moment.min.js',
        output='gen/statistics-js.js')
    assets.register('statistics_js', statistics_js)
