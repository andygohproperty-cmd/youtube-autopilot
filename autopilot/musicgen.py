"""Original background music, synthesised in numpy (no licence or Content ID risk).

Every video gets its own `style` (key, tempo, arpeggio, timbre, bass and drum feel; see pick_style), and
each section its own chord loop, so no two videos share a bed and it still changes per chapter.
Moods: "documentary" (minor, ~96 BPM, pulse + plucks) and "upbeat" (major, ~118 BPM, four-on-the-floor).
"""
import numpy as np

SR = 24000  # rendered here, resampled to the mix rate by the caller

MOODS = {
    "documentary": {"bpm": (84, 104), "loops": [[0, 8, 3, 10], [0, 5, 8, 7], [0, 10, 8, 7], [0, 3, 10, 5],
                                                [0, 8, 5, 7], [0, 7, 8, 10], [0, 0, 8, 10], [0, 5, 3, 8]],
                    "minor": True, "kick": [0, 2], "hats": False},
    "upbeat": {"bpm": (110, 126), "loops": [[0, 7, 9, 5], [0, 5, 7, 5], [9, 5, 0, 7], [0, 9, 5, 7], [5, 7, 0, 0]],
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


ARPS = [[0, 1, 2, 1, 0, 2, 1, 2], [0, 2, 1, 2, 0, 2, 1, 2], [0, 1, 2, 0, 1, 2, 0, 1],
        [2, 1, 0, 1, 2, 1, 0, 1], [0, 0, 2, 2, 1, 1, 2, 2], [0, 2, 0, 1, 0, 2, 0, 1]]
BASS = {"eighths": [0, 1, 2, 3, 4, 5, 6, 7], "quarters": [0, 2, 4, 6], "offbeat": [1, 3, 5, 7], "halves": [0, 4]}
KICKS = {"two": [0, 2], "one": [0], "four": [0, 1, 2, 3], "none": [], "push": [0, 2.5]}


def pick_style(mood: str, rng: np.random.Generator) -> dict:
    """One video's musical identity; `signature` names it so later videos can avoid repeating it."""
    cfg = MOODS.get(mood, MOODS["documentary"])
    st = {"key": int(rng.integers(0, 12)), "bpm": int(rng.integers(*cfg["bpm"])),
          "arp": int(rng.integers(0, len(ARPS))), "octave": int(rng.choice([12, 24])),
          "bright": int(rng.integers(3, 8)), "bass": str(rng.choice(list(BASS))),
          "kick": str(rng.choice(list(KICKS) if not cfg["hats"] else ["four", "two", "push"]))}
    st["signature"] = f"{mood}-k{st['key']}-a{st['arp']}-o{st['octave']}-{st['bass']}-{st['kick']}"
    return st


def section(seconds: float, mood: str, seed: int, style: dict | None = None) -> np.ndarray:
    cfg = MOODS.get(mood, MOODS["documentary"])
    rng = np.random.default_rng(seed)
    style = style or pick_style(mood, rng)
    beat = 60 / (style["bpm"] + rng.uniform(-1.5, 1.5))
    key = 41 + style["key"]                        # F2..E3 region
    loop = cfg["loops"][int(rng.integers(0, len(cfg["loops"])))]
    minor = cfg["minor"]
    n = int((seconds + 2) * SR)
    pad, arp, bass, drums = (np.zeros(n) for _ in range(4))
    bar = 4 * beat
    bars = int(np.ceil(seconds / bar)) + 1
    arp_pattern = ARPS[style["arp"]]
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
            pad[start:start + length] += env * (_tone(f, length, style["bright"], 0.003)
                                                + _tone(f, length, style["bright"], -0.003)) * 0.06
        for s in BASS[style["bass"]]:           # pulsing bass
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
            f = _hz(notes[arp_pattern[s]] + style["octave"])
            tt = np.arange(m) / SR
            arp[a:a + m] += _tone(f, m, 3) * np.exp(-tt * 9) * 0.09
        if intro:
            continue
        for k in KICKS[style["kick"]]:
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
