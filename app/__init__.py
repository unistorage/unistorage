from rq import Queue
from gridfs import GridFS
from bson.errors import InvalidId
from bson import ObjectId
from flask import Flask, g
from werkzeug.routing import BaseConverter, ValidationError
from flask.ext.assets import Environment, Bundle

import settings
import connections


class ObjectIdConverter(BaseConverter):
    def to_python(self, value):
        try:
            return ObjectId(value)
        except InvalidId:
            raise ValidationError()

    def to_url(self, value):
        return str(value)



#@app.before_request
def before_request():
    g.db_connection = connections.get_mongodb_connection()
    g.db = g.db_connection[settings.MONGO_DB_NAME]
    g.fs = GridFS(g.db)
    g.q = Queue(connection=connections.get_redis_connection())


#@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db_connection'):
        g.db_connection.close()


def create_app():
    app = Flask(__name__)
    app.url_map.converters['ObjectId'] = ObjectIdConverter

    app.secret_key = settings.SECRET_KEY

    import admin
    app.register_blueprint(admin.bp, url_prefix='/admin')
    import storage
    app.register_blueprint(storage.bp)

    if settings.DEBUG:
        app.config['PROPAGATE_EXCEPTIONS'] = True


    assets = Environment(app)

    bootstrap = Bundle('less/bootstrap/bootstrap.less', 'less/bootstrap-chosen.less',
            filters='less', output='gen/bootstrap.css')
    jquery = Bundle('js/libs/jquery.min.js', output='gen/jquery.js')
    css = Bundle('css/layout.css', output='gen/style.css')
    statistics_js = Bundle('js/statistics.js', 
            'js/libs/jquery.flot.js', 'js/libs/chosen.jquery.js', output='gen/statistics-js.js')

    assets.register('bootstrap', bootstrap)
    assets.register('jquery', jquery)
    assets.register('css', css)
    assets.register('statistics_js', statistics_js)

    app.before_request(before_request)
    app.teardown_request(teardown_request)

    return app
