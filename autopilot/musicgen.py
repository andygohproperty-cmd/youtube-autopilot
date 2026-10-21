"""Original background music, synthesised in numpy (no licence or Content ID risk).

Each section gets its own key, chord loop and seed, so the bed changes per chapter.
Moods: "documentary" (minor, ~96 BPM, pulse + plucks) and "upbeat" (major, ~118 BPM, four-on-the-floor).
"""
import numpy as np

SR = 24000  # rendered here, resampled to the mix rate by the caller

MOODS = {
    "documentary": {"bpm": (90, 100), "loops": [[0, 8, 3, 10], [0, 5, 8, 7], [0, 10, 8, 7]],
                    "minor": True, "kick": [0, 2], "hats": False},
    "upbeat": {"bpm": (114, 122), "loops": [[0, 7, 9, 5], [0, 5, 7, 5], [9, 5, 0, 7]],
               "minor": False, "kick": [0, 1, 2, 3], "hats": True},
}


def _hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def _tone(freq: float, n: int, harmonics: int = 5, detune: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        out += np.sin(2 * np.pi * freq * k * (1 + detune) * t) / k ** 1.4
    return out


def _chord(root: int, minor: bool) -> list[int]:
    return [root, root + (3 if minor else 4), root + 7]


def _reverb(x: np.ndarray, seconds: float = 1.8, wet: float = 0.25) -> np.ndarray:
    rng = np.random.default_rng(7)
    m = int(seconds * SR)
    ir = rng.standard_normal(m) * np.exp(-np.linspace(0, 6, m))
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + m)))
    wet_sig = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return x * (1 - wet) + wet_sig * wet


def section(seconds: float, mood: str, seed: int) -> np.ndarray:
    cfg = MOODS.get(mood, MOODS["documentary"])
    rng = np.random.default_rng(seed)
    bpm = rng.uniform(*cfg["bpm"])
    beat = 60 / bpm
    key = 45 + int(rng.integers(0, 7))            # A2..D#3 region
    loop = cfg["loops"][int(rng.integers(0, len(cfg["loops"])))]
    minor = cfg["minor"]
    n = int((seconds + 2) * SR)
    pad, arp, bass, drums = (np.zeros(n) for _ in range(4))
    bar = 4 * beat
    bars = int(np.ceil(seconds / bar)) + 1
    arp_pattern = [0, 1, 2, 1, 0, 2, 1, 2] if minor else [0, 2, 1, 2, 0, 2, 1, 2]
    for b in range(bars):
        start = int(b * bar * SR)
        if start >= n:
            break
        root = key + loop[b % len(loop)]
        if minor and loop[b % len(loop)] in (3, 8, 10):   # relative-major chords in a minor loop
            notes = _chord(root, False)
        elif not minor and loop[b % len(loop)] == 9:
            notes = _chord(root, True)
        else:
            notes = _chord(root, minor)
        length = min(int(bar * SR), n - start)
        env = np.minimum(1, np.arange(length) / (0.25 * SR)) * np.minimum(1, (length - np.arange(length)) / (0.3 * SR))
        for note in notes:
            f = _hz(note + 12)
            pad[start:start + length] += env * (_tone(f, length, 6, 0.003) + _tone(f, length, 6, -0.003)) * 0.06
        for s in range(8):                      # pulsing eighth-note bass
            a = start + int(s * beat / 2 * SR)
            m = min(int(beat / 2 * SR), n - a)
            if m <= 0:
                continue
            tt = np.arange(m) / SR
            bass[a:a + m] += np.tanh(1.5 * np.sin(2 * np.pi * _hz(root - 12) * tt)) * np.exp(-tt * 6) * 0.08
        intro = b < 2
        step = beat / 2
        for s in range(8):
            a = start + int(s * step * SR)
            m = min(int(step * SR * 1.5), n - a)
            if m <= 0:
                continue
            f = _hz(notes[arp_pattern[s]] + 24)
            tt = np.arange(m) / SR
            arp[a:a + m] += _tone(f, m, 3) * np.exp(-tt * 9) * 0.09
        if intro:
            continue
        for k in cfg["kick"]:
            a = start + int(k * beat * SR)
            m = min(int(0.35 * SR), n - a)
            if m <= 0:
                continue
            tt = np.arange(m) / SR
            freq = 45 + 90 * np.exp(-tt * 30)
            drums[a:a + m] += np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 9) * 0.35
        if cfg["hats"]:
            for k in range(4):
                a = start + int((k + 0.5) * beat * SR)
                m = min(int(0.05 * SR), n - a)
                if m <= 0:
                    continue
                noise = np.diff(rng.standard_normal(m + 1))
                drums[a:a + m] += noise * np.exp(-np.arange(m) / SR * 80) * 0.05
    mixed = _reverb(pad + arp, 2.2, 0.35) + bass + drums
    mixed = mixed[: int(seconds * SR)]
    return (mixed / (np.abs(mixed).max() + 1e-9) * 0.8).astype(np.float32)
