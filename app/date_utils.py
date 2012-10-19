from datetime import datetime


def get_today_utc_midnight():
    return datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0)
