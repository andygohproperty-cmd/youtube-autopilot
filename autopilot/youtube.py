"""YouTube Data API v3: private upload, thumbnail, and scheduling after approval."""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from .config import Channel

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]


def _service(channel: Channel):
    creds = Credentials(
        token=None,
        refresh_token=os.environ[f"YT_REFRESH_TOKEN_{channel.secret_suffix}"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_private(channel: Channel, video: Path, thumb: Path | None, title: str,
                   description: str, tags: list[str], synthetic: bool) -> str:
    yt = _service(channel)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": channel.category_id,
            "defaultLanguage": channel.language,
            "defaultAudioLanguage": channel.language,
        },
        "status": {
            "privacyStatus": "private",          # nothing goes public until approved
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": synthetic,
            "embeddable": True,
        },
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(video), chunksize=8 << 20, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    video_id = resp["id"]
    thumb_set = False
    if thumb and not channel.is_short:
        try:
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumb))).execute()
            thumb_set = True
        except HttpError as e:
            # Custom thumbnails need a phone-verified channel; keep the upload anyway.
            print(f"Thumbnail not set ({e.reason}); YouTube will pick a frame.")
    return video_id, thumb_set


def next_slot(channel: Channel, taken: list[str]) -> datetime:
    """Earliest future publish time on a production day that no other video holds."""
    now = datetime.now(timezone.utc)
    day = now.replace(hour=channel.publish_hour_utc, minute=0, second=0, microsecond=0)
    if day <= now + timedelta(hours=1):
        day += timedelta(days=1)
    while True:
        if channel.produces_today(day) and day.isoformat() not in taken:
            return day
        day += timedelta(days=1)


def schedule(channel: Channel, video_id: str, publish_at: datetime, synthetic: bool) -> None:
    yt = _service(channel)
    yt.videos().update(part="status", body={
        "id": video_id,
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": synthetic,
        },
    }).execute()
