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

SENTRY_DSN = ''

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

CELERY_BROKER = 'mongodb://localhost:27017,localhost:27018/q/#grid_fs_set'

# Бинарники ImageMagick
CONVERT_BIN = '/usr/bin/convert'
IDENTIFY_BIN = '/usr/bin/identify'
COMPOSITE_BIN = '/usr/bin/composite'


# Бинарники avconv
AVCONV_BIN = '/usr/bin/ffmpeg'
AVPROBE_BIN = '/usr/bin/ffprobe'
QT_FASTSTART_BIN = '/usr/bin/qt-faststart'


# Остальные бинарники
OO_WRAPPER_BIN = 'oowrapper.py'
FLVTOOL_BIN = '/usr/bin/flvtool2'


# Путь к gridfs-serve
GRIDFS_SERVE_URL = 'http://127.0.0.1/'


TTL = int(timedelta(days=7).total_seconds())  # TTL ответов со статусом "ok"
AVERAGE_TASK_TIME = timedelta(seconds=60)  # TTL ответов со статусом "wait"
ZIP_COLLECTION_TTL = timedelta(days=1)  # TTL ZIP-коллекций

MAGIC_DB_PATH = os.path.join(PROJECT_PATH, 'magic.mgc')

MAGIC_FILE_PATH = ':'.join((
    MAGIC_DB_PATH,
    # System-wide базы данных libmagic (можно узнать, сказав `file --version`):
    '/etc/magic',
    '/usr/share/misc/magic',
))

AVCONV_DB_PATH = os.path.join(PROJECT_PATH, 'avconv.db')


try:
    from settings_local import *
except ImportError:
    pass


test_commands = ('nosetests', 'test_quick', 'test_cov', 'test')
if any([command in sys.argv for command in test_commands]) or \
        os.environ.get('UNISTORAGE_TESTING'):
    try:
        from settings_test import *
    except ImportError:
        pass


if SENTRY_DSN:
    from raven.conf import setup_logging
    from raven.handlers.logging import SentryHandler
    handler = SentryHandler(SENTRY_DSN)
    setup_logging(handler)
