# coding: utf-8
"""
Usage:
>>> from migration02 import get_callback
>>> generic_migrate({}, get_callback(criteria=['watermark']))
"""
from bson import ObjectId
from celery import chain

import settings
from app import db
from actions.tasks import perform_actions


def is_redo_needed(file_, criteria):
    """
    :param file_: словарь с информацией о файле из Mongo,
    :param criteria: список названий операций, подлежащих перезапуску,
                     либо callable, принимающий `file_`, и возвращающий
                     True, если перезапуск необходим.
    """
    if isinstance(criteria, list):
        actions = file_.get('actions', [])
        for action in actions:
            if action[0] in criteria:
                return True
        return False
    elif callable(criteria):
        return criteria(file_)


def get_linearized_tree(file_, criteria, redo_needed):
    chain_tasks = []
    redo_needed = is_redo_needed(file_, criteria)

    if redo_needed:
        chain_tasks.append(perform_actions.si(file_['_id'], with_low_priority=True))

    modifications = file_ and file_.get('modifications', {}) or {}

    result = redo_needed
    for child_id in modifications.values():
        child = db.fs.files.find_one({'_id': child_id})
        linearized_tree, tree_redo_needed = get_linearized_tree(child, criteria, redo_needed)
        if tree_redo_needed:
            chain_tasks.extend(linearized_tree)
            result = result or tree_redo_needed
            db.fs.files.update({'_id': child_id}, {
                '$set': {
                    'pending': True,
                    'ttl': settings.AVERAGE_TASK_TIME,
                },
            })

    return chain_tasks, result


def get_callback(criteria):
    def callback(id_, file_, log=None):
        if not file_.get('original'):
            chain_tasks, redo_needed = get_linearized_tree(file_, criteria, False)
            if redo_needed and chain_tasks:
                print '  %i tasks enqueued' % len(chain_tasks)
                chain(*chain_tasks)()
    return callback
