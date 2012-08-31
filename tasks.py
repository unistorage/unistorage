import os.path

import gridfs
from pymongo import Connection, ReplicaSetConnection

import settings
from app import get_mongodb_connection
from fileutils import get_file_data, convert_to_filename


connection = get_mongodb_connection()
fs = gridfs.GridFS(connection[settings.MONGO_DB_NAME])


def perform_action(source_id, target_id, target_kwargs, action, args):
    """Performs `action` on `source_id` and writes result to `target_id`.
    Arguments:
    source_id, target_id -- ObjectIds;
    action -- callable, must take `source_file` and unpacked `args`
    """
    source_file = fs.get(source_id)
    target_file, target_file_ext = action(source_file, *args)
    
    ## Pretend that `target_file` is the GridOut instance:
    ## `name` needed for kaa.metadata, `filename` needed for `fs.put` kwargs
    source_file_name, _ = os.path.splitext(source_file.name)
    label = target_kwargs['label']
    target_file.filename = target_file.name = \
            convert_to_filename('%s_%s.%s' % (source_file_name, label, target_file_ext))
    target_kwargs.update(get_file_data(target_file))

    fs.delete(target_id)
    fs.put(target_file, _id=target_id, **target_kwargs)
 
    source_file.close()
    target_file.close()
