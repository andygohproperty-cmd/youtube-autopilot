"""Narration with Kokoro, a free open-source TTS model that runs on CPU."""
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

from .config import MODELS_DIR, Channel

PAUSE_S = 0.35  # silence between segments


def narrate(channel: Channel, texts: list[str], out_wav: Path) -> list[float]:
    """Write one narration track; return each segment's duration in seconds (incl. pause)."""
    tts = Kokoro(str(MODELS_DIR / "kokoro-v1.0.int8.onnx"), str(MODELS_DIR / "voices-v1.0.bin"))
    pieces, durations, sr = [], [], 24000
    for text in texts:
        samples, sr = tts.create(text, voice=channel.voice, speed=channel.speed, lang="en-us")
        samples = np.concatenate([samples, np.zeros(int(PAUSE_S * sr), dtype=samples.dtype)])
        pieces.append(samples)
        durations.append(len(samples) / sr)
    sf.write(out_wav, np.concatenate(pieces), sr)
    return durations
