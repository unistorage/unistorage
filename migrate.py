from bson import ObjectId

from app import db, fs
from wsgi import app


def generic_migrate(query, callback, no_input=False):
    files_to_update = db.fs.files.find(query, timeout=False)

    count = files_to_update.count()

    if count == 0:
        print 'No such entries found.'
        return
    
    if not no_input:
        print '%i files to be updated. Are you sure? (y/N)' % count
        a = raw_input('> ')
        if a not in ('y', 'Y'):
            exit()

    log = None
    if not no_input:
        print 'Log failed fixes (to ./failed-fixes.txt)? (y/N)'
        a = raw_input('> ')
        if a in ('y', 'Y'):
            log = open('./failed-fixes.txt', 'a+')

    for i, file_ in enumerate(files_to_update):
        id_ = file_['_id']
        print 'Processing %s (%i/%i)' % (id_, i, count)
        callback(id_, file_, log=log)

    if log:
        log.close()


def migrate(query, callback, no_input=False):
    """
    Updates files matching to `query`.
    If `force`, all files will be updated.
    If not, only those which `extra` field is broken.
    Example:
    >>> migrate({
    ...     'unistorage_type': 'video',
    ...     'extra.video.duration': None,
    ... })
    """
    query.update({'pending': False})
    generic_migrate(query, callback, no_input=no_input)


def main():
    with app.app_context():
        import code
        code.InteractiveConsole(locals={
            'migrate': migrate,
            'generic_migrate': generic_migrate,
        }).interact()


if __name__ == '__main__':
    main()
