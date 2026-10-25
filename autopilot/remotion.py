"""Render a long video's picture with Remotion (React motion graphics, remotion/ folder).

Each segment's `visual` picks scenes from remotion/src/scenes (photo, collage, map, timeline, stat,
brands, empire, chain, ledger, bars, waffle, donut, line, quote, versus, text, clip). A visual is one
scene ({"type": ...}) or several ({"shots": [...]}, each later shot starting when its `cue` word is
said). Asset fields are fetched here: `image`/`bgImage` (Wikimedia Commons), `broll`/`bgBroll`
(stock footage). With no visual, a segment shows its `image`, its `on_screen` stat, or stock b-roll.
Captions are timed per word by aligning the script to the narration (align.py), else faster-whisper,
else an estimate. Small photos are upscaled with Real-ESRGAN (upscale.py).
"""
import json
import os
import re
import shutil
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image

from .config import ROOT, Channel
from .footage import commons_image, download, find_clips
from .plan import Segment
from .voice import PAUSE_S

RDIR = ROOT / "remotion"
FPS = 30
TITLE_CARD = 2.6
CHAPTER_CARD = 1.8


# --- word timing ----------------------------------------------------------------------

def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _spread(words: list[str], a: float, b: float) -> list[tuple[float, float]]:
    """Estimate: share a speech window by word length."""
    weights = [len(x) + 1 for x in words]
    per = max(b - a, 0.1) / (sum(weights) or 1)
    out, t = [], a
    for wt in weights:
        out.append((t, t + wt * per * 0.9))
        t += wt * per
    return out


def _whisper_words(narration: Path) -> list[tuple[str, float, float]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return []
    try:
        model = WhisperModel(os.environ.get("WHISPER_MODEL", "base.en"), device="cpu", compute_type="int8")
        segs, _ = model.transcribe(str(narration), word_timestamps=True, beam_size=1, vad_filter=False)
        return [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or [])]
    except Exception as e:  # never fail a render over captions
        print(f"whisper failed, estimating word times: {e}")
        return []


def _fill(got: dict[int, tuple[float, float]], n: int, a: float, b: float) -> list[tuple[float, float]]:
    """Words without a time (numbers spelled differently, etc.) share the gaps between timed words."""
    idx = sorted(got)
    out = dict(got)
    for i in range(n):
        if i in got:
            continue
        prev = max([j for j in idx if j < i], default=None)
        nxt = min([j for j in idx if j > i], default=None)
        lo = got[prev][1] if prev is not None else a
        hi = got[nxt][0] if nxt is not None else b
        run = [j for j in range(n) if (prev is None or j > prev) and (nxt is None or j < nxt)]
        pos = run.index(i)
        step = max(hi - lo, 0.05) / len(run)
        out[i] = (lo + pos * step, lo + (pos + 1) * step)
    return [out[i] for i in range(n)]


def word_times(narration: Path, segments: list[Segment], durations: list[float],
               leads: list[float]) -> list[dict]:
    """Every script word with its start/end: forced alignment of the script (align.py), else whisper's
    timing matched to the script's spelling, else an estimate."""
    from .align import load_aligner

    aligner = load_aligner() if os.environ.get("FORCED_ALIGN", "1") != "0" else None
    wave = aligner.load(narration) if aligner else None
    heard = None
    out, t, aligned = [], 0.0, 0
    for seg, dur, lead in zip(segments, durations, leads):
        a, b = t + lead, t + dur - PAUSE_S
        words = seg.narration.split()
        times = _spread(words, a, b)
        got: dict[int, tuple[float, float]] = {}
        if aligner and words:
            try:
                got = {i: x for i, x in enumerate(aligner.align(wave, a, b, words)) if x}
            except Exception as e:   # never fail a render over captions
                print(f"alignment failed for a segment ({e}); using whisper there")
        if len(got) >= len(words) * 0.5:
            aligned += 1
        else:
            if heard is None:
                heard = _whisper_words(narration)
            got = {}
            near = [h for h in heard if a - 0.15 <= (h[1] + h[2]) / 2 <= b + 0.15]
            if near:
                sm = SequenceMatcher(None, [_norm(w) for w in words], [_norm(h[0]) for h in near], autojunk=False)
                for blk in sm.get_matching_blocks():
                    for k in range(blk.size):
                        got[blk.a + k] = (near[blk.b + k][1], near[blk.b + k][2])
        if words and len(got) >= len(words) * 0.5:
            times = _fill(got, len(words), a, b)
        out += [{"text": w, "start": round(s, 3), "end": round(e, 3)} for w, (s, e) in zip(words, times)]
        t += dur
    print(f"word timing: {aligned}/{len(segments)} segments force-aligned")
    return out


# --- assets ---------------------------------------------------------------------------

