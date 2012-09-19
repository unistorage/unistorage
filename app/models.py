from datetime import date, time, datetime, timedelta

import pytz
from bson import ObjectId
from monk import modeling
from monk.validation import ValidationError

import file_utils


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


class Template(ValidationMixin, modeling.Document):
    collection = 'templates'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'applicable_for': basestring,
        'action_list': list
    }
    required = ['user_id', 'applicable_for', 'action_list']


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

    @classmethod
    def _aggregate_statistics(cls, db, group_by, conditions):
        return db[Statistics.collection].group(
            group_by,
            conditions,
            {'files_size': 0, 'files_count': 0},
            'function(entry, summary) {' \
                'summary.files_size += entry.files_size;' \
                'summary.files_count += entry.files_count;' \
            '}',
            finalize='function(entry) {' \
                'entry.files_size /= (1024 * 1024);' \
                'entry.files_size = parseFloat(entry.files_size.toFixed(2));' \
                'entry.files_count = parseInt(entry.files_count);' \
            '}'
        )

    @classmethod
    def _get_conditions(cls, user_id, type_id=None, start=None, end=None):
        conditions = {'user_id': user_id}
        
        if type_id:
            conditions['type_id'] = type_id
        
        timestamp_conditions = {}
        if start or end:
            if start: 
                timestamp_conditions['$gte'] = start
            if end: 
                timestamp_conditions['$lte'] = end
            conditions['timestamp'] = timestamp_conditions
        return conditions

    @classmethod
    def get_timely(cls, db, user_id, **kwargs):
        conditions = cls._get_conditions(user_id, **kwargs)
        group_by = ['user_id', 'timestamp']
        if 'type_id' in kwargs:
            group_by.append('type_id')
        return cls._aggregate_statistics(db, group_by, conditions)

    @classmethod
    def get_summary(cls, db, user_id, **kwargs):
        conditions = cls._get_conditions(user_id, **kwargs)
        group_by = ['user_id']
        if 'type_id' in kwargs:
            group_by.append('type_id')
        result = cls._aggregate_statistics(db, group_by, conditions)
        return result[0] if result else None


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
    def put_to_fs(cls, db, fs, data, **kwargs):
        kwargs.update(file_utils.get_file_data(data))
        kwargs.update({
            'pending': False    
        })

        cls(**kwargs).validate()
        file_id = fs.put(data, **kwargs)

        today_utc_midnight = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0)

        db[Statistics.collection].update({
            'user_id': kwargs.get('user_id'),
            'type_id': kwargs.get('type_id'),
            'timestamp': today_utc_midnight,
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
