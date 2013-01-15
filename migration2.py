import json
from pprint import pprint

import jsonschema

import file_utils
from app import db, fs
from wsgi import app


def validate_extra(unistorage_type, extra):
    if not unistorage_type:
        raise Exception('File doesn\'t have `unistorage_type`')
    elif unistorage_type in ('video', 'audio', 'image'):
        with open('schemas/%s.json' % unistorage_type) as schema_file:
            schema = json.load(schema_file)
            extra_schema = schema['properties']['data']['properties']['extra']
            jsonschema.validate(extra, extra_schema)


with app.app_context():
    files_to_update = db.fs.files.find({
        'pending': False,
        #'unistorage_type': 'video',
        #'extra.audio.codec': 'vorbis'
    })

    count = files_to_update.count()
    log = open('./failed_fixes.txt', 'a+')
    for i, _file in enumerate(files_to_update):
        _id = _file['_id']
        print 'Processing %s (%i/%i)' % (_id, i, count)
        try:
            unistorage_type = _file.get('unistorage_type')
            extra = _file.get('extra', {})
            validate_extra(unistorage_type, extra)
        except Exception as e:
            print '  Schema validation failed:'
            print '  %s: %s' % (e, getattr(e, 'path', ''))
            gridout = fs.get(_id)
            new_file_data = file_utils.get_file_data(gridout, _file['filename'])

            new_unistorage_type = new_file_data['unistorage_type']
            new_extra = new_file_data['extra']

            set_spec = {
               '$set': {
                    'unistorage_type': new_unistorage_type,
                    'extra': new_extra,
                }
            }
            db.fs.files.update({'_id': _id}, set_spec)

            try:
                validate_extra(new_unistorage_type, new_extra)
            except Exception as e:
                print '  Not fixed!'
                message = '  %s: %s' % (e, getattr(e, 'path', ''))
                print message
                log.write('%s %s\n' % (_id, message))
            else:
                print '  Fixed'
        else:
            print 'OK'

    log.close()
