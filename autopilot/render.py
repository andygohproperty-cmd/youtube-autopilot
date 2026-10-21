"""Assemble stock clips, narration, captions and music into the final MP4 with FFmpeg."""
import random
import subprocess
from pathlib import Path

from .config import ASSETS_DIR, Channel
from .footage import download, find_clips
from .voice import PAUSE_S

SHOT_SECONDS = 5.0
FPS = 30


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _shot(src: Path | None, length: float, size: tuple[int, int], dest: Path) -> None:
    w, h = size
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"fps={FPS},setsar=1,format=yuv420p")
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-an"]
    if src is None:  # no footage found: dark slate so the render never fails
        _ff("-f", "lavfi", "-i", f"color=c=0x15171c:s={w}x{h}:r={FPS}", "-t", f"{length:.3f}",
            "-vf", "format=yuv420p", *enc, str(dest))
    else:
        _ff("-stream_loop", "-1", "-i", str(src), "-t", f"{length:.3f}", "-vf", vf, *enc, str(dest))


def _ass_time(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _captions(channel: Channel, texts: list[str], durations: list[float], dest: Path) -> None:
    w, h = channel.size
    if channel.is_short:
        style = "Anton,120,&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,7,2,5,60,60,0"
        words_per_line = 3
    else:
        style = "Anton,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,5,2,2,120,120,70"
        words_per_line = 7
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Default,{style}", "",
        "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    t = 0.0
    for text, dur in zip(texts, durations):
        words = text.split()
        chunks = [" ".join(words[i:i + words_per_line]) for i in range(0, len(words), words_per_line)]
        speech = max(dur - PAUSE_S, 0.1)
        total_chars = sum(len(c) for c in chunks) or 1
        start = t
        for chunk in chunks:
            end = start + speech * len(chunk) / total_chars
            safe = chunk.replace("{", "(").replace("}", ")")
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{safe}")
            start = end
        t += dur
    dest.write_text("\n".join(lines) + "\n")


def render(channel: Channel, queries: list[str], texts: list[str], durations: list[float],
           narration: Path, workdir: Path) -> Path:
    clips_dir = workdir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    shots: list[Path] = []
    for i, (query, dur) in enumerate(zip(queries, durations)):
        n = max(1, round(dur / SHOT_SECONDS))
        found = find_clips(query, channel.is_short, used, n)
        sources = [download(c, clips_dir / f"src_{i}_{j}.mp4") for j, c in enumerate(found)]
        for j in range(n):
            dest = clips_dir / f"shot_{i:03d}_{j}.mp4"
            src = sources[j % len(sources)] if sources else None
            _shot(src, dur / n, channel.size, dest)
            shots.append(dest)

    concat = workdir / "shots.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in shots))
    silent = workdir / "silent.mp4"
    _ff("-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent))

    subs = workdir / "captions.ass"
    _captions(channel, texts, durations, subs)
    fonts = ASSETS_DIR / "fonts"
    vf = f"subtitles={subs}:fontsdir={fonts}"

    out = workdir / "final.mp4"
    music = sorted((ASSETS_DIR / "music").glob("*.mp3"))
    inputs = ["-i", str(silent), "-i", str(narration)]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(random.choice(music))]
        audio = ["-filter_complex", "[2:a]volume=0.08[m];[1:a][m]amix=inputs=2:duration=first[a]",
                 "-map", "0:v", "-map", "[a]"]
    else:
        audio = ["-map", "0:v", "-map", "1:a"]
    _ff(*inputs, "-vf", vf, *audio, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out))
    return out
