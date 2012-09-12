from rq import Queue
from gridfs import GridFS
from flask import Flask, g

import settings
import connections
from app.storage import storage
from app.admin import admin


app = Flask(__name__)
app.secret_key = 'N4BU123dasHxNoO8g'
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(storage)


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
