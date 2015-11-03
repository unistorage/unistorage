# coding: utf-8
import sys
from app import db
from app.models import File, User, Statistics


def delete_user_files(user_token, statistics_delete=False, number_of_querying_files='100'):
    """Marks user as 'blocked', then deletes files. With '-s' deletes user
    statistics too. Use '-n NUMBER' to set number of files in query to delete
    """
    # Flask-Script неявно пушит application context, поэтому мы можем использовать db
    user = User.get_one(db, {'token': user_token})
    user['blocked'] = True
    user.save(db)

    def _get_files_ids():
        files = db[File.collection].find(
                {'user_id': user['_id'], 'deleted': {'$in': [None, False]}}
                ).limit(int(number_of_querying_files))
        return [f['_id'] for f in files]

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

    if statistics_delete:
        sys.stdout.write('Deleting statistics...')
        sys.stdout.flush()
        db[Statistics.collection].remove({
            'user_id': user['_id']
        })
        print 'done'
