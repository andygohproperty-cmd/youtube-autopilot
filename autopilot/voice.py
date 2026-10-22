"""Narration with free open-source TTS models that run on CPU: Kokoro (fast) or Chatterbox (more natural)."""
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

from .config import MODELS_DIR, ROOT, Channel

PAUSE_S = 0.25  # silence between segments


def narrate(channel: Channel, texts: list[str], out_wav: Path,
            leads: list[float] | None = None) -> list[float]:
    """Write one narration track; return each segment's duration in seconds.

    A segment's duration includes its lead-in silence (`leads`, e.g. a beat before a
    chapter card) and the pause after it."""
    speak = _chatterbox(channel) if channel.tts == "chatterbox" else _kokoro(channel)
    pieces, durations, sr = [], [], 24000
    leads = leads or [0.0] * len(texts)
    for text, lead in zip(texts, leads):
        samples, sr = speak(text)
        samples = np.concatenate([np.zeros(int(lead * sr), dtype=samples.dtype), samples,
                                  np.zeros(int(PAUSE_S * sr), dtype=samples.dtype)])
        pieces.append(samples)
        durations.append(len(samples) / sr)
    sf.write(out_wav, np.concatenate(pieces), sr)
    return durations


def _kokoro(channel: Channel):
    tts = Kokoro(str(MODELS_DIR / "kokoro-v1.0.int8.onnx"), str(MODELS_DIR / "voices-v1.0.bin"))
    return lambda text: tts.create(text, voice=channel.voice, speed=channel.speed, lang="en-us")


def _chatterbox(channel: Channel):
    """Chatterbox (Resemble AI, MIT licence). `voice` "default" uses its built-in voice; a path to a
    .wav clones that voice, so only use synthetic or consented recordings."""
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device="cpu")
    ref = None if channel.voice == "default" else str(ROOT / channel.voice)

    def speak(text):
        wav = model.generate(text, audio_prompt_path=ref, exaggeration=channel.exaggeration, cfg_weight=0.4)
        samples = wav.squeeze(0).numpy().astype(np.float32)
        if channel.speed != 1.0:   # Chatterbox has no speed control: pitch-preserving tempo change via FFmpeg
            samples = _tempo(samples, model.sr, channel.speed)
        return samples, model.sr

    return speak


def _tempo(samples: np.ndarray, sr: int, speed: float) -> np.ndarray:
    import subprocess

    out = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                          "-af", f"atempo={speed}", "-f", "f32le", "-"],
                         input=samples.tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32)
