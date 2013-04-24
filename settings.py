# coding: utf-8
import sys
import os
import logging.config
from datetime import timedelta

import yaml


PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))


DEBUG = False
TESTING = False
SECRET_KEY = 'qwertyuiop[]'
ADMINS = ['anthony.romanovich@gmail.com']

SERVER_NAME = 'locahost'
SENTRY_DSN = ''

# Логин и пароль от интерфейса администратора (/admin/)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'  # Should we put md5 here?

MONGO_REPLICATION_ON = True

# Настройки доступа к Mongo
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'grid_fs'

# Следующие две настройки используются только при MONGO_REPLICATION_ON = True
MONGO_REPLICA_SET_URI = 'localhost:27017,localhost:27018'
MONGO_REPLICA_SET_NAME = 'grid_fs_set'

# Настройки брокера сообщений
BROKER_HOSTS = []  # Например, ['localhost:5672']
BROKER_USERNAME = ''
BROKER_PASSWORD = ''
BROKER_VHOST = ''

# Бинарники ImageMagick
CONVERT_BIN = '/usr/bin/convert'
IDENTIFY_BIN = '/usr/bin/identify'
COMPOSITE_BIN = '/usr/bin/composite'

# Бинарники avconv
AVCONV_BIN = '/usr/bin/ffmpeg'
AVPROBE_BIN = '/usr/bin/ffprobe'

# Остальные бинарники
OO_WRAPPER_BIN = '/bin/oowrapper.py'
FLVTOOL_BIN = '/usr/bin/flvtool2'

# Путь к gridfs-serve
GRIDFS_SERVE_URL = 'http://127.0.0.1/'

to_seconds = lambda td: int(td.total_seconds())
# TTL ответов со статусом "ok":
TTL = to_seconds(timedelta(days=7))
# Плюс-минус разброс для `TTL`
TTL_DEVIATION = to_seconds(timedelta(days=1))
# TTL ответов со статусом "wait"
AVERAGE_TASK_TIME = to_seconds(timedelta(seconds=60))
# TTL ZIP-коллекций
ZIP_COLLECTION_TTL = to_seconds(timedelta(days=1))

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
