"""Animated motion-graphics visuals: scenes described as JSON, drawn by assets/anim/engine.html in
headless Chromium, captured frame by frame and encoded with FFmpeg.

Scene types (segment.visual): icons, stat, bars, pie, receipt, text, versus, list, quote, floorplan, chapter.
Icons are Lucide names (assets/anim/icons, ISC licence).
"""
import json
import os
import subprocess
from pathlib import Path

from .config import ASSETS_DIR

ANIM_DIR = ASSETS_DIR / "anim"
ICON_DIR = ANIM_DIR / "icons"
FPS = 30


def _icons_for(scenes: list[dict]) -> dict[str, str]:
    names = {"check", "circle-help"}
    for sc in scenes:
        s = sc["spec"]
        names.update(s.get("icons", []))
        names.update(s.get("corners", []))
        names.update(s.get("center", []))
        for side in ("left", "right"):
            if isinstance(s.get(side), dict):
                names.add(s[side].get("icon", ""))
        if s.get("icon"):
            names.add(s["icon"])
    out = {}
    for n in names:
        f = ICON_DIR / f"{n}.svg"
        if n and f.exists():
            out[n] = f.read_text()
    return out


def icon_exists(name: str) -> bool:
    return (ICON_DIR / f"{name}.svg").exists()


def _render_range(args) -> None:
    scenes, total, size, first, last, dest = args
    from playwright.sync_api import sync_playwright

    w, h = size
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg",
         "-i", "-", "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p", "-c:v", "libx264",
         "-preset", "fast", "-crf", "16", "-tune", "animation", "-r", str(FPS), str(dest)],
        stdin=subprocess.PIPE)
    exe = os.environ.get("CHROMIUM_PATH") or None
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe, args=["--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=w / 1920)
        page.add_init_script(f"window.ICONS = {json.dumps(_icons_for(scenes))};")
        page.goto((ANIM_DIR / "engine.html").resolve().as_uri())
        page.evaluate("document.fonts.ready")
        page.evaluate("([s, t]) => build(s, t)", [scenes, total])
        for i in range(first, last):
            page.evaluate("t => seek(t)", i / FPS)
            ff.stdin.write(page.screenshot(type="jpeg", quality=92))
        browser.close()
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed while encoding the animation")


def render_scenes(scenes: list[dict], total: float, size: tuple[int, int], dest: Path) -> Path:
    """scenes: [{"start": s, "end": s, "spec": {...}}]; writes a silent MP4 of length `total`.

    Frames are captured by one headless browser per CPU core, each taking a slice of the timeline."""
    from concurrent.futures import ProcessPoolExecutor

    frames = round(total * FPS)
    workers = max(1, min(os.cpu_count() or 1, 8, frames // 60 or 1))
    bounds = [frames * k // workers for k in range(workers + 1)]
    parts = [dest.with_name(f"{dest.stem}_part{k}.mp4") for k in range(workers)]
    jobs = [(scenes, total, size, bounds[k], bounds[k + 1], parts[k]) for k in range(workers)]
    with ProcessPoolExecutor(workers) as pool:
        list(pool.map(_render_range, jobs))
    listing = dest.with_name(f"{dest.stem}_parts.txt")
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(dest)], check=True)
    return dest
