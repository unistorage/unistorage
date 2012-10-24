#!/usr/bin/env python
import sys

from celery.bin.celeryd import WorkerCommand


def main():
    from celery import current_app
    try:
        WorkerCommand(app=current_app).run(
            app=current_app, concurrency=1, hostname='test_worker')
    except:
        pass


sys.stderr = sys.stdout

if __name__ == '__main__':
    main()