class Assets:
    def __init__(self, channel: Channel, workdir: Path):
        self.channel = channel
        self.dir = RDIR / "public" / "run"
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        self.raw = workdir / "clips"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.photos_used: set[str] = set()
        self.clips_used: set[str] = set()
        self.credits: list[str] = []
        self.photos: dict[str, dict] = {}
        self.n = 0

    def photo(self, query: str) -> dict:
        if query in self.photos:              # the same photo can return later in the video
            return self.photos[query]
        self.n += 1
        got = commons_image(query, self.dir / f"img_{self.n}.jpg", self.photos_used)
        if not got:
            print(f"no photo for {query!r}")
            self.photos[query] = {}
            return {}
        path, credit = got
        self.credits.append(credit)
        if os.environ.get("UPSCALE", "1") != "0":
            from .upscale import upscale
            upscale(path)
        with Image.open(path) as im:
            w, h = im.size
        self.photos[query] = {"photo": f"run/{path.name}", "pw": w, "ph": h,
                              "credit": "Photo: " + credit.split(" (")[0][:90]}
        return self.photos[query]

    def clip(self, query: str, seconds: float) -> str:
        self.n += 1
        found = find_clips(query, False, self.clips_used, 1)
        src = download(found[0], self.raw / f"src_{self.n}.mp4") if found else None
        if not src:
            print(f"no clip for {query!r}")
            return ""
        dest = self.dir / f"clip_{self.n}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-t", f"{seconds + 0.5:.2f}",
                        "-vf", f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080",
                        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", str(dest)],
                       check=True)
        return f"run/{dest.name}"

    def resolve(self, spec: dict, seconds: float) -> dict:
        """Fetch the files a scene names and swap the names for paths."""
        s = dict(spec)
        if s.get("image"):
            s.update(self.photo(s.pop("image")))
        if s.get("bgImage"):
            s["bgPhoto"] = self.photo(s.pop("bgImage")).get("photo", "")
        if s.get("broll"):
            s["clip"] = self.clip(s.pop("broll"), seconds)
        if s.get("bgBroll"):
            s["bgClip"] = self.clip(s.pop("bgBroll"), seconds)
        if s.get("items") and s.get("type") == "collage":
            items = []
            for it in s["items"]:
                it = dict(it)
                if it.get("image"):
                    it.update(self.photo(it.pop("image")))
                items.append(it)
            s["items"] = items
        if s.get("type") == "photo" and not s.get("photo"):
            s["type"] = "clip" if s.get("clip") else "text"
            s.setdefault("lines", [])
        if s.get("type") == "clip" and not s.get("clip") and s.get("photo"):
            s["type"] = "photo"
        return s


SCENE_TYPES = {"photo", "clip", "collage", "title", "chapter", "text", "stat", "quote", "versus", "brands", "empire",
               "chain", "ledger", "bars", "waffle", "donut", "line", "timeline", "map"}   # remotion/src/scenes/index.tsx


def plan_problems(plan) -> list[str]:
    out = []
    for i, seg in enumerate(plan.segments):
        for sh in (seg.visual.get("shots") or [seg.visual]) if seg.visual else []:
            if sh.get("type") not in SCENE_TYPES:
                out.append(f"segment {i}: unknown scene type {sh.get('type')!r}")
    # motion, not a slideshow: ~1 in 3 shots is video, and never 3 still photos in a row
    shots = [(i, sh) for i, seg in enumerate(plan.segments)
             for sh in ((seg.visual.get("shots") or [seg.visual]) if seg.visual else [])]
    moving = sum(1 for _, sh in shots if sh.get("type") == "clip" or sh.get("bgBroll"))
    if len(shots) >= 12 and moving < len(shots) * 0.3:
        out.append(f"only {moving} of {len(shots)} shots are video (clip or bgBroll); make about 1 in 3 move")
    run = 0
    for i, sh in shots:
        run = run + 1 if sh.get("type") in ("photo", "collage") else 0
        if run == 3:
            out.append(f"segment {i}: 3 photo/collage shots in a row; swap one for a clip or a graphic")
    return out


# --- scenes ---------------------------------------------------------------------------

def _default_visual(seg: Segment) -> dict:
    if seg.image:
        return {"type": "photo", "image": seg.image}
    if seg.on_screen:
        return {"type": "stat", "value": seg.on_screen, "bgBroll": seg.broll_query}
    return {"type": "clip", "broll": seg.broll_query}


def _said(words: list[dict], key: str, after: float) -> float | None:
    parts = [_norm(p) for p in key.split()]
    for i, w in enumerate(words):
        if w["start"] < after:
            continue
        if all(i + j < len(words) and _norm(words[i + j]["text"]).startswith(p) for j, p in enumerate(parts)):
            return w["start"]
    return None


