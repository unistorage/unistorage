from pymongo import Connection, ReplicaSetConnection
from redis import Redis

import settings


def get_mongodb_connection():
    if settings.MONGO_REPLICATION_ON:
        return ReplicaSetConnection(settings.MONGO_REPLICA_SET_URI,
                    replicaset=settings.MONGO_REPLICA_SET_NAME)
    else:
        return Connection(settings.MONGO_HOST, settings.MONGO_PORT)


def get_redis_connection():
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
