from bson import ObjectId
from celery import chain

import settings
from app import db
from actions.tasks import perform_actions


def get_linearized_tree(file_):
    chain_tasks = []
    if file_.get('original'):
        chain_tasks = [perform_actions.si(file_['_id'])]

    modifications = file_.get('modifications', {})

    for child_id in modifications.values():
        child = db.fs.files.find_one({'_id': child_id})
        chain_tasks.extend(get_linearized_tree(child))
        db.fs.files.update({'_id': child_id}, {
           '$set': {
                'pending': True,
                'ttl': int(settings.AVERAGE_TASK_TIME.total_seconds()),
            }
        })
    return chain_tasks


def callback(id_, file_, log=None):
    if not file_.get('original'):
        chain_tasks = get_linearized_tree(file_)
        if chain_tasks:
            print '  %i tasks enqueued' % len(chain_tasks)
            chain(*chain_tasks)()
        else:
            print '  Skipped'
    else:
        print '  Skipped'
