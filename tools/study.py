"""Study top-viewed YouTube videos on a topic: titles, views, durations and transcripts.

Used to learn structure (hook, beats, pacing). Transcripts are for analysis only and are
never reused in scripts.  python tools/study.py "how costco makes money" out.json
"""
import json
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

query, dest = sys.argv[1], sys.argv[2]
creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN_BIZ"],
                    client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                    token_uri="https://oauth2.googleapis.com/token")
creds.refresh(Request())
yt = build("youtube", "v3", credentials=creds)
ids = [i["id"]["videoId"] for i in yt.search().list(q=query, part="id", type="video", order="viewCount",
                                                     maxResults=15, relevanceLanguage="en").execute()["items"]]
info = yt.videos().list(id=",".join(ids), part="snippet,statistics,contentDetails").execute()["items"]
out = []
for v in info:
    rec = {"id": v["id"], "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
           "views": int(v["statistics"].get("viewCount", 0)), "duration": v["contentDetails"]["duration"],
           "published": v["snippet"]["publishedAt"]}
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        tr = YouTubeTranscriptApi().fetch(v["id"], languages=["en"])
        rec["transcript"] = [{"t": round(s.start, 1), "text": s.text} for s in tr]
    except Exception as e:  # noqa: BLE001
        rec["transcript_error"] = str(e)[:200]
    out.append(rec)
    print(rec["views"], rec["duration"], rec["channel"], "|", rec["title"], "| transcript:", "transcript" in rec)
json.dump(out, open(dest, "w"), indent=1)
