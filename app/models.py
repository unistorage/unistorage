# coding: utf-8
import random
from datetime import datetime
from urlparse import urljoin

from bson import ObjectId
from monk import modeling
from monk.validation import ValidationError
from flask.ext.principal import RoleNeed

import settings
import file_utils
from app.date_utils import get_today_utc_midnight
from app.uris import parse_template_uri


class ValidationMixin(object):
    def validate(self):
        super(ValidationMixin, self).validate()
        for field in self.required:
            if not self[field]:
                raise ValidationError('Field %s is required.' % field)


class User(ValidationMixin, modeling.Document):
    """Реализация сущности :term:`пользователь`.

    .. attribute:: name

        Имя пользователя в свободной форме.

    .. attribute:: token

        Токен для авторизации.
    
    .. attribute:: needs

        Роли пользователя (Flask Principal needs).
    
    .. attribute:: domains

        Домены-алиасы для gridfs-serve.
    """
    collection = 'users'
    structure = {
        '_id': ObjectId,
        'name': basestring,
        'token': basestring,
        'needs': [tuple],
        'domains': [basestring],
    }
    required = ('token',)

    @classmethod
    def wrap_incoming(cls, data, db):
        # Восстановление tuple, который в Mongo хранится как список
        needs = data.get('needs', [])
        data['needs'] = [tuple(role) for role in needs]
        return super(User, cls).wrap_incoming(data, db)

    @property
    def provides(self):
        """ Возвращает полный список требований, реализуемых пользователем:

        * явные, хранящиеся в поле :attr:`needs`;
        * неявные, связанные с аутентификацией.

        Наличие этого свойства позволяет использовать объект :class:`User` в
        качестве "identity" для Flask-Principal, в т.ч. в `Permission.allows`.
        """
        implicit_needs = [
            RoleNeed(self.get_id())
        ]
        return implicit_needs + self.needs


class Template(ValidationMixin, modeling.Document):
    """Реализация сущности :term:`шаблон`.

    .. attribute:: user_id

        :class:`ObjectId` создателя шаблона.

    .. attribute:: applicable_for

        :term:`Семейство типов`, к которому применим шаблон.

    .. attribute:: action_list

        Список операций шаблона.
    """
    collection = 'templates'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'applicable_for': basestring,
        'action_list': list,
        'cleaned_action_list': list,
    }
    required = ('user_id', 'applicable_for', 'action_list')

    @classmethod
    def get_by_resource_uri(cls, db, template_uri):
        try:
            template_id = parse_template_uri(template_uri)
        except ValueError:
            return None

        return cls.get_one(db, {'_id': template_id})


class Statistics(ValidationMixin, modeling.Document):
    """Статистика, отражающая суммарный объем и количество файлов, появившихся в хранилище в
    конкретную дату.

    Файлы учитываются как залитые пользователем, так и полученные в результате операций,
    произведённых им.

    .. attribute:: user_id

        :class:`ObjectId` пользователя, для которого собирается статистика.
    
    .. attribute:: type_id

        :term:`Идентификатор контента` файлов, для которых собирается статистика.

    .. attribute:: timestamp

        :class:`datetime` начала дня, для которого собирается статистика, в формате UTC.

    .. attribute:: files_count

        Суммарное количество файлов.

    .. attribute:: files_size

        Cуммарный объём файлов в байтах.
    """
    collection = 'statistics.daily'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'type_id': ObjectId,
        'timestamp': datetime,
        'files_count': int,
        'files_size': int,
    }
    required = ['user_id', 'timestamp']

    @classmethod
    def aggregate_statistics(cls, db, group_by, conditions):
        """Агрегирует статистику, группируя по полям, указанным в `group_by`, и фильтруя по
        условиям, указанным в `conditions`.  После агрегации приводит `files_size` к мегабайтам, а
        `files_count` -- к целому числу.
        """
        return db[Statistics.collection].group(
            group_by,
            conditions,
            {'files_size': 0, 'files_count': 0},
            'function(entry, summary) {'
                'summary.files_size += entry.files_size;'
                'summary.files_count += entry.files_count;'
            '}',
            finalize='function(entry) {'
                'entry.files_size /= (1024 * 1024);'
                'entry.files_size = parseFloat(entry.files_size.toFixed(2));'
                'entry.files_count = parseInt(entry.files_count.toFixed(0));'
            '}'
        )

    @classmethod
    def _get_conditions(cls, user_id=None, type_id=None, start=None, end=None):
        conditions = {}
        
        if type_id:
            conditions['type_id'] = type_id
        if user_id:
            conditions['user_id'] = user_id

        timestamp_conditions = {}
        if start or end:
            if start:
                timestamp_conditions['$gte'] = start
            if end:
                timestamp_conditions['$lte'] = end
            conditions['timestamp'] = timestamp_conditions
        return conditions

    @classmethod
    def get_timely(cls, db, **kwargs):
        """Возвращает статистику, агрегированную по дням.

        Если `kwargs` содержит поле `type_id`, то статистика считается только для файлов, имеющих
        заданный :term:`идентификатор контента`; если `kwargs` содержит поле `user_id`, статистика
        считается по заданному пользователю. Если `kwargs` содержит поля `start` и/или `end`,
        агрегироваться будет статистика только между этими датами.
        
        :rtype: list({'user_id': ..., 'files_count': ..., 'files_size: ...})
        """
        conditions = cls._get_conditions(**kwargs)
        group_by = ['timestamp']
        if 'type_id' in kwargs:
            group_by.append('type_id')
        if 'user_id' in kwargs:
            group_by.append('user_id')
        return cls.aggregate_statistics(db, group_by, conditions)

    @classmethod
    def get_summary(cls, db, **kwargs):
        """Агрегирует всю доступную статистику. `kwargs` имеют то же значение,
        что и в :func:`get_timely`.

        :rtype: {'user_id': ..., 'files_count': ..., 'files_size: ...}
        """
        conditions = cls._get_conditions(**kwargs)
        group_by = []
        if 'type_id' in kwargs:
            group_by.append('type_id')
        if 'user_id' in kwargs:
            group_by.append('user_id')
        result = cls.aggregate_statistics(db, group_by, conditions)
        return result[0] if result else None


