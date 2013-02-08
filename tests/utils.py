import os.path
import subprocess
import time

from flask import url_for
from celery import current_app
from celery.signals import task_sent
from bson.objectid import ObjectId

import app
import settings
from app import db, fs
from app.models import User, RegularFile
from app.admin.forms import get_random_token
from actions.tasks import perform_actions
from tests.flask_webtest import FlaskTestCase, FlaskTestApp


FIXTURES_DIR = './tests/fixtures'


def fixture_path(path):
    return os.path.join(FIXTURES_DIR, path)


class WorkerMixin(object):
    def __call__(self, result=None):
        try:
            self._sent_tasks = []
            @task_sent.connect
            def task_sent_handler(sender=None, task_id=None, task=None, args=None,
                                  kwargs=None, **kwds):
                self._sent_tasks.append((task, args, kwargs))
            super(WorkerMixin, self).__call__(result)
        finally:
            self._sent_tasks = []

    def run_worker(self):
        while self._sent_tasks:
            (task, args, kwargs) = self._sent_tasks.pop(0)
            self.assertEqual(task, 'actions.tasks.perform_actions')
            perform_actions(*args, **kwargs)

from app import mongo

class ContextMixin(object):
    """
    Creates request context and runs `app.before_request`, so that
    `g` and `request` objects becomes available in tests.
    """
    def setUp(self):
        super(ContextMixin, self).setUp()
        self.ctx = app.create_app().test_request_context()
        self.ctx.push()
        mongo.cx.drop_database(settings.MONGO_DB_NAME)

    def tearDown(self):
        super(ContextMixin, self).tearDown()
        self.ctx.pop()

    def get_id_from_uri(self, resource_uri):
        return ObjectId(resource_uri.rstrip('/').split('/')[-1])


class GridFSMixin(ContextMixin):
    """
    Provides `put_file(path)` method to put file in GridFS.
    Requires Flask request context (see `ContextMixin`).
    """
    def setUp(self):
        super(GridFSMixin, self).setUp()

    def put_file(self, path, user_id=ObjectId('50516e3e8149950f0fa50462'), type_id=None):
        path = fixture_path(path)
        return RegularFile.put_to_fs(db, fs, os.path.basename(path), open(path, 'rb'), **{
            'type_id': type_id,
            'user_id': user_id,
        })


class AdminFunctionalTest(ContextMixin, FlaskTestCase):
    def setUp(self):
        super(AdminFunctionalTest, self).setUp()
        self.app = FlaskTestApp(app.create_app())

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


class StorageFunctionalTest(ContextMixin, WorkerMixin, FlaskTestCase):
    def setUp(self):
        super(StorageFunctionalTest, self).setUp()
        
        token = get_random_token()
        User({'name': 'Test', 'token': token}).save(db)
        self.app = StorageFlaskTestApp(app.create_app(), token)

    def put_file(self, path, type_id=None):
        path = fixture_path(path)
        files = [('file', path)]
        params = {}
        if type_id is not None:
            params.update({'type_id': type_id})
            
        r = self.app.post('/', params, upload_files=files)
        self.assertEqual(r.json['status'], 'ok')
        return r.json['resource_uri']

    def assert_fileinfo(self, r, key, value):
        self.assertEqual(r.json['data']['extra'][key], value)

    def check(self, url, width=None, height=None, mime=None):
        r = self.app.get(url)
        self.assertEqual(r.json['status'], 'ok')
        if width:
            self.assert_fileinfo(r, 'width', width)
        if height:
            self.assert_fileinfo(r, 'height', height)
        if mime:
            self.assertEqual(r.json['data']['mimetype'], mime)
        return r
