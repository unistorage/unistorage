import settings

# Broker settings.
BROKER_URL = settings.CELERY_BROKER

# List of modules to import when celery starts.
CELERY_IMPORTS = ('actions.tasks',)
