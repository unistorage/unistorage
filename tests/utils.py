import unittest
import sys
import os.path
from StringIO import StringIO

import redis
from flask import g
from webtest import TestApp
from bson.objectid import ObjectId
from rq import Queue, Worker, use_connection

import app
import settings
import file_utils
from app.models import User, Statistics, File


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
    Creates request context and run `app.before_request`, so that
    `g` and `request` objects becomes available in tests.
    """
    def setUp(self):
        super(ContextMixin, self).setUp()
        self.ctx = app.app.test_request_context()
        self.ctx.push()
        app.before_request()

    def tearDown(self):
        super(ContextMixin, self).tearDown()
        self.ctx.pop()


class GridFSMixin(object):
    """
    Provides `put_file(path)` method to put file in GridFS.
    Requires Flask request context (see `ContextMixin`).
    """
    def setUp(self):
        super(GridFSMixin, self).setUp()
        g.db[User.collection].drop()
        g.db[Statistics.collection].drop()
        g.db.fs.files.drop()
        g.db.fs.chunks.drop()
        g.db.fs.drop()

    def put_file(self, filepath, user_id=ObjectId('50516e3e8149950f0fa50462'), type_id=None):
        file = StringIO(open(filepath, 'rb').read())
        file.name = file.filename = os.path.basename(filepath)
        return File.put_to_fs(g.db, g.fs, file, **{
            'type_id': type_id,
            'user_id': user_id,
        })


class FunctionalTest(unittest.TestCase):
    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.app = TestApp(app.app)
        self.headers = {'Token': settings.TOKENS[0]}

    def put_file(self, path, type_id=None):
        files = [('file', path)]
        params = {}
        if type_id is not None:
            params.update({'type_id': type_id})
            
        r = self.app.post('/', params, headers=self.headers, upload_files=files)
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)
        return ObjectId(r.json['id'])

    def assert_fileinfo(self, r, key, value):
        self.assertEquals(r.json['information']['fileinfo'][key], value)

    def check(self, url, width=None, height=None, mime=None):
        r = self.app.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        if width:
            self.assert_fileinfo(r, 'width', width)
        if height:
            self.assert_fileinfo(r, 'height', height)
        if mime:
            self.assertEquals(r.json['information']['mimetype'], mime)
        return r
