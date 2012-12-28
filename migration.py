import file_utils
from app import db, fs
from wsgi import app


with app.app_context():
    files_to_update = db.fs.files.find({
        'pending': False,
        #'unistorage_type': 'video',
        #'extra.audio.codec': 'vorbis'
    })
    fields_to_update = ['extra.audio.channels', 'content_type']

    for file in list(files_to_update):
        _id = file['_id']

        gridout = fs.get(_id)
        file_data = file_utils.get_file_data(gridout, file['filename'])

        set_spec = {}
        for field in fields_to_update:
            parts = field.split('.')

            target_dict = set_spec
            source_dict = file_data
            for part in parts[:-1]:
                source_dict = source_dict[part]
                target_dict.setdefault(part, {})
                target_dict = target_dict[part]

            target_dict[parts[-1]] = source_dict[parts[-1]]
        
        if 'content_type' in fields_to_update:
            set_spec['contentType'] = set_spec.pop('content_type')

        db.fs.files.update({'_id': _id}, {'$set': set_spec})
