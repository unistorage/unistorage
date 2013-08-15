#!/usr/bin/env ipython
import json

import jsonschema

from app import get_db, fs
from wsgi import app
from actions.tasks import perform_actions
from pymongo.read_preferences import ReadPreference


def restart(query, no_input=False):
    """Starts actions for pending files matching `query`."""
    db = get_db(read_preference=ReadPreference.SECONDARY_PREFERRED)

    query.update({'pending': True})
    actions_to_update = db.fs.files.find(query, timeout=False)

    count = actions_to_update.count()
   
    if count == 0:
        print 'No such entries found.'
        return 

    if not no_input:
        print '%i actions to be restarted. Are you sure? (y/N)' % count
        a = raw_input('> ')
        if a not in ('y', 'Y'):
            exit()

    for i, action in enumerate(actions_to_update, start=1):
        id_ = action['_id']
        print 'Processing %s (%i/%i)' % (id_, i, count)
        original = db.fs.files.find_one(action['original'])
        perform_actions.delay(
            id_, source_unistorage_type=original['unistorage_type'])
        print 'OK'


def main():
    banner = """
================================
Type `help(restart)` to get help
================================
"""
    with app.app_context():
        import code
        code.InteractiveConsole(locals=globals()).interact(banner)


if __name__ == '__main__':
    main()
