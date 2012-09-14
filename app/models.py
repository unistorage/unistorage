from datetime import date, time, datetime

from bson import ObjectId
from monk import modeling
from monk.validation import ValidationError

from file_utils import get_file_data


class ValidationMixin(object):
    def validate(self):
        super(ValidationMixin, self).validate()
        for field in self.required:
            if not self[field]:
                raise ValidationError('field %s is required' % field)


class User(ValidationMixin, modeling.Document):
    collection = 'users'
    structure = {
        '_id': ObjectId,
        'name': basestring,
        'token': basestring,
    }
    required = ['token']


class Statistics(ValidationMixin, modeling.Document):
    collection = 'statistics.daily'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'type_id': ObjectId,
        'timestamp': datetime,
        'files_count': int,
        'files_size': int
    }
    required = ['user_id', 'timestamp']


class File(ValidationMixin, modeling.Document):
    collection = 'fs.files'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'type_id': basestring,

        'fileinfo': dict,
        'original': ObjectId,
        'label': basestring,
        'filename': basestring,
        'content_type': basestring,
        'pending': bool
    }
    required = ['user_id', 'filename', 'content_type']

    @classmethod
    def wrap_incoming(cls, data, db):
        data['content_type'] = data.pop('contentType', None)
        data['upload_date'] = data.pop('uploadDate', None)
        data['chunk_size'] = data.pop('chunkSize', None)
        return super(File, cls).wrap_incoming(data, db)

    @classmethod
    def put_to_fs(cls, db, fs, data, kwargs):
        kwargs.update(get_file_data(data))
        kwargs.update({
            'pending': False    
        })

        cls(**kwargs).validate()
        file_id = fs.put(data, **kwargs)

        start_of_the_day = datetime.combine(date.today(), time())
        db[Statistics.collection].update({
            'user_id': kwargs.get('user_id'),
            'type_id': kwargs.get('type_id'),
            'timestamp': start_of_the_day,
        }, {
            '$inc': {'files_count': 1, 'files_size': fs.get(file_id).length}
        }, upsert=True)
        return file_id


class PendingFile(File):
    structure = dict(File.structure, **{
        'pending': True,
        'ttl': int,
        'actions': list,
        'original_content_type': basestring,
    })
    required = ['user_id', 'actions', 'label', 'original',
            'original_content_type', 'pending', 'ttl']

    @classmethod
    def find(cls, *args, **kwargs):
        kwargs.update({'pending': True})
        return cls.find(*args, **kwargs)

    @classmethod
    def get_one(cls, *args, **kwargs):
        kwargs.update({'pending': True})
        return cls.get_one(*args, **kwargs)

    @classmethod
    def put_to_fs(cls, db, fs, **kwargs):
        kwargs.update({'pending': True})
        cls(**kwargs).validate()
        file_id = fs.put('', **kwargs)
        return file_id
