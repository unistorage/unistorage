import os.path

import gridfs
import requests
from bson.objectid import ObjectId
from pymongo import Connection, ReplicaSetConnection
from PIL import Image

import settings
from app import get_mongodb_connection
from fileutils import get_file_data, convert_to_filename
from imageutils import resize


connection = get_mongodb_connection()
fs = gridfs.GridFS(connection[settings.MONGO_DB_NAME])

def resize_task(source_id, target_id, mode='keep', w=None, h=None):
    source_file = fs.get(source_id)
    resized_image = resize(source_file, mode, w, h)
    
    name, ext = os.path.splitext(source_file.name)
    # Pretend that `resized_image` is the GridOut instance:
    # `name` needed for kaa.metadata, `filename` needed for `fs.put` kwargs
    resized_image.filename = resized_image.name = \
            '{0}_{2}x{3}_{4}{1}'.format(name, ext, w, h, mode)
    file_data = get_file_data(resized_image)

    fs.delete(target_id)
    target_file = fs.put(resized_image, _id=target_id, **file_data)
