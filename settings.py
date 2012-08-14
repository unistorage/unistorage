DEBUG = False

#Mongo
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'test_base'

MONGO_DB_REPL_ON = True
MONGO_DB_REPL_URI = 'localhost:27017,localhost:27018'
MONGO_REPLICA_NAME = 'test_set'

#gridfs-server
GFS_HOST = '127.0.0.1'
GFS_PORT = 80

try:
    from settings_local import *
except ImportError:
    pass
