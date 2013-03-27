"""
Usage:
>>> from migration02 import get_callback
>>> generic_migrate({}, get_callback(actions_to_redo=['watermark']))
"""
from bson import ObjectId
from celery import chain

import settings
from app import db
from actions.tasks import perform_actions


def get_linearized_tree(file_, actions_to_redo, redo_needed):
    chain_tasks = []
    
    actions = file_.get('actions', [])
    for action in actions:
        if action[0] in actions_to_redo:
            redo_needed = True

    if redo_needed:
        chain_tasks.append(perform_actions.si(file_['_id']))

    modifications = file_.get('modifications', {})

    result = redo_needed
    for child_id in modifications.values():
        child = db.fs.files.find_one({'_id': child_id})
        linearized_tree, tree_redo_needed = get_linearized_tree(child, actions_to_redo, redo_needed)
        if tree_redo_needed:
            chain_tasks.extend(linearized_tree)
            result = result or tree_redo_needed
        db.fs.files.update({'_id': child_id}, {
           '$set': {
                'pending': True,
                'ttl': int(settings.AVERAGE_TASK_TIME.total_seconds()),
            }
        })

    return chain_tasks, result

def get_callback(actions_to_redo):
    def callback(id_, file_, log=None):
        if not file_.get('original'):
            chain_tasks, redo_needed = get_linearized_tree(file_, actions_to_redo, False)
            if redo_needed and chain_tasks:
                print '  %i tasks enqueued' % len(chain_tasks)
                chain(*chain_tasks)()
            else:
                print '  Skipped'
        else:
            print '  Skipped'
    return callback
