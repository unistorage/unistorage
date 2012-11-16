# -*- coding: utf-8 -*-
from pymongo import Connection, ReplicaSetConnection

import settings


def get_mongodb_connection():
    # TODO Решить, необходимо ли использование safe=True
    # http://api.mongodb.org/python/current/api/pymongo/collection.html?highlight=lasterror#pymongo.collection.Collection.safe
    # http://www.mongodb.org/display/DOCS/getLastError+Command
    if settings.MONGO_REPLICATION_ON:
        return ReplicaSetConnection(
            settings.MONGO_REPLICA_SET_URI,
            replicaset=settings.MONGO_REPLICA_SET_NAME, safe=True)
    else:
        return Connection(settings.MONGO_HOST, settings.MONGO_PORT, safe=True)


class MongoDBConnection(object):
    def __enter__(self):
        self.connection = get_mongodb_connection()
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()
