# coding: utf-8
import urllib2
from email.utils import encode_rfc2231
from unidecode import unidecode

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from models import RegularFile, Statistics, File
import file_utils
from app.date_utils import get_today_utc_midnight


from settings import (AWS_DEFAULT_ACCESS_KEY_ID,
                      AWS_DEFAULT_SECRET_ACCESS_KEY,
                      AWS_DEFAULT_BUCKET_NAME)


class AWSRegularFile(RegularFile):
    """Реализация модели :term:`файл в s3`. Наследуется от :class:`RegularFile`."""

    @classmethod
    def put_to_fs(cls, db, fs, file_name, file, aws_credentials, reduced_redundancy=False, **kwargs):
        """Обновляет поля `extra`, `content_type`, `filename` у kwargs, помещает `file` в GridFS
        и обновляет статистику. Помещает тело файла в s3

        :param aws_credentials: Данные для аутентификации в s3
        """
        kwargs.update(file_utils.get_file_data(file, file_name))
        kwargs.update({'pending': False})
        kwargs.update({'aws_bucket_name': aws_credentials['aws_bucket_name']})
        kwargs.update({'aws_size': len(file.read())})
        file.seek(0)

        cls(**kwargs).validate()

        file_id = fs.put('', **kwargs)
        put_file(aws_credentials, file_id, file, reduced_redundancy=reduced_redundancy, **kwargs)

        db[Statistics.collection].update({
            'user_id': kwargs.get('user_id'),
            'type_id': kwargs.get('type_id'),
            'timestamp': get_today_utc_midnight(),
        }, {
            '$inc': {
                'files_count': 1,
                'files_size': kwargs['aws_size'],
            }
        }, upsert=True)
        return file_id

    @classmethod
    def remove_from_fs(cls, db, fs, aws_credentials, **kwargs):
        super(AWSRegularFile, cls).remove_from_fs(db, fs, **kwargs)
        delete_file(aws_credentials, kwargs['_id'])


def put_file(aws_credentials, file_id, file, reduced_redundancy=False, **kwargs):
    """Кладет файл в s3"""
    bucket = get_bucket(aws_credentials)

    k = Key(bucket)
    k.key = str(file_id)
    k.content_type = kwargs.get('content_type')
    headers = {}
    filename = kwargs.get('filename')
    if filename:
        # Process non-latin filenames using technique described here:
        # http://greenbytes.de/tech/tc2231/#encoding-2231-fb
        rfc2231_filename = encode_rfc2231(filename.encode('utf-8'), 'UTF-8')
        transliterated_filename = unidecode(filename)
        content_disposition = 'inline; filename="{}"; filename*={};'.format(
            transliterated_filename, rfc2231_filename)

        headers = {'Content-Disposition': content_disposition}
    length = k.set_contents_from_file(file, reduced_redundancy=reduced_redundancy, headers=headers)
    k.make_public()
    return length


def get_file(aws_bucket_name, file_id):
    """Достает файл из s3. Т.к. все файлы публичные, используется простой http get
    """
    return urllib2.urlopen('http://{}.s3.amazonaws.com/{}'.format(aws_bucket_name, file_id))


def delete_file(aws_credentials, file_id):
    """Удаляет файл из s3"""
    bucket = get_bucket(aws_credentials)
    k = Key(bucket)
    k.key = str(file_id)
    k.delete()


def get_bucket(aws_credentials):
    """Возвращает 'bucket' для заданных данных аутентификции"""
    conn = S3Connection(aws_credentials['aws_access_key_id'],
                        aws_credentials['aws_secret_access_key'])
    return conn.get_bucket(aws_credentials['aws_bucket_name'])


def get_aws_credentials(user):
    """ Возвращает словарь с данными для аутентификации и загрузки файла в
    AWS S3, специфичный для пользователя, либо дефолтный
    """
    assert user.get('s3')

    return {'aws_access_key_id': user.get('aws_access_key_id') or AWS_DEFAULT_ACCESS_KEY_ID,
            'aws_secret_access_key': user.get('aws_secret_access_key') or AWS_DEFAULT_SECRET_ACCESS_KEY,
            'aws_bucket_name': user.get('aws_bucket_name') or AWS_DEFAULT_BUCKET_NAME}
