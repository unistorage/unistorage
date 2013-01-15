import json
from pprint import pprint

import jsonschema

import file_utils
from app import db, fs
from wsgi import app


def validate_extra(_file):
    unistorage_type = _file.get('unistorage_type')
    if not unistorage_type:
        raise Exception('File doesn\'t have `unistorage_type`')
    elif unistorage_type in ('video', 'audio', 'image'):
        with open('schemas/%s.json' % unistorage_type) as schema_file:
            schema = json.load(schema_file)
            extra_schema = schema['properties']['data']['properties']['extra']
            jsonschema.validate(_file.get('extra', {}), extra_schema)


with app.app_context():
    files_to_update = db.fs.files.find({
        'pending': False,
        #'unistorage_type': 'video',
        #'extra.audio.codec': 'vorbis'
    })

    for _file in files_to_update:
        _id = _file['_id']
        print 'Processing %s' % _id
        try:
            validate_extra(_file)
        except Exception as e:
            print '  Schema validation failed:'
            print '  %s: %s' % (e, getattr(e, 'path', ''))
            gridout = fs.get(_id)
            new_file_data = file_utils.get_file_data(gridout, _file['filename'])

            set_spec = {
               '$set': {
                    'unistorage_type': new_file_data['unistorage_type'],
                    'extra': new_file_data['extra'],
                }
            }
            db.fs.files.update({'_id': _id}, set_spec)
            print '  Fixed'
        else:
            print 'OK'
