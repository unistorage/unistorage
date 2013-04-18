# coding: utf-8
from datetime import datetime, timedelta

import settings
import connections
from app import db
from app.models import ZipCollection


def expire_zip_collections():
    """Removes all zip collections older than `settings.ZIP_COLLECTION_TTL`."""
    # Flask-Script неявно пушит application context, поэтому мы можем использовать db
    db[ZipCollection.collection].remove({
        'created_at': {
            '$lt': datetime.utcnow() - timedelta(seconds=settings.ZIP_COLLECTION_TTL),
        },
    })
