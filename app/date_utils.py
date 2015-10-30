from datetime import datetime


def get_today_utc_midnight(now=None):
    if not now:
        now = datetime.utcnow()
    return now.replace(
        hour=0, minute=0, second=0, microsecond=0)
