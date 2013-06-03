# coding: utf-8
from raven import Client
from raven.contrib.celery import register_signal
from kombu import Exchange, Queue

import settings


default_exchange = Exchange('unistorage', type='direct')

CELERY_QUEUES = (
    Queue('ha.unistorage.low-priority', default_exchange, routing_key='low-priority'),
    Queue('ha.unistorage.images', default_exchange, routing_key='images'),
    Queue('ha.unistorage.non-images', default_exchange, routing_key='non-images'),
)


class Router(object):
    def route_for_task(self, task, args=None, kwargs=None):
        is_low_priority = kwargs.get('low_priority')
        source_unistorage_type = kwargs.get('source_unistorage_type')

        assert is_low_priority or source_unistorage_type

        if is_low_priority:
            routing_key = 'low-priority'
        else:
            if source_unistorage_type == 'image':
                routing_key = 'images'
            else:
                routing_key = 'non-images'
        return {
            'exchange': 'unistorage',
            'exchange_type': 'direct',
            'routing_key': routing_key,
        }


CELERY_ROUTES = ('celeryconfig.Router',)

CELERY_IMPORTS = ('actions.tasks',)

# Пытаемся избавиться от зависания при перезапуске
CELERYD_FORCE_EXECV = True

# Важно, иначе Celery на каждый таск начнёт создавать новую очередь
CELERY_IGNORE_RESULT = True

# Включаем хартбиты, чтобы обнаруживать падение брокера
BROKER_HEARTBEAT = 60

# И включаем поддержку RabbitMQ-шных publisher confirms:
# `task.delay()` будет блокироваться до получения подтверждения от брокера,
# тем самым гарантируя, что таск не потеряется
BROKER_TRANSPORT_OPTIONS = {'block_for_ack': True}

# Формируем список URL-ов RabbitMQ. Если первый отпадёт, Celery
# будет пробовать подключаться к последующим
BROKER_URL = []
for host in settings.BROKER_HOSTS:
    # Важно использовать транспорт pyamqp, так как только он
    # поддерживает heartbears и publisher confirms
    broker_url = 'pyamqp://%s:%s@%s/%s' % \
        (settings.BROKER_USERNAME, settings.BROKER_PASSWORD,
         host, settings.BROKER_VHOST)
    BROKER_URL.append(broker_url)

# Подключаем логирование ошибок в Sentry
sentry_dsn = settings.SENTRY_DSN
if sentry_dsn:
    client = Client(sentry_dsn)
    register_signal(client)
