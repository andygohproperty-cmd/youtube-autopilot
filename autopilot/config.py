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
    voice: str
    category_id: str
    niche: str
    style: str
    avoid: str
    production_days: list = field(default_factory=list)
    publish_hour_utc: int = 15
    target_minutes: float = 8
    target_seconds: int = 50
    speed: float = 1.0
    language: str = "en"
    music_mood: str = ""                # folder under assets/music picked first

    @property
    def is_short(self) -> bool:
        return self.format == "short"

    @property
    def size(self) -> tuple[int, int]:
        return (1080, 1920) if self.is_short else (1920, 1080)

    @property
    def target_words(self) -> int:
        # Kokoro narrates at roughly 150 words per minute at speed 1.0.
        if self.is_short:
            return int(self.target_seconds / 60 * 150 * self.speed)
        return int(self.target_minutes * 150 * self.speed)

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
