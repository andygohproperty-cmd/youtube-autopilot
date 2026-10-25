"""Audio mix: narration + ducked music bed + sparse sound effects, all built in numpy.

Sound effects and (by default) music are synthesised, so they are original with no licence
or Content ID questions. Licensed tracks dropped in assets/music/<mood>/*.mp3 are used instead.
"""
import random
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from .config import ASSETS_DIR

SR = 48000


def _load(path: Path) -> np.ndarray:
    """Any audio file as mono float32 at SR."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def _fade(x: np.ndarray, fin: float, fout: float) -> np.ndarray:
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, min(a, len(x)))[: len(x[:a])]
    if b:
        x[-b:] *= np.linspace(1, 0, min(b, len(x)))[-len(x[-b:]):]
    return x


# --- sound effects ---------------------------------------------------------------

def whoosh(length: float = 0.55) -> np.ndarray:
    n = int(length * SR)
    noise = np.random.default_rng(1).standard_normal(n).astype(np.float32)
    # Sweep a one-pole low-pass up then down for the "air rushing past" feel.
    cutoff = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    alpha = 0.02 + 0.5 * cutoff
    out = np.empty(n, dtype=np.float32)
    y = 0.0
    for i in range(n):
        y += alpha[i] * (noise[i] - y)
        out[i] = y
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (out * env / (np.abs(out).max() + 1e-9) * 0.5).astype(np.float32)


def pop(length: float = 0.12) -> np.ndarray:
    t = np.arange(int(length * SR)) / SR
    freq = 900 * np.exp(-t * 25) + 300
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    return (tone * np.exp(-t * 40) * 0.45).astype(np.float32)


def impact(length: float = 1.2) -> np.ndarray:
    t = np.arange(int(length * SR)) / SR
    freq = 70 * np.exp(-t * 3) + 38
    boom = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 3.5)
    click = np.random.default_rng(2).standard_normal(len(t)) * np.exp(-t * 60) * 0.3
    return ((boom + click) * 0.7).astype(np.float32)


def riser(length: float = 1.6) -> np.ndarray:
    t = np.arange(int(length * SR)) / SR
    freq = 200 * (8 ** (t / length))
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR) * 0.3
    noise = np.random.default_rng(3).standard_normal(len(t)) * 0.15
    return ((tone + noise) * (t / length) ** 2 * 0.5).astype(np.float32)


SFX = {"whoosh": whoosh, "pop": pop, "impact": impact, "riser": riser,
       "swish": lambda: whoosh(0.35) * 0.45}   # soft, for ordinary scene changes


# --- music -----------------------------------------------------------------------

def music_tracks(prefer: str) -> list[Path]:
    """Tracks in assets/music, with the channel's mood folder first."""
    base = ASSETS_DIR / "music"
    mood = sorted((base / prefer).glob("*.mp3")) if prefer else []
    rest = sorted(p for p in base.rglob("*.mp3") if p not in mood)
    return mood or rest


def _generated(seconds: float, mood: str, seed: int) -> np.ndarray:
    from . import musicgen
    raw = musicgen.section(seconds, mood or "documentary", seed)
    x = np.linspace(0, len(raw) - 1, int(len(raw) * SR / musicgen.SR))
    return np.interp(x, np.arange(len(raw)), raw).astype(np.float32)


def music_bed(total: float, sections: list[float], prefer: str) -> tuple[np.ndarray, list[str]]:
    """One piece of music per section (chapter), crossfaded; returns audio and licensed tracks used.

    Uses tracks from assets/music when present, otherwise original generated music."""
    tracks = music_tracks(prefer)
    random.shuffle(tracks)
    n = int(total * SR)
    bed = np.zeros(n, dtype=np.float32)
    used: list[str] = []
    seed = random.randint(0, 10_000)
    bounds = [0.0, *sections, total]
    for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if b - a < 0.5:
            continue
        need = int((b - a + 1.5) * SR)
        if tracks:
            track = tracks[k % len(tracks)]
            audio = _load(track)
            used.append(track.stem)
        else:
            audio = _generated(b - a + 1.5, prefer, seed + k)
        audio = audio / (_rms(audio) + 1e-9) * 0.1        # equal loudness across sections
        start = random.randint(0, len(audio) - need) if len(audio) > need else 0
        piece = np.resize(audio[start:], need) if len(audio) - start < need else audio[start:start + need]
        piece = _fade(piece, 1.0 if k else 0.3, 1.5)
        i = int(a * SR)
        piece = piece[: n - i]
        bed[i:i + len(piece)] += piece
    return bed, sorted(set(used))


# --- mix -------------------------------------------------------------------------

def mix(narration: Path, cues: list[tuple[float, str]], sections: list[float], prefer: str,
        dest: Path, music_level: float = 0.55) -> list[str]:
    """Write the final stereo mix; returns the music tracks used (for attribution)."""
    voice = _load(narration)
    total = len(voice) / SR + 1.0
    n = int(total * SR)
    out_voice = np.zeros(n, dtype=np.float32)
    out_voice[: len(voice)] = voice / (np.abs(voice).max() + 1e-9) * 0.85

    bed, used = music_bed(total, sections, prefer)
    # Duck the music under speech: 50 ms envelope, smoothed, gain 1.0 -> 0.35 while talking.
    win = int(0.05 * SR)
    env = np.sqrt(np.convolve(out_voice ** 2, np.ones(win) / win, mode="same"))
    talking = (env > 0.02).astype(np.float32)
    smooth = int(0.25 * SR)
    talking = np.convolve(talking, np.ones(smooth) / smooth, mode="same")
    bed *= music_level * (1.0 - 0.65 * np.clip(talking, 0, 1))

    fx = np.zeros(n, dtype=np.float32)
    for t, name in cues:
        s = SFX[name]()
        i = int(max(0.0, t) * SR)
        s = s[: n - i]
        fx[i:i + len(s)] += s * 0.6

    master = out_voice + bed + fx
    peak = np.abs(master).max()
    if peak > 0.98:
        master *= 0.98 / peak
    sf.write(dest, np.stack([master, master], axis=1), SR)
    return used
