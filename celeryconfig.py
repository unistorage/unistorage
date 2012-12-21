import settings

# Broker settings.
BROKER_URL = settings.CELERY_BROKER

# List of modules to import when celery starts.
CELERY_IMPORTS = ('actions.tasks',)

ADMINS = ('Anton Romanovich', 'anthony.romanovich@gmail.com')

CELERY_SEND_TASK_ERROR_EMAILS = True
