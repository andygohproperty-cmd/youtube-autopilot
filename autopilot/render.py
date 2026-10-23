"""Assemble stock clips, narration, captions, cards, music and sound effects into the final MP4.

Editing style (studied from top business-explainer and facts-Shorts channels):
- a new shot every ~2.8 s on long videos (~1.8 s in the first 30 s), ~1.3 s on Shorts
- every shot moves: slow push in, pull out or pan, plus a light colour grade
- word-by-word highlighted captions; Shorts get big centred pop-in captions
- big stat cards for key numbers, chapter title cards with a beat of silence
- music bed that changes per chapter and ducks under the voice, sparse whoosh/pop/impact
"""
import random
import subprocess
from pathlib import Path

from .config import ASSETS_DIR, Channel
from .footage import download, find_clips
from .plan import Segment
from .sound import mix
from .voice import PAUSE_S

FPS = 30
CHAPTER_LEAD = 0.9      # silence before a chapter's narration while its card shows
CHAPTER_CARD = 1.8
MAX_SOURCES = 2         # distinct clips per segment; extra shots reuse them from a new angle


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _probe_seconds(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _motion(move: str, w: int, h: int, length: float, amount: float = 0.12) -> str:
    """FFmpeg filter that gives a still-framed shot a slow camera move."""
    if move in ("in", "out"):
        k = f"(t/{length:.3f})" if move == "in" else f"(1-t/{length:.3f})"
        return (f"scale=w='2*trunc({w}*(1+{amount}*{k})/2)':h='2*trunc({h}*(1+{amount}*{k})/2)'"
                f":eval=frame,crop={w}:{h}")
    big_w, big_h = 2 * round(w * (1 + amount) / 2), 2 * round(h * (1 + amount) / 2)
    x = f"(iw-{w})*t/{length:.3f}" if move == "right" else f"(iw-{w})*(1-t/{length:.3f})"
    return f"scale={big_w}:{big_h},crop={w}:{h}:x='{x}':y='(ih-{h})/2'"


GRADES = {   # colour grade per channel `grade`
    "natural": "eq=contrast=1.05:saturation=1.08",
    "cinematic": "eq=contrast=1.18:saturation=0.78:brightness=-0.04:gamma=0.95,vignette=PI/4.5",
    "bright": "eq=contrast=1.06:saturation=1.2:brightness=0.03",
}


def _shot(src: Path | None, frames: int, size: tuple[int, int], move: str, dest: Path,
          grade: str = "natural") -> None:
    w, h = size
    length = frames / FPS
    enc = ["-frames:v", str(frames), "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-an"]
    if src is None:  # no footage at all: dark slate so the render never fails
        _ff("-f", "lavfi", "-i", f"color=c=0x15171c:s={w}x{h}:r={FPS}", "-vf", "format=yuv420p",
            *enc, str(dest))
        return
    span = _probe_seconds(src)
    start = random.uniform(0, max(0.0, span - length - 0.2)) if span > length + 0.5 else 0.0
    vf = (f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},"
          f"{_motion(move, w, h, length, 0.08)},{GRADES.get(grade, GRADES['natural'])},unsharp=5:5:0.4,"
          f"setsar=1,format=yuv420p")
    _ff("-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", str(src), "-vf", vf, *enc, str(dest))


# --- subtitles, cards and overlays (one ASS file) --------------------------------

