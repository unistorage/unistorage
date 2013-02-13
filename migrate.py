import json

import jsonschema

import file_utils
from app import db, fs
from wsgi import app


def _validate_extra(unistorage_type, extra):
    if unistorage_type in ('video', 'audio', 'image'):
        with open('schemas/%s.json' % unistorage_type) as schema_file:
            schema = json.load(schema_file)
            extra_schema = schema['properties']['data']['properties']['extra']
            jsonschema.validate(extra, extra_schema)


def _validate(file_):
    unistorage_type = file_.get('unistorage_type')
    if not unistorage_type:
        raise Exception('File doesn\'t have `unistorage_type`')
    extra = file_.get('extra', {})
    _validate_extra(unistorage_type, extra)


def _update_extra(id_, file_):
    gridout = fs.get(id_)
    new_file_data = file_utils.get_file_data(gridout, file_['filename'])
    new_unistorage_type = new_file_data['unistorage_type']
    new_extra = new_file_data['extra']
    
    _validate_extra(new_unistorage_type, new_extra)

    db.fs.files.update({'_id': id_}, {
       '$set': {
            'unistorage_type': new_unistorage_type,
            'extra': new_extra,
        }
    })


def migrate(query, force=False, no_input=False):
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
        try:
            _validate(file_)
            if force:
                try:
                    _update_extra(id_, file_)
                except Exception as e:
                    print '  Update failed!'
                    message = '  %s: %s' % (e, getattr(e, 'path', ''))
                    print message
        except Exception as e:
            print '  Schema validation failed:'
            print '  %s: %s' % (e, getattr(e, 'path', ''))
            try:
                _update_extra(id_, file_)
            except Exception as e:
                print '  Not fixed!'
                message = '  %s: %s' % (e, getattr(e, 'path', ''))
                print message
                if log:
                    log.write('%s %s\n' % (id_, message))
            else:
                print '  Fixed'
        else:
            print 'OK'

    if log:
        log.close()


def main():
    banner = """
================================
Type `help(migrate)` to get help
================================
"""
    with app.app_context():
        import code
        code.InteractiveConsole(locals=globals()).interact(banner)


if __name__ == '__main__':
    main()
