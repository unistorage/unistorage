#!/usr/bin/env python
import sys

from celery.bin.celeryd import WorkerCommand

from actions.tasks import celery


def main():
    from celery import current_app
    worker = WorkerCommand(app=current_app).run(
            app=current_app, concurrency=1, hostname='test_worker')


sys.stderr = sys.stdout

if __name__ == '__main__':
    main()