class ServableMixin(object):
    """Миксин, общий для файлов и ZIP-архивов. Предоставляет методы для конструирования URL-ов
    бинарного содержимого файла.
    """
    def get_binary_data_url(self, db, through_nginx_serve=False):
        """Возвращает URL бинарного содержимого файла, указывающий либо на gridfs-serve,
        либо, в случае, если `through_nginx_serve` равно `True`, на unistore-nginx-serve.
        """
        user = User.get_one(db, {'_id': self.user_id})
        base_url = user.domains and random.choice(user.domains) or settings.GRIDFS_SERVE_URL

        if not base_url.endswith('/'):
            base_url += '/'

        if through_nginx_serve:
            base_url = urljoin(base_url, '/uns/')

        file_id = str(self.get_id())
        return urljoin(base_url, file_id)

    def can_be_served_by_unistore_nginx_serve(self):
        """Возвращает True, если файл может быть отдан с помощью unistore-nginx-serve (например, в
        случае, если файл -- картинка, для которой заказан ресайз).
        """
        original_content_type = self.original_content_type
        actions = self.actions

        supported_types = ('image/gif', 'image/png', 'image/jpeg')
        if not original_content_type in supported_types or len(actions) > 1:
            return False
        
        action_name, action_args = actions[0]
        if action_name == 'resize':
            mode, w, h = action_args
            if mode in ('keep', 'crop'):
                return True
        elif action_name == 'rotate':
            return True

        return False


class File(ValidationMixin, ServableMixin, modeling.Document):
    """Реализация базовой сущности "файл" (см. :term:`временный файл` и :term:`обычный файл`).

    .. attribute:: user_id
    
        :class:`ObjectId` владельца файла.
    
    .. attribute:: type_id

        :term:`Идентификатор контента` файла.

    .. attribute:: extra

        Словарь с дополнительной информацией о файле (например, ширина и высота для картинки,
        кодек для видео и так далее).

    .. attribute:: original

        Если файл получен в результате применения операции, это поле содержит :class:`ObjectId`
        оригинального файла.

    .. attribute:: label

        Если файл получен в результате применения операции, это поле содержит идентификатор,
        уникальный среди всех файлов с тем же самым `original`.

    .. attribute:: filename

        Имя файла.

    .. attribute:: content_type

        MIME-type файла.

    .. attribute:: pending

        Является ли файл временным.
    """
    collection = 'fs.files'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'type_id': basestring,

        'extra': dict,
        'original': ObjectId,
        'modifications': dict,
        'label': basestring,
        'filename': basestring,
        'content_type': basestring,
        'unistorage_type': basestring,
        'pending': bool,
    }
    required = ('user_id', 'filename', 'content_type', 'unistorage_type')

    @classmethod
    def wrap_incoming(cls, data, db):
        """Выполняет преобразование Mongo- к Python-нотации (``contentType`` -> ``content_type``)
        для объектов, приходящих из базы данных."""
        data['content_type'] = data.pop('contentType', None)
        data['upload_date'] = data.pop('uploadDate', None)
        data['chunk_size'] = data.pop('chunkSize', None)

        extra = data.pop('extra', None)  # Workaround: избегаем валидации средствами monk
        result = super(File, cls).wrap_incoming(data, db)
        result.extra = extra

        return result

    @classmethod
    def put_to_fs(cls, db, fs, data, **kwargs):
        raise NotImplementedError

    @classmethod
    def get_from_fs(cls, db, fs, **kwargs):
        """Возвращает GridOut-инстанс, соответствующий указанным `kwargs`.

        :rtype: :class:`gridfs.GridOut`
        """
        return fs.get_version(**kwargs)


