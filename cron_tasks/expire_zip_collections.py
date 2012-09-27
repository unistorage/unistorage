from datetime import datetime

import connections
import settings
from app.models import ZipCollection


db_connection = connections.get_mongodb_connection()
db = db_connection[settings.MONGO_DB_NAME]

db[ZipCollection.collection].remove({
    'created_at': {'$lt': datetime.utcnow() - settings.ZIP_COLLECTION_TTL}
})
