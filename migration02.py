from app import db

from actions.tasks import perform_actions


def recursively_redo(file_):
    modifications = file_.get('modifications')
    if not modifications:
        return

    for child_id in modifications.values():
        child = db.fs.files.find_one({'_id': child_id})
        db.fs.files.update({'_id': child_id}, {
           '$set': {
                'pending': True,
                'ttl': 5,
            }
        })
        action, args = child['actions'][0]
        print 'Redo %s modification (%s, %s) -- see %s' % \
            (file_['_id'], action, args, child_id)
        perform_actions.delay(child_id)
        recursively_redo(child)


def callback(id_, file_, log=None):
    if not file_.get('original'):
        recursively_redo(file_)
