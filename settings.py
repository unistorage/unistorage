import sys
from datetime import timedelta

DEBUG = False

#Mongo
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'grid_fs'
MONGO_USERS_DB = 'users'
MONGO_TEMPLATES_DB = 'templates'

MONGO_REPLICATION_ON = True
MONGO_REPLICA_SET_URI = 'localhost:27017,localhost:27018'
MONGO_REPLICA_SET_NAME = 'grid_fs_set'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

CONVERT_BIN = '/usr/bin/convert'
OO_WRAPPER_BIN = 'oowrapper.py'
FFMPEG_BIN = '/usr/bin/ffmpeg'
FFPROBE_BIN = '/usr/bin/ffprobe'
FLVTOOL_BIN = '/usr/bin/flvtool2'

MAGIC_PATH = '/etc/magic:/usr/share/misc/magic' # Check your `file --version`

GRIDFS_SERVE_URL = 'http://127.0.0.1'
UNISTORE_NGINX_SERVE_URL = 'http://127.0.0.1/uns'

TTL = int(timedelta(days=7).total_seconds())
AVERAGE_TASK_TIME = timedelta(seconds=5)

try:
    from settings_local import *
except ImportError:
    pass

if 'test' in sys.argv[0]: # Is there another way?
    try:
        from settings_test import *
    except ImportError:
        pass
