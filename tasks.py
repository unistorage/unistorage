import os.path

import gridfs
from pymongo import Connection, ReplicaSetConnection

import settings
from fileutils import get_file_data, convert_to_filename


def perform_action(source_id, target_id, action, args):
    """
    Performs `action` on `source_id` and writes result to `target_id`.
    Arguments:
    source_id, target_id -- ObjectIds;
    action -- callable, must take `source_file` and unpacked `args`
    """
    from app import get_mongodb_connection
    connection = get_mongodb_connection()
    fs = gridfs.GridFS(connection[settings.MONGO_DB_NAME])

    source_file = fs.get(source_id)
    target_file = action(source_file, *args)
    
    ## Pretend that `target_file` is the GridOut instance:
    ## `name` needed for kaa.metadata, `filename` needed for `fs.put` kwargs
    name, ext = os.path.splitext(source_file.name)
    label = '_'.join(map(str, args))
    target_file.filename = target_file.name = '%s_%s%s' % (name, label, ext)
    file_data = get_file_data(target_file)

    fs.delete(target_id)
    fs.put(target_file, _id=target_id, **file_data)