def build_props(channel: Channel, segments: list[Segment], durations: list[float], leads: list[float],
                words: list[dict], title: str, workdir: Path) -> tuple[dict, list[tuple[float, str]], list[str]]:
    assets = Assets(channel, workdir)
    scenes, cues, cuts, quiet = [], [(0.0, "impact")], [], []
    t, chapter_no, hook_end, last_fx = 0.0, 0, None, 0.0
    for i, (seg, dur, lead) in enumerate(zip(segments, durations, leads)):
        start, end = t, t + dur
        if seg.chapter:
            chapter_no += 1
            if chapter_no == 1 and t > 0:
                hook_end = t
                scenes.append({"type": "title", "start": t, "end": t + TITLE_CARD, "channel": channel.name.upper(),
                               "lines": _title_lines(title)})
                cues += [(t - 0.2, "whoosh"), (t + 0.1, "impact")]
                quiet.append([t, t + TITLE_CARD])
                start = t + TITLE_CARD
            card_end = min(start + CHAPTER_CARD, end - 1.0)
            scenes.append({"type": "chapter", "start": start, "end": card_end, "number": chapter_no, "title": seg.chapter})
            cues += [(start - 0.2, "whoosh"), (start + 0.05, "impact")]
            last_fx = card_end
            cuts.append(start)
            quiet.append([start, card_end])
            start = card_end
        seg_words = [w for w in words if start - 0.05 <= w["start"] < end]
        vis = seg.visual or _default_visual(seg)
        shots = vis.get("shots") or [vis]
        # shot boundaries: when each shot's `from` word is said
        bounds, cursor = [start], start
        for sh in shots[1:]:
            at = _said(seg_words, sh["cue"], cursor + 0.6) if sh.get("cue") else None
            if at is None:
                at = cursor + (end - cursor) / (len(shots) - len(bounds) + 1)
            bounds.append(at)
            cursor = at
        bounds.append(end)
        for k, sh in enumerate(shots):
            a, b = bounds[k], bounds[k + 1]
            spec = {key: v for key, v in sh.items() if key != "cue"}
            if spec.get("type") == "stat" and not spec.get("value"):
                spec["value"] = seg.on_screen
            spec = assets.resolve(spec, b - a)
            spec.update(start=round(a, 3), end=round(b, 3),
                        words=[w for w in seg_words if a - 0.05 <= w["start"] < b])
            scenes.append(spec)
            if a - last_fx > 3.5 and a > 0.5:   # a soft swish on scene changes, never back to back
                cues.append((a - 0.12, "swish"))
                last_fx = a
            if spec["type"] == "text" and hook_end is None:
                quiet.append([a, b])        # hook: the big words are already on screen
            if spec["type"] in ("stat", "donut", "waffle"):
                cues.append((a + 0.15, "pop"))
        t = end
    total = t
    props = {
        "fps": FPS, "width": channel.size[0], "height": channel.size[1], "duration": round(total, 3), "title": title,
        "channel": channel.name.upper(), "hookEnd": round(hook_end if hook_end is not None else min(30.0, total), 3),
        "noCaptions": quiet, "scenes": scenes, "words": words, "cuts": cuts,
    }
    return props, cues, assets.credits


def _title_lines(title: str) -> list[str]:
    words = title.split()
    if len(words) <= 3:
        return [title]
    cut = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    return [" ".join(words[:cut]), " ".join(words[cut:])]


def render_remotion(channel: Channel, segments: list[Segment], durations: list[float], leads: list[float],
                    narration: Path, workdir: Path, title: str, dest: Path) -> tuple[list[tuple[float, str]], list[str]]:
    """Render the silent picture (captions burned in) to `dest`; return SFX cues and photo credits."""
    words = word_times(narration, segments, durations, leads) if channel.captions != "none" else []
    props, cues, credits = build_props(channel, segments, durations, leads, words, title, workdir)
    props_file = workdir / "remotion-props.json"
    props_file.write_text(json.dumps(props))
    if not (RDIR / "node_modules").exists():
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=RDIR, check=True)
    cmd = ["npx", "remotion", "render", "src/index.ts", "Doc", str(dest.resolve()), f"--props={props_file.resolve()}",
           f"--concurrency={os.cpu_count() or 2}", "--codec=h264", "--crf=16",
           "--muted", "--log=info"]
    if os.environ.get("REMOTION_BROWSER"):
        cmd.append(f"--browser-executable={os.environ['REMOTION_BROWSER']}")
    subprocess.run(cmd, cwd=RDIR, check=True)
    return cues, credits


def remotion_still(workdir: Path, at: float, dest: Path) -> Path:
    """A caption-free frame of the rendered picture (thumbnail background)."""
    props = json.loads((workdir / "remotion-props.json").read_text())
    props["words"] = []
    clean = workdir / "remotion-props-still.json"
    clean.write_text(json.dumps(props))
    cmd = ["npx", "remotion", "still", "src/index.ts", "Doc", str(dest.resolve()), f"--props={clean.resolve()}",
           f"--frame={int(at * FPS)}"]
    if os.environ.get("REMOTION_BROWSER"):
        cmd.append(f"--browser-executable={os.environ['REMOTION_BROWSER']}")
    subprocess.run(cmd, cwd=RDIR, check=True)
    return dest
