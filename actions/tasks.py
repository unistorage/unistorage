# coding: utf-8
"""
Код, исполняемый воркерами
==========================
"""
import os.path

import gridfs
from celery import Celery
from bson.objectid import ObjectId

import settings
import actions
import connections
from file_utils import get_file_data
from app.models import PendingFile, UpdatingPendingFile, RegularFile


celery = Celery('tasks')


def resolve_object_ids(fs, args):
    """Проходит по списку `args`, заменяя встреченные `ObjectId` на соответствующие им
    GridOut-объекты.
    """
    def try_resolve(arg):
        if isinstance(arg, ObjectId):
            return fs.get(arg)
        else:
            return arg
    return [try_resolve(arg) for arg in args]


@celery.task
def perform_actions(target_id):
    """Проверяет существование исходного обычного файла с идентификатором `source_id` и временного с
    идентификатором `target_id`. Последовательно применяет к исходному файлу операции, записанные
    в поле `actions` временного файла; удаляёт файл с `target_id` и записывает на его место
    результат последней операции.

    :param source_id: :class:`ObjectId` исходного файла (файл должен быть обычным)
    :param target_id: :class:`ObjectId` результирующего файла (файл должен быть временным)
    :param target_kwargs: словарь с атрибутами, которые появятся у результирующего файла после
    применения операций
    """
    connection = connections.get_mongodb_connection()
    db = connection[settings.MONGO_DB_NAME]
    fs = gridfs.GridFS(db)

    target_file = PendingFile.get_from_fs(db, fs, _id=target_id)
    source_id = target_file.original
    source_file = RegularFile.get_from_fs(db, fs, _id=source_id)

    source_file_name, source_file_ext = os.path.splitext(source_file.name)

    curr_file = source_file
    curr_file_ext = source_file_ext
    curr_unistorage_type = source_file.unistorage_type

    for action_name, action_args in target_file.actions:
        action = actions.get_action(curr_unistorage_type, action_name)
        action_args = resolve_object_ids(fs, action_args)
        
        try:
            next_file, next_file_ext = action.perform(curr_file, *action_args)
        finally:
            curr_file.close()

        curr_file = next_file
        curr_file_ext = next_file_ext

        data = get_file_data(curr_file, file_name=source_file_name + curr_file_ext)
        curr_unistorage_type = data['unistorage_type']

    result_file = curr_file
    result_file_name = '%s_%s.%s' % (source_file_name, target_file.label, curr_file_ext)
    # Необходимо обеспечить "атомарность" операции "удалить временный файл и
    # записать результат в обычный файл". Для этого операция производится как
    # "скопировать временный файл в отдельную коллекцию, удалить оригинальный
    # временный файл, записать обычный файл". 
    updating_pending_file_id = \
        PendingFile.get_one(db, {'_id': target_id}).move_to_updating(db, fs)
    kwargs = {
        'user_id': target_file.user_id,
        'type_id': target_file.type_id,
        'original': target_file.original,
        'label': target_file.label,
        'actions': target_file.actions,
    }
    
    # Если операция применяется к временному файлу, который ранее был постоянным
    # (такое случается при переделывании операций), нам необходимо сохранить
    # словарь с модификациями
    modifications = getattr(target_file, 'modifications', None)
    if modifications:
        kwargs['modifications'] = modifications

    RegularFile.put_to_fs(db, fs, result_file_name, result_file, _id=target_id, **kwargs)
    UpdatingPendingFile.get_one(db, {'_id': updating_pending_file_id}).remove(db)
    result_file.close()
