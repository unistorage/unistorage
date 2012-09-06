import os.path
import logging

import gridfs
from pymongo import Connection, ReplicaSetConnection

import settings
from connections import get_mongodb_connection
from fileutils import get_file_data, get_content_type, convert_to_filename
from actions import get_action, ActionException
from actions.utils import get_type_family


connection = get_mongodb_connection()
fs = gridfs.GridFS(connection[settings.MONGO_DB_NAME])


LOG_TEMPLATE = '''
    Action failed!
    Source file id: %(source_id)s
    Target file id: %(target_id)s
    Action: %(action)s
    Action arguments: %(action_args)s
    Exception type: %(exception_type)s
    Exception message: %(exception_msg)s
'''


def perform_action_list(source_id, target_id, target_kwargs, action_list):
    source_file = fs.get(source_id)
    source_file_name, source_file_ext = os.path.splitext(source_file.name)

    curr_file = source_file
    curr_file_name, curr_file_ext = source_file_name, source_file_ext

    for action_name, action_args in action_list:
        content_type = hasattr(curr_file, 'content_type') and curr_file.content_type \
                or get_content_type(curr_file)
        type_family = get_type_family(content_type)
        action = get_action(type_family, action_name)

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

        curr_file, curr_file_ext = next_file, next_file_ext

    target_file = curr_file
    target_file_name = '%s_%s' % (source_file_name, target_kwargs['label'])
    target_file_ext = curr_file_ext

    target_file.filename = target_file.name = \
            convert_to_filename('%s.%s' % (target_file_name, target_file_ext))
    target_kwargs.update(get_file_data(target_file))

    fs.delete(target_id)
    fs.put(target_file, _id=target_id, **target_kwargs)
    target_file.close()
