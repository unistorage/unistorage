import file_utils
from wsgi import app
from app import db, fs

from bson import ObjectId as O

with app.app_context():
    files_to_update = db.fs.files.find({
        'pending': False,
        'modifications': {
            '$exists': True
        }
    }, timeout=False)

    count = files_to_update.count()
    for i, _file in enumerate(files_to_update, start=1):
        _id = _file['_id']
        print 'Processing file %s (%i/%i)' % (_id, i, count)

        for before_dot, value in _file['modifications'].iteritems():
            if isinstance(value, dict):
                set_spec = {}
                unset_spec = {}
                for after_dot, object_id in value.iteritems():
                    set_spec.update({
                        'modifications.%s_%s' % (before_dot, after_dot): object_id,
                    })
                    unset_spec.update({
                        'modifications.%s' % before_dot: True
                    })
                spec = {
                   '$set': set_spec,
                   '$unset': unset_spec
                }
                from pprint import pprint
                pprint(spec)
                db.fs.files.update({'_id': _id}, spec)

        print 'OK'
