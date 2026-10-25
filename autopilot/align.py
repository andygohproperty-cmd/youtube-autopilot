"""Forced alignment of the script to the narration (the WhisperX method: wav2vec2 + CTC).

We already know every word that is said, so instead of transcribing we align the script itself with
torchaudio's MMS_FA model. That gives each word a start/end to within a frame or two, which keeps the
captions and the word-cued shots locked to the voice. Needs torch + torchaudio (< 2.9) and num2words;
without them, or if anything fails, callers fall back to whisper timings.
"""
import re
from pathlib import Path

_CURRENCY = {"$": "dollars", "€": "euros", "£": "pounds", "¥": "yen"}
_SUFFIX = {"%": "percent", "k": "thousand", "m": "million", "bn": "billion", "b": "billion"}


def spoken(word: str) -> str:
    """How a script word sounds, as a-z letters only ("€26.5bn" -> "twentysixpointfiveeurosbillion")."""
    from num2words import num2words

    w = word.lower().replace("’", "'")
    out = []
    for tok in re.findall(r"[€$£¥]|\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th)?|%|[a-z']+", w):
        if tok in _CURRENCY:
            out.append(("after", _CURRENCY[tok]))
        elif tok[0].isdigit():
            ordinal = tok[-2:] in ("st", "nd", "rd", "th")
            n = tok[:-2] if ordinal else tok
            n = n.replace(",", "")
            try:
                if ordinal:
                    text = num2words(int(n), to="ordinal")
                elif "." not in n and 1100 <= int(n) <= 2099:
                    text = num2words(int(n), to="year")
                else:
                    text = num2words(float(n) if "." in n else int(n))
            except (ValueError, OverflowError):
                text = ""
            out.append(("num", text))
        elif tok == "%":
            out.append(("word", "percent"))
        else:
            suffix = out and out[-1][0] == "num" and tok in _SUFFIX
            out.append(("num", _SUFFIX[tok]) if suffix else ("word", tok))
    # "€26.5bn" is said "twenty-six point five billion euros": currency words go after the number
    words, pending = [], []
    for k, (kind, text) in enumerate(out):
        if kind == "after":
            pending.append(text)
            continue
        words.append(text)
        if kind == "num" and pending and not (k + 1 < len(out) and out[k + 1][0] == "num"):
            words += pending
            pending = []
    words += pending
    return re.sub(r"[^a-z]", "", "".join(words))


class Aligner:
    def __init__(self):
        import torch
        import torchaudio

        self.torch, self.ta = torch, torchaudio
        bundle = torchaudio.pipelines.MMS_FA
        self.sr = bundle.sample_rate
        self.model = bundle.get_model(with_star=False).eval()
        self.tokenizer = bundle.get_tokenizer()
        self.aligner = bundle.get_aligner()
        torch.set_num_threads(max(1, torch.get_num_threads()))

    def load(self, narration: Path):
        import soundfile as sf

        audio, sr = sf.read(str(narration), dtype="float32", always_2d=True)
        wave = self.torch.from_numpy(audio.mean(axis=1)).unsqueeze(0)
        return self.ta.functional.resample(wave, sr, self.sr) if sr != self.sr else wave

    def align(self, wave, a: float, b: float, words: list[str]) -> list[tuple[float, float] | None]:
        """Times for each word said between a and b seconds; None for words with nothing to align."""
        sounds = [spoken(w) for w in words]
        keep = [i for i, s in enumerate(sounds) if s]
        if not keep:
            return [None] * len(words)
        lo = max(0, int((a - 0.1) * self.sr))
        clip = wave[:, lo:int((b + 0.1) * self.sr)]
        with self.torch.inference_mode():
            emission, _ = self.model(clip)
        spans = self.aligner(emission[0], self.tokenizer([sounds[i] for i in keep]))
        ratio = clip.size(1) / emission.size(1) / self.sr
        out: list[tuple[float, float] | None] = [None] * len(words)
        for i, sp in zip(keep, spans):
            out[i] = (lo / self.sr + sp[0].start * ratio, lo / self.sr + sp[-1].end * ratio)
        return out


def load_aligner() -> Aligner | None:
    try:
        return Aligner()
    except Exception as e:   # not installed, or the model could not be fetched
        print(f"forced alignment unavailable ({type(e).__name__}: {e}); using whisper timings")
        return None
