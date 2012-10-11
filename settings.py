import sys
import os
import logging.config
from datetime import timedelta

import yaml


PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

DEBUG = False
SECRET_KEY = 'qwertyuiop[]'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin' # Should we put md5 here?

#Mongo
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'grid_fs'

MONGO_REPLICATION_ON = True
MONGO_REPLICA_SET_URI = 'localhost:27017,localhost:27018'
MONGO_REPLICA_SET_NAME = 'grid_fs_set'

CELERY_BROKER = 'mongodb://localhost:27017/q/'

# ImageMagick binaries
CONVERT_BIN = '/usr/bin/convert'
IDENTIFY_BIN = '/usr/bin/identify'
COMPOSITE_BIN = '/usr/bin/composite'

# FFMpeg binaries
FFMPEG_BIN = '/usr/bin/ffmpeg'
FFPROBE_BIN = '/usr/bin/ffprobe'

# Other binaries
OO_WRAPPER_BIN = 'oowrapper.py'
FLVTOOL_BIN = '/usr/bin/flvtool2'

MAGIC_PATH = '/etc/magic:/usr/share/misc/magic' # Check your `file --version`

GRIDFS_SERVE_URL = 'http://127.0.0.1'
UNISTORE_NGINX_SERVE_URL = 'http://127.0.0.1/uns'

TTL = int(timedelta(days=7).total_seconds())
AVERAGE_TASK_TIME = timedelta(seconds=60)

ZIP_COLLECTION_TTL = timedelta(days=1)

try:
    from settings_local import *
except ImportError:
    pass

if 'test' in sys.argv[0]: # Is there another way?
    try:
        from settings_test import *
    except ImportError:
        pass

logging_conf_path = os.path.join(PROJECT_PATH, 'logging.conf')
config = yaml.load(open(logging_conf_path))
logging.config.dictConfig(config)
