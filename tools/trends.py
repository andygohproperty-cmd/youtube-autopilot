"""What's hot right now: the most-viewed recent videos for a set of searches, plus YouTube's trending chart.

  python tools/trends.py 30 "how * makes money" "business explained"   (days back, then queries)
Prints one line per video, most views first. Used to pick topics, never to copy content."""
import os
import sys
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

days, queries = int(sys.argv[1]), sys.argv[2:]
creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN_BIZ"],
                    client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                    token_uri="https://oauth2.googleapis.com/token")
creds.refresh(Request())
yt = build("youtube", "v3", credentials=creds)
since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def details(ids):
    if not ids:
        return []
    return yt.videos().list(id=",".join(ids), part="snippet,statistics,contentDetails").execute()["items"]


def show(label, items):
    print(f"\n===== {label}")
    for v in sorted(items, key=lambda v: -int(v["statistics"].get("viewCount", 0))):
        print(f'{int(v["statistics"].get("viewCount", 0)):>11,} | {v["contentDetails"]["duration"]:>9} | '
              f'{v["snippet"]["publishedAt"][:10]} | {v["snippet"]["channelTitle"][:24]} | {v["snippet"]["title"]}')


for q in queries:
    ids = [i["id"]["videoId"] for i in yt.search().list(q=q, part="id", type="video", order="viewCount", maxResults=15,
                                                         publishedAfter=since, relevanceLanguage="en").execute()["items"]]
    show(f"{q} (last {days} days)", details(ids))
for cat, name in [("27", "Education"), ("25", "News"), ("28", "Science & Tech"), ("24", "Entertainment")]:
    try:
        show(f"Trending now US: {name}", yt.videos().list(chart="mostPopular", regionCode="US", videoCategoryId=cat,
                                                          part="snippet,statistics,contentDetails", maxResults=15).execute()["items"])
    except Exception as e:  # noqa: BLE001  (some categories have no chart)
        print(f"\n===== Trending {name}: unavailable ({str(e)[:80]})")
