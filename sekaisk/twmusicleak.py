import datetime
import json
from datetime import timezone, timedelta

def twmusicleak():
    now = datetime.datetime.now()
    end_days = now + datetime.timedelta(days=30)
    now_timestamp = int(now.timestamp() * 1000)
    end_days_timestamp = int(end_days.timestamp() * 1000)

    with open('./twmasterdata/musics.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    musiclist = []
    for musicinfo in data:
        if now_timestamp < musicinfo['releasedAt'] < end_days_timestamp:
            published_at_utc = datetime.datetime.fromtimestamp(musicinfo['publishedAt'] / 1000, timezone.utc)
            published_at_beijing = published_at_utc.astimezone(timezone(timedelta(hours=8)))
            musiclist.append({
                'name': musicinfo['title'],
                'publishtime': published_at_beijing.strftime('%Y-%m-%d %H:%M:%S'),
                'composer': musicinfo['composer']
            })
    return musiclist