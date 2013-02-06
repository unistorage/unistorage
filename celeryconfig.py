import settings


BROKER_URL = settings.CELERY_BROKER

CELERY_IMPORTS = ('actions.tasks',)

ADMINS = [('Anton Romanovich', 'anthony.romanovich@gmail.com')]

CELERY_SEND_TASK_ERROR_EMAILS = True
