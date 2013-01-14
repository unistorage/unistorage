import file_utils
from app import db, fs
from wsgi import app


with app.app_context():
    files_to_update = db.fs.files.find({
        'pending': False,
        #'unistorage_type': 'video',
        #'extra.audio.codec': 'vorbis'
    })
    fields_to_update = ['extra.video.codec']

    for file in list(files_to_update):
        _id = file['_id']
        print 'Processing %s' % _id

        gridout = fs.get(_id)
        file_data = file_utils.get_file_data(gridout, file['filename'])

        set_spec = {}
        for field in fields_to_update:
            parts = field.split('.')

            target_dict = set_spec
            source_dict = file_data
            original_dict = file
            for part in parts[:-1]:
                source_dict = source_dict[part]
                original_dict = original_dict[part]
                target_dict.setdefault(part, {})
                target_dict = target_dict[part]
            
            last_part = parts[-1]
            something_has_changed = False
            if source_dict[last_part] == original_dict[last_part]:
                print '  Field `%s` has not changed.' % field
            else:
                something_has_changed = True
            if not something_has_changed:
                print '  Nothing has changed!'
            target_dict[last_part] = source_dict[last_part]
        
        if 'content_type' in fields_to_update:
            set_spec['contentType'] = set_spec.pop('content_type')

        db.fs.files.update({'_id': _id}, {'$set': set_spec})
        print '  OK'
