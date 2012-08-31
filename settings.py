import sys
from datetime import timedelta

DEBUG = False

#Mongo
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'grid_fs'

MONGO_DB_REPL_ON = True
MONGO_DB_REPL_URI = 'localhost:27017,localhost:27018'
MONGO_REPLICA_NAME = 'test_set'

CONVERT_BIN = '/usr/bin/convert'
OPENOFFICE_BIN = '/usr/bin/libreoffice'
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
