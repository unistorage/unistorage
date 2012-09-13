from datetime import date, time, datetime

from bson import ObjectId
from monk import modeling
from monk.validation import ValidationError


class ValidationMixin(object):
    def validate(self):
        super(ValidationMixin, self).validate()
        assert self.required
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
        'filename': basestring,
        'content_type': basestring,
        'fileinfo': dict,
        'original': ObjectId,
        'label': basestring,
    }
    required = ['user_id', 'filename', 'content_type']
    
    @classmethod
    def put(cls, db, fs, data, kwargs):
        File(**kwargs).validate()
        file_id = fs.put(data, **kwargs)
        
        start_of_the_day = datetime.combine(date.today(), time())

        file = cls.get_one(db, file_id)
        db[Statistics.collection].update({
            'user_id': kwargs.get('user_id'),
            'type_id': kwargs.get('type_id'),
            'timestamp': start_of_the_day,
        }, {
            '$inc': {'files_count': 1, 'files_size': file.length}
        }, upsert=True)
        return file
