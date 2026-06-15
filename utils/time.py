from datetime import datetime, timedelta

def parse_news_time(occurrence_time):
    return datetime.fromisoformat(occurrence_time.replace("Z", "+00:00"))

def get_window(news_time):
    return {
        "before_15m": news_time - timedelta(minutes=15),
        "after_1h": news_time + timedelta(hours=1),
    }