# -*- coding: utf-8 -*-
"""
Код, исполняемый воркерами python-rq
====================================
"""
import os.path
import logging

import gridfs
from bson.objectid import ObjectId

import settings
import actions
import connections
from app.models import PendingFile, RegularFile
from file_utils import get_content_type, convert_to_filename
from actions.utils import get_type_family


connection = connections.get_mongodb_connection()
db = connection[settings.MONGO_DB_NAME]
fs = gridfs.GridFS(db)


LOG_TEMPLATE = """
    Action failed!
    Source file id: %(source_id)s
    Target file id: %(target_id)s
    Action: %(action)s
    Action arguments: %(action_args)s
    Exception type: %(exception_type)s
    Exception message: %(exception_msg)s
"""


def resolve_object_ids(args):
    """Проходит по списку `args`, заменяя встреченные `ObjectId` на соответствующие им
    GridOut-объекты."""
    def try_resolve(arg):
        if isinstance(arg, ObjectId):
            return fs.get(arg)
        else:
            return arg
    return [try_resolve(arg) for arg in args]


def perform_actions(source_id, target_id, target_kwargs):
    """Проверяет существование обычного файла с идентификатором `source_id` и временного с
    идентификатором `target_id`. Последовательно применяет к обычному файлу операции, записанные
    в поле `actions` временного файла; удаляёт файл с `target_id` и записывает на его место
    результат последней операции.

    :param source_id: идентификатор исходного файла (файл должен быть обычным)
    :type source_id: :class:`ObjectId`
    :param target_id: идентификатор результирующего файла (файл должен быть временным)
    :type target_id: :class:`ObjectId`
    :param target_kwargs: атрибуты, которые появятся у результирующего файла после применения операций
    :type target_kwargs: dict
    """
    source_file = RegularFile.get_from_fs(db, fs, _id=source_id)
    # Исключительно для проверки существования временного файла с _id=target_id:
    target_file = PendingFile.get_from_fs(db, fs, _id=target_id)

    source_file_name, source_file_ext = os.path.splitext(source_file.name)

    curr_file = source_file
    curr_file_name = source_file_name
    curr_file_ext = source_file_ext
    curr_content_type = curr_file.content_type

    for action_name, action_args in target_file.actions:
        type_family = get_type_family(curr_content_type)
        action = actions.get_action(type_family, action_name)
        action_args = resolve_object_ids(action_args)
        
        try:
            next_file, next_file_ext = action.perform(curr_file, *action_args)
        except Exception as e:
            logging.getLogger('action_error_logger').error(LOG_TEMPLATE % {
                'source_id': source_id,
                'target_id': target_id,
                'action': action,
                'action_args': action_args,
                'exception_type': type(e),
                'exception_msg': e
            })
            return
        finally:
            curr_file.close()

        curr_file = next_file
        curr_file_ext = next_file_ext
        curr_content_type = get_content_type(curr_file)

    target_file = curr_file
    target_file_name = '%s_%s' % (source_file_name, target_kwargs['label'])
    target_file.name = convert_to_filename('%s.%s' % (target_file_name, curr_file_ext))
    
    PendingFile.remove_from_fs(db, fs, _id=target_id)
    RegularFile.put_to_fs(db, fs, target_file, _id=target_id, **target_kwargs)
    target_file.close()
