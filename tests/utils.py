import unittest
import sys
import os.path
from StringIO import StringIO

import redis
from flask import g, url_for
from webtest import TestApp
from bson.objectid import ObjectId
from rq import Queue, Worker, use_connection

import app
import settings
import file_utils
from app.models import User, Statistics, RegularFile
from app.admin.forms import get_random_token
from tests.flask_webtest import FlaskTestCase, FlaskTestApp


FIXTURES_DIR = './tests/fixtures'

def fixture_path(path):
    return os.path.join(FIXTURES_DIR, path)


class WorkerMixin(object):
    """Provides `run_worker` method to run all tasks from default queue."""
    def run_worker(self):
        old_stderr = sys.stderr
        sys.stderr = sys.stdout # Let worker log be captured by nose

        use_connection(redis.Redis())
        queues = map(Queue, ['default'])
        w = Worker(queues)
        w.work(burst=True)

        sys.stderr = old_stderr


class ContextMixin(object):
    """
    Creates request context and runs `app.before_request`, so that
    `g` and `request` objects becomes available in tests.
    """
    def setUp(self):
        super(ContextMixin, self).setUp()
        self.ctx = app.create_app().test_request_context()
        self.ctx.push()
        app.before_request()

    def tearDown(self):
        super(ContextMixin, self).tearDown()
        self.ctx.pop()


class GridFSMixin(ContextMixin):
    """
    Provides `put_file(path)` method to put file in GridFS.
    Requires Flask request context (see `ContextMixin`).
    """
    def setUp(self):
        super(GridFSMixin, self).setUp()
        g.db_connection.drop_database(settings.MONGO_DB_NAME)

    def put_file(self, path, user_id=ObjectId('50516e3e8149950f0fa50462'), type_id=None):
        path = fixture_path(path)
        file = StringIO(open(path, 'rb').read())
        file.name = file.filename = os.path.basename(path)
        return RegularFile.put_to_fs(g.db, g.fs, file, **{
            'type_id': type_id,
            'user_id': user_id,
        })


class AdminFunctionalTest(ContextMixin, FlaskTestCase):
    def setUp(self):
        super(AdminFunctionalTest, self).setUp()
        self.app = FlaskTestApp(app.create_app())
        g.db_connection.drop_database(settings.MONGO_DB_NAME)

    def login(self):
        form = self.app.get(url_for('admin.login')).form
        form.set('login', settings.ADMIN_USERNAME)
        form.set('password', settings.ADMIN_PASSWORD)
        form.submit()


class StorageFlaskTestApp(FlaskTestApp):
    def __init__(self, app, token, **kwargs):
        super(StorageFlaskTestApp, self).__init__(app, **kwargs)
        self.token = token

    def do_request(self, req, status, expect_errors):
        req.headers.update({'Token': self.token})
        return super(StorageFlaskTestApp, self).do_request(req, status, expect_errors)


class StorageFunctionalTest(ContextMixin, FlaskTestCase):
    def setUp(self):
        super(StorageFunctionalTest, self).setUp()
        g.db_connection.drop_database(settings.MONGO_DB_NAME)
        
        token = get_random_token()
        User({'name': 'Test', 'token': token}).save(g.db)
        self.app = StorageFlaskTestApp(app.create_app(), token)

    def put_file(self, path, type_id=None):
        path = fixture_path(path)
        files = [('file', path)]
        params = {}
        if type_id is not None:
            params.update({'type_id': type_id})
            
        r = self.app.post('/', params, upload_files=files)
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)
        return r.json['resource_uri'], ObjectId(r.json['id'])

    def assert_fileinfo(self, r, key, value):
        self.assertEquals(r.json['information']['fileinfo'][key], value)

    def check(self, url, width=None, height=None, mime=None):
        r = self.app.get(url)
        self.assertEquals(r.json['status'], 'ok')
        if width:
            self.assert_fileinfo(r, 'width', width)
        if height:
            self.assert_fileinfo(r, 'height', height)
        if mime:
            self.assertEquals(r.json['information']['mimetype'], mime)
        return r
