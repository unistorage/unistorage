#!/usr/bin/env python
import sys
import subprocess
import signal

from actions.tasks import celery
from celery import current_app
from celery.bin.celeryd import WorkerCommand


sys.stderr = sys.stdout
def on_sigalrm(*args):
    reserved_tasks = current_app.control.inspect().reserved()
    if not reserved_tasks:
        return
    for tasks in reserved_tasks.values():
        if not tasks:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            current_app.control.broadcast('shutdown', destination=['test_worker'])
    signal.alarm(1)


signal.signal(signal.SIGALRM, on_sigalrm)
signal.alarm(1)


def main():
    worker = WorkerCommand(app=current_app).run(app=current_app, concurrency=1,
            hostname='test_worker')

if __name__ == '__main__':
    main()
