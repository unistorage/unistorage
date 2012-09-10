import os.path
import sys

import redis
from rq import Queue, Worker, use_connection
from flask import g

import app
import fileutils


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
    def put_file(self, path):
        f = open(path, 'rb')
        filename = os.path.basename(path)
        content_type = fileutils.get_content_type(f)
        return g.fs.put(f.read(), filename=filename, content_type=content_type)
