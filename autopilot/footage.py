"""Free stock footage from Pexels (primary) and Pixabay (backup)."""
import os
from pathlib import Path

import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "")


def _pexels(query: str, portrait: bool) -> list[dict]:
    if not PEXELS_KEY:
        return []
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "per_page": 15, "orientation": "portrait" if portrait else "landscape"},
        timeout=30,
    )
    r.raise_for_status()
    out = []
    for v in r.json().get("videos", []):
        files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width")]
        if not files:
            continue
        # Smallest file that is still at least HD on its short side.
        hd = [f for f in files if min(f["width"], f["height"]) >= 1080] or files
        best = min(hd, key=lambda f: f["width"] * f["height"])
        out.append({"id": f"pexels-{v['id']}", "url": best["link"], "duration": v.get("duration", 0)})
    return out


def _pixabay(query: str, portrait: bool) -> list[dict]:
    if not PIXABAY_KEY:
        return []
    r = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": PIXABAY_KEY, "q": query, "per_page": 15, "safesearch": "true"},
        timeout=30,
    )
    r.raise_for_status()
    out = []
    for v in r.json().get("hits", []):
        f = v["videos"].get("large") or v["videos"].get("medium")
        if f and f.get("url"):
            out.append({"id": f"pixabay-{v['id']}", "url": f["url"], "duration": v.get("duration", 0)})
    return out


def find_clips(query: str, portrait: bool, used: set[str], n: int) -> list[dict]:
    """Up to n unused clips for a query, falling back to a broader query."""
    picks = []
    for q in (query, " ".join(query.split()[:2]), query.split()[0]):
        for clip in _pexels(q, portrait) + _pixabay(q, portrait):
            if clip["id"] not in used and clip["duration"] >= 3:
                picks.append(clip)
                used.add(clip["id"])
                if len(picks) == n:
                    return picks
    return picks


def download(clip: dict, dest: Path) -> Path:
    with requests.get(clip["url"], stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return dest
