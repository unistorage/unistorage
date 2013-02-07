# coding: utf-8
from pymongo import MongoClient, MongoReplicaSetClient

import settings


def get_mongodb_connection():
    if settings.MONGO_REPLICATION_ON:
        return MongoReplicaSetClient(
            settings.MONGO_REPLICA_SET_URI,
            replicaset=settings.MONGO_REPLICA_SET_NAME, w=1)
    else:
        return MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)


class MongoDBConnection(object):
    def __enter__(self):
        self.connection = get_mongodb_connection()
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()
