import sys

import redis
from rq import Queue, Worker, use_connection

import app


class WorkerMixin(object):
    def run_worker(self):
        old_stderr = sys.stderr
        sys.stderr = sys.stdout # Let worker log be captured by nose

        use_connection(redis.Redis())
        queues = map(Queue, ['default'])
        w = Worker(queues)
        w.work(burst=True)

        sys.stderr = old_stderr


class ContextMixin(object):
    def setUp(self):
        super(ContextMixin, self).setUp()
        self.ctx = app.app.test_request_context()
        self.ctx.push()
        app.before_request()

    def tearDown(self):
        super(ContextMixin, self).tearDown()
        self.ctx.pop()
