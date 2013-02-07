from raven import Client
from raven.contrib.celery import register_signal

import settings


BROKER_URL = settings.CELERY_BROKER

CELERY_IMPORTS = ('actions.tasks',)

ADMINS = [('Anton Romanovich', 'anthony.romanovich@gmail.com')]

# CELERY_SEND_TASK_ERROR_EMAILS = True ?

sentry_dsn = getattr(settings, 'SENTRY_DSN', False)
if sentry_dsn:
    client = Client(sentry_dsn)
    register_signal(client)
