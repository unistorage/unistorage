#!/usr/bin/env python
import sys
from cStringIO import StringIO

from celery.bin.celeryd import WorkerCommand


def main():
    from celery import current_app
    sys.stderr = StringIO()
    sys.stdout = StringIO()
    try:
        WorkerCommand(app=current_app).run(
            app=current_app, concurrency=1, hostname='test_worker', verbosity=0, loglevel='ERROR')
    except:
        pass


if __name__ == '__main__':
    main()
