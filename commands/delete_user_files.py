# coding: utf-8
from app import db
from app.models import File, User, Statistics


def delete_user_files(user_name):
    """Deletes user stats. Marks all files as 'deleted&pending'
    """
    # Flask-Script неявно пушит application context, поэтому мы можем использовать db
    user = db[User.collection].find_one({'name': user_name})
    db[Statistics.collection].remove({
        'user_id': user['_id']
    })

    db[File.collection].update(
        {'user_id': user['_id'], 'deleted': False},
        {'$set': {'deleted':  True, 'pending': True}},
        multi=True
    )
