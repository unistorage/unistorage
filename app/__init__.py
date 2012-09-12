from rq import Queue
from gridfs import GridFS
from flask import Flask, g
from flask.ext.assets import Environment, Bundle

import settings
import connections
import storage
import admin


app = Flask(__name__)
app.secret_key = settings.SECRET_KEY
app.register_blueprint(admin.bp, url_prefix='/admin')
app.register_blueprint(storage.bp)


assets = Environment(app)

bootstrap = Bundle('less/bootstrap/bootstrap.less', filters='less', output='gen/bootstap.css')
less = Bundle('less/layout.less', filters='less', output='gen/style.css')

assets.register('bootstrap', bootstrap)
assets.register('less', less)


if settings.DEBUG:
    app.config['PROPAGATE_EXCEPTIONS'] = True


@app.before_request
def before_request():
    g.db_connection = connections.get_mongodb_connection()
    g.db = g.db_connection[settings.MONGO_DB_NAME]
    g.fs = GridFS(g.db)
    g.q = Queue(connection=connections.get_redis_connection())


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db_connection'):
        g.db_connection.close()
