"""Channel config and shared paths."""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_DIR = ROOT / "channels"
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"
MODELS_DIR = Path(os.environ.get("MODELS_DIR", ROOT / "models"))
OUT_DIR = Path(os.environ.get("OUT_DIR", ROOT / "out"))


@dataclass
class Channel:
    id: str
    name: str
    secret_suffix: str
    format: str
    voice: str                          # Kokoro voice id, or a reference .wav for Chatterbox ("default" = its own voice)
    category_id: str
    niche: str
    style: str
    avoid: str
    production_days: list = field(default_factory=list)
    publish_hour_utc: int = 15
    target_minutes: float = 8
    min_minutes: float = 0              # long videos: never shorter (8+ min allows mid-roll ads)
    target_seconds: int = 50
    speed: float = 1.0
    language: str = "en"
    music_mood: str = ""                # folder under assets/music picked first
    visual_style: str = "stock"         # "stock" footage or "animated" motion graphics
    visual_theme: str = "dark"          # animated look: "dark" or "light" (cartoon)
    tts: str = "kokoro"                 # "kokoro" (fast) or "chatterbox" (more natural, ~10x slower on CPU)
    exaggeration: float = 0.6           # Chatterbox expressiveness

    @property
    def is_short(self) -> bool:
        return self.format == "short"

    @property
    def size(self) -> tuple[int, int]:
        # Long videos are uploaded at 1440p: YouTube then streams them with its higher-quality codec.
        return (1080, 1920) if self.is_short else (2560, 1440)

    @property
    def target_words(self) -> int:
        # Kokoro narrates at roughly 150 words per minute at speed 1.0, Chatterbox at roughly 200.
        wpm = (200 if self.tts == "chatterbox" else 150) * self.speed
        if self.is_short:
            return int(self.target_seconds / 60 * wpm)
        return int(self.target_minutes * wpm)

    def produces_today(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now.strftime("%a").lower() in self.production_days


def load_channel(channel_id: str) -> Channel:
    with open(CHANNELS_DIR / f"{channel_id}.yaml") as f:
        return Channel(**yaml.safe_load(f))


def all_channels() -> list[Channel]:
    return [load_channel(p.stem) for p in sorted(CHANNELS_DIR.glob("*.yaml"))]


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def history(channel_id: str) -> list[dict]:
    return _jsonl(DATA_DIR / "history" / f"{channel_id}.jsonl")


def feedback(channel_id: str) -> list[dict]:
    return _jsonl(DATA_DIR / "feedback" / f"{channel_id}.jsonl")


def append_record(kind: str, channel_id: str, record: dict) -> None:
    path = DATA_DIR / kind / f"{channel_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