class ZipCollection(ValidationMixin, ServableMixin, modeling.Document):
    collection = 'zip_collections'
    structure = {
        '_id': ObjectId,
        'user_id': ObjectId,
        'file_ids': [ObjectId],
        'filename': basestring,
        'created_at': datetime.utcnow,
    }
    required = ['user_id', 'file_ids', 'filename', 'created_at']


class RegularFile(File):
    """Реализация модели :term:`обычный файл`. Наследуется от :class:`File`."""
    structure = dict(File.structure, **{
        'pending': False,
        'crc32': int
    })

    @classmethod
    def find(cls, *args, **kwargs):
        kwargs.update({'pending': False})
        return cls.find(*args, **kwargs)

    @classmethod
    def get_one(cls, *args, **kwargs):
        kwargs.update({'pending': False})
        return cls.get_one(*args, **kwargs)

    @classmethod
    def get_from_fs(cls, db, fs, **kwargs):
        kwargs.update({'pending': False})
        return super(RegularFile, cls).get_from_fs(db, fs, **kwargs)

    @classmethod
    def put_to_fs(cls, db, fs, file_name, file, **kwargs):
        """Обновляет поля `extra`, `content_type`, `filename` у kwargs, помещает `file` в GridFS
        и обновляет статистику.
        
        Обычные файлы должны помещаться в GridFS исключительно посредством этого метода.

        :param db: база данных
        :type db: pymongo.Connection
        :param fs: файловая система
        :type fs: gridfs.GridFS
        :param file: файл
        :type file: file-like object или :class:`werkzeug.datastructures.FileStorage`
        :param **kwargs: дополнительные параметры, которые станут атрибутами файла в GridFS
        """
        kwargs.update(file_utils.get_file_data(file, file_name))

        cls(**kwargs).validate()
        file_content = file.read()

        # Если файл большой, увеличиваем размер чанков:
        if len(file_content) > 30 * 1024 * 1024:
            kwargs.update({'chunkSize': 8 * 1024 * 1024})

        file_id = fs.put(file_content, **kwargs)

        db[Statistics.collection].update({
            'user_id': kwargs.get('user_id'),
            'type_id': kwargs.get('type_id'),
            'timestamp': get_today_utc_midnight(),
        }, {
            '$inc': {
                'files_count': 1,
                'files_size': fs.get(file_id).length,
            }
        }, upsert=True)
        return file_id


class PendingFile(File):
    """Реализация сущности :term:`временный файл`. Наследуется от :class:`File` и вводит следующие
    дополнительные атрибуты:

    .. attribute:: ttl

        Примерное время в секундах, через которое будут выполнены все `actions` и файл перестанет
        быть временным. FIXME -- new semantics

    .. attribute:: actions

        Список операций, применяемых к `original`.

    .. attribute:: original_content_type

       Денормализация для `original.content_type`.
    """
    structure = dict(File.structure, **{
        'pending': True,
        'ttl': int,
        'actions': list,
        'original_content_type': basestring,
    })
    required = ('user_id', 'actions', 'label', 'original', 'pending', 'ttl')

    @classmethod
    def find(cls, *args, **kwargs):
        kwargs.update({'pending': True})
        return super(PendingFile, cls).find(*args, **kwargs)

    @classmethod
    def get_one(cls, *args, **kwargs):
        kwargs.update({'pending': True})
        return super(PendingFile, cls).get_one(*args, **kwargs)

    @classmethod
    def get_from_fs(cls, db, fs, **kwargs):
        kwargs.update({'pending': True})
        return super(PendingFile, cls).get_from_fs(db, fs, **kwargs)

    @classmethod
    def put_to_fs(cls, db, fs, **kwargs):
        """Помещает :term:`временный файл` в GridFS. Временные файлы должны помещаться в GridFS
        исключительно посредством этого метода.
        """
        kwargs.update({'pending': True})
        cls(**kwargs).validate()
        return fs.put('', **kwargs)

    @classmethod
    def remove_from_fs(cls, db, fs, **kwargs):
        assert '_id' in kwargs
        if fs.exists(pending=True, **kwargs):
            fs.delete(kwargs['_id'])

    def move_to_updating(self, db, fs):
        """Перемещает временный файл в коллекцию обновляющихся временных файлов.
        (Вначале копирует временный файл, после чего удаляет оригинал.)
        """
        result = UpdatingPendingFile(self).save(db)
        PendingFile.remove_from_fs(db, fs, _id=self.get_id())
        return result


class UpdatingPendingFile(PendingFile):
    """Реализация сущности :term:`обновляющийся временный файл`.
    По сути, является :class:`PendingFile`, но хранится в отдельной коллекции.
    """
    collection = 'updating_pending_files'
    structure = dict(PendingFile.structure, **{
        # TODO Переместить эту структуру в :class:`File`?
        'upload_date': datetime,
        'length': int,
        'md5': basestring,
        'chunk_size': int,
    })
