"""Weekly performance report per channel from the YouTube Analytics API.

Writes data/analytics/<channel>.json for the script writer: per-video views, average % viewed,
CTR where YouTube reports it, and where viewers drop off. Needs the refresh token to include the
yt-analytics.readonly scope (see SETUP.md step 4).   python -m autopilot.analytics
"""
import json
import os
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import DATA_DIR, all_channels, history

DAYS = 28
BASE_METRICS = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,subscribersGained"
CTR_METRICS = "videoThumbnailImpressions,videoThumbnailImpressionsClickRate"


def _creds(channel) -> Credentials | None:
    token = os.environ.get(f"YT_REFRESH_TOKEN_{channel.secret_suffix}")
    if not token:
        return None
    creds = Credentials(None, refresh_token=token, client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token")
    creds.refresh(Request())
    return creds


def _rows(resp: dict) -> list[dict]:
    names = [h["name"] for h in resp.get("columnHeaders", [])]
    return [dict(zip(names, r)) for r in resp.get("rows", [])]


def _query(api, **kw) -> list[dict]:
    return _rows(api.reports().query(ids="channel==MINE", **kw).execute())


def _drop_off(api, video_id: str, start: str, end: str) -> dict:
    """Share of viewers still watching at 10%, 25%, 50%, 75% and 95% of the video."""
    curve = _query(api, startDate=start, endDate=end, metrics="audienceWatchRatio",
                   dimensions="elapsedVideoTimeRatio", filters=f"video=={video_id}")
    points = {round(r["elapsedVideoTimeRatio"], 2): r["audienceWatchRatio"] for r in curve}
    out = {}
    for mark in (0.1, 0.25, 0.5, 0.75, 0.95):
        near = min(points, key=lambda p: abs(p - mark), default=None)
        if near is not None:
            out[f"{int(mark * 100)}%"] = round(points[near], 2)
    return out


def report(channel) -> dict:
    creds = _creds(channel)
    if creds is None:
        return {"error": f"secret YT_REFRESH_TOKEN_{channel.secret_suffix} not set"}
    api = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=DAYS)).isoformat()
    try:
        try:
            videos = _query(api, startDate=start, endDate=end, metrics=f"{BASE_METRICS},{CTR_METRICS}",
                            dimensions="video", sort="-views", maxResults=50)
        except HttpError:
            # CTR metrics are not offered for every channel; fall back without them.
            videos = _query(api, startDate=start, endDate=end, metrics=BASE_METRICS,
                            dimensions="video", sort="-views", maxResults=50)
        sources = _query(api, startDate=start, endDate=end, metrics="views",
                         dimensions="insightTrafficSourceType", sort="-views")
        for v in videos[:10]:
            v["retention"] = _drop_off(api, v["video"], start, end)
    except HttpError as e:
        if e.resp.status in (401, 403):
            return {"error": "refresh token lacks the yt-analytics.readonly scope or the YouTube "
                             "Analytics API is not enabled; see SETUP.md step 4"}
        raise
    titles = {h["video_id"]: h["title"] for h in history(channel.id) if h.get("video_id")}
    for v in videos:
        v["title"] = titles.get(v["video"], "")
    return {"window": f"{start}..{end}", "videos": videos, "traffic_sources": sources}


def main() -> None:
    out_dir = DATA_DIR / "analytics"
    out_dir.mkdir(parents=True, exist_ok=True)
    for channel in all_channels():
        rep = {"channel": channel.id, "generated": date.today().isoformat(), **report(channel)}
        (out_dir / f"{channel.id}.json").write_text(json.dumps(rep, indent=1))
        print(channel.id, rep.get("error") or f"{len(rep['videos'])} videos")


if __name__ == "__main__":
    main()
