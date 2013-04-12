# coding: utf-8
from raven import Client
from raven.contrib.celery import register_signal

import settings


CELERY_IMPORTS = ('actions.tasks',)

# Важно, иначе Celery на каждый таск начнёт создавать новую очередь
CELERY_IGNORE_RESULT = True

# Очередь для сообщений
CELERY_DEFAULT_QUEUE = 'ha.unistorage'

# Включаем хартбиты, чтобы обнаруживать падение брокера
BROKER_HEARTBEAT = 10

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
