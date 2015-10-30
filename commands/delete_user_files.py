# coding: utf-8
from app import db
from app.models import File, User, Statistics


def delete_user_files(user_token):
    """Deletes user stats. Marks all files as 'deleted&pending'
    """
    # Flask-Script неявно пушит application context, поэтому мы можем использовать db
    user = User.get_one(db, {'token': user_token})
    user['blocked'] = True
    user.save(db)

    db[Statistics.collection].remove({
        'user_id': user['_id']
    })

    db[File.collection].update(
        {'user_id': user['_id'], 'deleted': False},
        {'$set': {'deleted':  True, 'pending': True}},
        multi=True
    )