def _t(t: float) -> str:
    h, rem = divmod(max(t, 0.0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _esc(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


YELLOW = "&H00E1FF&"   # ASS override colours are &HBBGGRR&
WHITE = "&HFFFFFF&"


def _styles(channel: Channel) -> list[str]:
    fmt = ("Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
           "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
           "Alignment,MarginL,MarginR,MarginV,Encoding")
    if channel.is_short:
        cap = "Cap,Anton,140,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,8,4,5,70,70,0"
        stat = "Stat,Anton,170,&H0000E1FF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,10,6,5,60,60,0"
        banner = "Banner,Anton,96,&H00000000,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,1,0,3,22,0,8,90,90,300"
    else:
        cap = "Cap,Anton,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,6,3,2,160,160,80"
        stat = "Stat,Anton,200,&H0000E1FF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,3,0,1,10,6,5,100,100,0"
        banner = "Banner,Anton,64,&H00000000,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,1,0,3,18,0,8,90,90,60"
    label = "Label,Anton,54,&H0000E1FF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,8,0,1,0,0,5,60,60,0"
    title = "Title,Anton,130,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,6,4,5,120,120,0"
    box = "Box,Arial,10,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0"
    return ["[V4+ Styles]", fmt] + [f"Style: {s}" for s in (cap, stat, banner, label, title, box)]


def _rect(w: int, h: int, alpha: str) -> str:
    return f"{{\\an7\\pos(0,0)\\bord0\\shad0\\1c&H000000&\\1a&H{alpha}&\\p1}}m 0 0 l {w} 0 {w} {h} 0 {h}{{\\p0}}"


def _overlays(channel: Channel, segments: list[Segment], durations: list[float],
              leads: list[float], hook_text: str, dest: Path, cards: bool = True) -> list[tuple[float, str]]:
    """Write the ASS file; return sound-effect cues [(time, name)] that match the visuals."""
    w, h = (1080, 1920) if channel.is_short else (1920, 1080)   # design size; libass scales it
    ev: list[str] = []
    cues: list[tuple[float, str]] = []
    words_per_chunk = 2 if channel.is_short else 4

    def add(layer: int, a: float, b: float, style: str, text: str) -> None:
        ev.append(f"Dialogue: {layer},{_t(a)},{_t(b)},{style},,0,0,0,,{text}")

    if channel.is_short and hook_text:          # hook banner over the first seconds
        add(8, 0.0, 2.6, "Banner", "{\\fad(0,200)}" + _esc(hook_text.upper()))
        cues.append((0.0, "whoosh"))
    elif not channel.is_short:
        cues.append((0.0, "impact"))            # cold open lands with a hit

    t = 0.0
    chapter_no = 0
    for seg, dur, lead in zip(segments, durations, leads):
        speech_a, speech_b = t + lead, t + dur - PAUSE_S
        if seg.chapter and not channel.is_short:
            chapter_no += 1
            a, b = t, t + CHAPTER_CARD
            cues += [(a - 0.2, "whoosh"), (a + 0.05, "impact")]
            if cards:
                add(6, a, b, "Box", "{\\fad(120,250)}" + _rect(w, h, "40"))
                add(7, a, b, "Label", f"{{\\fad(120,250)\\pos({w // 2},{h // 2 - 110})}}PART {chapter_no}")
                add(7, a, b, "Title", f"{{\\fad(120,250)\\pos({w // 2},{h // 2 + 30})"
                                      f"\\fscx85\\fscy85\\t(0,250,\\fscx100\\fscy100)}}{_esc(seg.chapter.upper())}")
        if seg.on_screen and cards:
            a = speech_a + 0.1
            b = min(speech_b + 0.2, a + 2.6)
            y = h // 2 if not channel.is_short else int(h * 0.33)
            add(3, a, b, "Box", "{\\fad(80,150)}" + _rect(w, h, "70"))
            add(4, a, b, "Stat", f"{{\\pos({w // 2},{y})\\fad(60,150)\\fscx60\\fscy60"
                                 f"\\t(0,120,\\fscx112\\fscy112)\\t(120,220,\\fscx100\\fscy100)}}"
                                 f"{_esc(seg.on_screen.upper())}")
            cues.append((a, "pop"))

        if not cards and seg.visual.get("type") in ("stat", "pie", "bars", "receipt"):
            cues.append((t + lead + 0.1, "pop"))

        # Word-by-word captions, timed by character share of the segment's speech.
        words = seg.narration.split() if channel.captions != "none" else []
        weights = [len(x) + 1 for x in words]
        span = max(speech_b - speech_a, 0.1)
        per = span / (sum(weights) or 1)
        starts, s = [], speech_a
        for wt in weights:
            starts.append(s)
            s += wt * per
        for c in range(0, len(words), words_per_chunk):
            chunk = words[c:c + words_per_chunk]
            chunk_end = starts[c + len(chunk)] if c + len(chunk) < len(words) else speech_b
            for k in range(len(chunk)):
                a = starts[c + k]
                b = starts[c + k + 1] if c + k + 1 < len(words) else speech_b
                if k == len(chunk) - 1:
                    b = chunk_end
                parts = [(f"{{\\c{YELLOW}}}{_esc(x)}{{\\c{WHITE}}}" if j == k else _esc(x))
                         for j, x in enumerate(chunk)]
                text = " ".join(parts)
                if channel.is_short:
                    y = int(h * 0.62)
                    anim = f"\\pos({w // 2},{y})"
                    if k == 0:
                        anim += "\\fscx75\\fscy75\\t(0,90,\\fscx108\\fscy108)\\t(90,150,\\fscx100\\fscy100)"
                    text = f"{{{anim}}}" + text.upper()
                add(5, a, b, "Cap", text)
        t += dur

    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}",
             "WrapStyle: 0", "ScaledBorderAndShadow: yes", "", *_styles(channel), "",
             "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text", *ev]
    dest.write_text("\n".join(lines) + "\n")
    return cues


# --- assembly ---------------------------------------------------------------------

def shot_length(channel: Channel, at: float) -> float:
    if channel.is_short:
        return 1.3
    return 1.8 if at < 30 else 2.8


def leads_for(channel: Channel, segments: list[Segment]) -> list[float]:
    return [CHAPTER_LEAD if (s.chapter and not channel.is_short) else 0.0 for s in segments]


def render(channel: Channel, segments: list[Segment], durations: list[float], leads: list[float],
           narration: Path, workdir: Path, hook_text: str = "") -> tuple[Path, list[str]]:
    """Returns the final video and the music tracks used (for attribution)."""
    w, h = channel.size
    animated = channel.visual_style == "animated"
    silent = workdir / "silent.mp4"
    if animated:
        from .animate import render_scenes
        render_scenes(scenes_for(channel, segments, durations), sum(durations), (w, h), silent,
                      channel.visual_theme)
    else:
        _stock_video(channel, segments, durations, workdir, silent)

    subs = workdir / "overlays.ass"
    cues = _overlays(channel, segments, durations, leads, hook_text, subs, cards=not animated)
    sections, t = [], 0.0
    for seg, dur in zip(segments, durations):
        if seg.chapter and t > 0:
            sections.append(t)
        t += dur
    audio = workdir / "mix.wav"
    tracks = mix(narration, cues, sections, channel.music_mood, audio)

    out = workdir / "final.mp4"
    fonts = ASSETS_DIR / "fonts"
    _ff("-i", str(silent), "-i", str(audio), "-vf", f"subtitles={subs}:fontsdir={fonts}",
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-tune", "film", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out))
    return out, tracks


def scenes_for(channel: Channel, segments: list[Segment], durations: list[float]) -> list[dict]:
    """One animated scene per segment; a chapter card takes the first moments of its segment."""
    scenes, t, chapter_no = [], 0.0, 0
    for seg, dur in zip(segments, durations):
        start = t
        if seg.chapter and not channel.is_short:
            chapter_no += 1
            card = min(CHAPTER_CARD, dur * 0.5)
            scenes.append({"start": t, "end": t + card,
                           "spec": {"type": "chapter", "number": chapter_no, "title": seg.chapter}})
            start = t + card
        spec = seg.visual or ({"type": "text", "lines": [seg.on_screen]} if seg.on_screen
                              else {"type": "text", "lines": [" ".join(seg.narration.split()[:3])]})
        scenes.append({"start": start, "end": t + dur, "spec": spec})
        t += dur
    return scenes


def _stock_video(channel: Channel, segments: list[Segment], durations: list[float], workdir: Path,
                 silent: Path) -> None:
    clips_dir = workdir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    w, h = channel.size
    used: set[str] = set()
    shots: list[Path] = []
    moves = ["in", "right", "out", "left"]
    t, frame_pos, k = 0.0, 0, 0
    last_sources: list[Path] = []
    for i, (seg, dur) in enumerate(zip(segments, durations)):
        n = max(1, round(dur / shot_length(channel, t)))
        found = find_clips(seg.broll_query, channel.is_short, used, min(n, MAX_SOURCES))
        sources = [p for j, c in enumerate(found) if (p := download(c, clips_dir / f"src_{i}_{j}.mp4"))]
        sources = sources or last_sources      # nothing found: reuse the previous segment's clips
        last_sources = sources or last_sources
        seg_end = round((t + dur) * FPS)
        for j in range(n):
            end = frame_pos + (seg_end - frame_pos) // (n - j)
            dest = clips_dir / f"shot_{i:03d}_{j}.mp4"
            src = sources[j % len(sources)] if sources else None
            _shot(src, max(1, end - frame_pos), (w, h), moves[k % len(moves)], dest, channel.grade)
            shots.append(dest)
            frame_pos, k = end, k + 1
        t += dur

    concat = workdir / "shots.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in shots))
    _ff("-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent))
