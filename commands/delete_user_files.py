# coding: utf-8
import sys
from time import sleep
from app import db
from wsgi import app
from app.models import File, User, Statistics


def delete_user_files(user_token, statistics_delete=False, number_of_querying_files='100', query=False, block=False, pause=None):
    """'-b' marks user as 'blocked', then deletes files. With '-s' deletes user
    statistics too. Use '-n NUMBER' to set number of files in query to delete.
    Use '-p' for specifying time in seconds to sleep per operations.
    Use '-q' for specifying additional query
    """
    # Flask-Script неявно пушит application context, поэтому мы можем использовать db
    user = User.get_one(db, {'token': user_token})
    if block:
        user['blocked'] = True
        user.save(db)

    if query is True:
        with app.app_context():
            import code
            code.InteractiveConsole(locals=globals()).interact("call delete_user_files with 'query'")
        return

    search_query = {'user_id': user['_id'], 'deleted': {'$in': [None, False]}}
    if query is not False:
        search_query.update(query)

    def _get_files_ids():
        files = db[File.collection].find(search_query).limit(int(number_of_querying_files))
        return [f['_id'] for f in files]

    print 'Files for query {} will be deleted. Are you sure? (y/N)'.format(str(search_query))
    a = raw_input('> ')
    if a not in ('y', 'Y'):
        exit()

    while True:
        ids = _get_files_ids()
        if len(ids) == 0:
            break

        db['fs.chunks'].remove({
            'files_id': {
                '$in': ids,
            },
        })

        db[File.collection].update(
            {'_id': {'$in': ids}},
            {'$set': {'deleted':  True}},
            multi=True
        )

        sys.stdout.write('.')
        sys.stdout.flush()

        if pause:
            sleep(int(pause))

    if statistics_delete:
        sys.stdout.write('Deleting statistics...')
        sys.stdout.flush()
        db[Statistics.collection].remove({
            'user_id': user['_id']
        })
        print 'done'
