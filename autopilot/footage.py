"""Free stock footage from Pexels (primary) and Pixabay (backup)."""
import os
import time
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
        hd = [f for f in files if min(f["width"], f["height"]) >= 1080]
        if not hd:
            continue
        best = min(hd, key=lambda f: f["width"] * f["height"])
        out.append({"id": f"pexels-{v['id']}", "url": best["link"], "duration": v.get("duration", 0)})
    return out


def _pixabay(query: str, portrait: bool) -> list[dict]:
    """Sharp clips only: 4K for Shorts (cropped to vertical) or portrait clips; 1080p+ for long videos."""
    if not PIXABAY_KEY:
        return []
    r = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": PIXABAY_KEY, "q": query, "per_page": 30, "safesearch": "true",
                "video_type": "film", "min_width": 0 if portrait else 1920},
        timeout=30,
    )
    r.raise_for_status()
    out = []
    for v in r.json().get("hits", []):
        sizes = [f for f in v["videos"].values() if f.get("url") and f.get("width")]
        if portrait:
            ok = [f for f in sizes if f["height"] >= 1920 and (f["height"] > f["width"] or f["width"] >= 3840)]
        else:
            ok = [f for f in sizes if f["width"] >= 1920]
        if not ok:
            continue
        # Smallest file that is still sharp enough; skip giant downloads.
        best = min(ok, key=lambda f: f.get("size") or f["width"] * f["height"])
        if (best.get("size") or 0) > 150_000_000:
            continue
        out.append({"id": f"pixabay-{v['id']}", "url": best["url"], "duration": v.get("duration", 0)})
    return out


def find_clips(query: str, portrait: bool, used: set[str], n: int) -> list[dict]:
    """Up to n unused clips for a query, falling back to a broader query."""
    picks = []
    for q in dict.fromkeys((query, " ".join(query.split()[:2]))):   # single words match too loosely
        for clip in _pexels(q, portrait) + _pixabay(q, portrait):
            if clip["id"] not in used and clip["duration"] >= 3:
                picks.append(clip)
                used.add(clip["id"])
                if len(picks) == n:
                    return picks
    return picks


def download(clip: dict, dest: Path) -> Path | None:
    """Download with backoff on rate limits (Pixabay's CDN answers 429 when pushed); None if it never works."""
    for attempt in range(6):
        try:
            with requests.get(clip["url"], stream=True, timeout=120) as r:
                if r.status_code == 429 or r.status_code >= 500:
                    wait = float(r.headers.get("Retry-After") or 0) or 5 * 2 ** attempt
                    time.sleep(min(wait, 120))
                    continue
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            return dest
        except requests.RequestException:
            time.sleep(5 * 2 ** attempt)
    return None


# --- High-resolution photos from Wikimedia Commons (free licences, credited in the description) ---

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "youtube-autopilot/1.0 (https://github.com/andygohproperty-cmd/youtube-autopilot)"}
FREE = ("cc0", "public domain", "pd", "cc by", "cc-by")      # no NC / ND licences


def _plain(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html or "").strip()


def commons_image(query: str, dest: Path, used: set[str], min_width: int = 1600) -> tuple[Path, str] | None:
    """`query` is a search ("federal reserve building") or an exact "File:..." title.
    Returns (image, credit line) for the first unused, freely licensed, large photo."""
    params = {"action": "query", "format": "json", "prop": "imageinfo",
              "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 2560}
    if query.startswith("File:"):
        params["titles"] = query
    else:
        params.update({"generator": "search", "gsrsearch": f"{query} filetype:bitmap",
                       "gsrnamespace": 6, "gsrlimit": 12})
    try:
        r = requests.get(COMMONS_API, params=params, headers=UA, timeout=30)
        r.raise_for_status()
        pages = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    except (requests.RequestException, ValueError):
        return None
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = _plain(meta.get("LicenseShortName", {}).get("value", "")).lower()
        if (p["title"] in used or info.get("width", 0) < min_width or info.get("mime") not in ("image/jpeg", "image/png")
                or not lic.startswith(FREE) or "nc" in lic.split("-") or "nd" in lic.split("-")):
            continue
        try:
            img = requests.get(info.get("thumburl") or info["url"], headers=UA, timeout=60)
            img.raise_for_status()
        except requests.RequestException:
            continue
        dest.write_bytes(img.content)
        used.add(p["title"])
        artist = _plain(meta.get("Artist", {}).get("value", "")) or "unknown"
        lic_name = _plain(meta.get("LicenseShortName", {}).get("value", ""))
        credit = f"{artist[:60]}, {lic_name}, commons.wikimedia.org/?curid={p.get('pageid', '')}"
        return dest, credit
    return None
