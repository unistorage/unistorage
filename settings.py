# -*- coding: utf-8 -*-
import sys
import os
import logging.config
from datetime import timedelta

import yaml


PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))


DEBUG = False
SECRET_KEY = 'qwertyuiop[]'
ADMINS = ['anthony.romanovich@gmail.com']


# Логин и пароль от интерфейса администратора (/admin/)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'  # Should we put md5 here?


# Настройки доступа к Mongo
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'grid_fs'

MONGO_REPLICATION_ON = True
# Следующие две настройки используются только при MONGO_REPLICATION_ON = True
MONGO_REPLICA_SET_URI = 'localhost:27017,localhost:27018'
MONGO_REPLICA_SET_NAME = 'grid_fs_set'

CELERY_BROKER = 'mongodb://localhost:27017/q/'


# Бинарники ImageMagick
CONVERT_BIN = '/usr/bin/convert'
IDENTIFY_BIN = '/usr/bin/identify'
COMPOSITE_BIN = '/usr/bin/composite'


# Бинарники avconv
AVCONV_BIN = '/usr/bin/avconv'
AVPROBE_BIN = '/usr/bin/avprobe'


# Остальные бинарники
OO_WRAPPER_BIN = 'oowrapper.py'
FLVTOOL_BIN = '/usr/bin/flvtool2'


# Пути к gridfs-serve и unistore-nginx-serve
GRIDFS_SERVE_URL = 'http://127.0.0.1'
UNISTORE_NGINX_SERVE_URL = 'http://127.0.0.1/uns'


TTL = int(timedelta(days=7).total_seconds())  # TTL ответов со статусом "ok"
AVERAGE_TASK_TIME = timedelta(seconds=60)  # TTL ответов со статусом "wait"
ZIP_COLLECTION_TTL = timedelta(days=1)  # TTL ZIP-коллекций


MAGIC_FILE_PATH = ':'.join((
    os.path.join(PROJECT_PATH, 'magic.mgc'),
    # System-wide базы данных libmagic (можно узнать, сказав `file --version`):
    '/etc/magic',
    '/usr/share/misc/magic',
))


logging_conf_path = os.path.join(PROJECT_PATH, 'logging.conf')
config = yaml.load(open(logging_conf_path))
config['handlers']['mail']['toaddrs'] = ADMINS

logging.config.dictConfig(config)


try:
    from settings_local import *
except ImportError:
    pass


if 'test' in sys.argv[0]:
    try:
        from settings_test import *
    except ImportError:
        pass
