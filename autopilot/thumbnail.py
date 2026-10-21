"""1280x720 thumbnail: a frame from the video plus bold, readable text."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .config import ASSETS_DIR

W, H = 1280, 720
ACCENT = (255, 214, 0)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def make_thumbnail(video: Path, text: str, dest: Path, at_fraction: float = 0.3) -> Path:
    frame = dest.with_suffix(".frame.jpg")
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True).stdout)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dur * at_fraction:.2f}",
                    "-i", str(video), "-frames:v", "1", str(frame)], check=True)

    img = Image.open(frame).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)))
    left, top = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((left, top, left + W, top + H))
    img = ImageEnhance.Brightness(img).enhance(0.55)
    img = ImageEnhance.Contrast(img).enhance(1.2)

    draw = ImageDraw.Draw(img)
    font_path = str(ASSETS_DIR / "fonts" / "Anton-Regular.ttf")
    text = text.upper()
    for size in range(170, 60, -10):
        font = ImageFont.truetype(font_path, size)
        lines = _wrap(draw, text, font, W - 140)
        if len(lines) <= 3:
            break
    line_h = font.size * 1.1
    y = (H - line_h * len(lines)) / 2
    for i, line in enumerate(lines):
        fill = ACCENT if i == len(lines) - 1 else (255, 255, 255)
        draw.text((70, y), line, font=font, fill=fill, stroke_width=8, stroke_fill=(0, 0, 0))
        y += line_h
    img.save(dest, "JPEG", quality=92)
    frame.unlink(missing_ok=True)
    return dest
