# coding: utf-8
from app import db
from app.models import File


def delete_file_contents():
    """ Удаляет чанки данных для файлов, помеченных как 'deleted' и 'pending'.
    У обработанных файлов снимает флажок 'pending' """
    # Flask-Script неявно пушит application context, поэтому мы можем использовать db

    files = db[File.collection].find({
        'deleted': True,
        'pending': True,
    }).limit(100)

    ids = [f['_id'] for f in files]
    print ids

    db['fs.chunks'].remove({
        'files_id': {
            '$in': ids,
        },
    })

    db[File.collection].update(
        {'_id': {'$in': ids}},
        {'$set': {'pending': False}},
        multi=True)
