"""1280x720 thumbnail: a frame from the video plus 2-4 huge words.

Style studied from the top faceless business channels (How Money Works, Logically Answered, Company Man,
ModernMBA, MagnatesMedia, Oct 2026): one bright subject, 2-4 condensed all-caps words with a thick black
outline on the side away from the subject, and one key word or number on a yellow box (`*word*` in the text marks it).
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .config import ASSETS_DIR

W, H = 1280, 720
ACCENT = (255, 214, 0)
TEXT_W = int(W * 0.62)     # text column on one side; the subject stays visible on the other


def _wrap(draw: ImageDraw.ImageDraw, words: list[str], font: ImageFont.FreeTypeFont, max_w: int) -> list[list[str]]:
    lines, line = [], []
    for word in words:
        trial = " ".join(line + [word]).replace("*", "")
        if draw.textlength(trial, font=font) <= max_w or not line:
            line.append(word)
        else:
            lines.append(line)
            line = [word]
    return lines + [line]


def _frame(video: Path, dest: Path, at_seconds: float | None) -> Image.Image:
    if at_seconds is None:
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
            capture_output=True, text=True, check=True).stdout)
        at_seconds = dur * 0.3
    frame = dest.with_suffix(".frame.jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at_seconds:.2f}",
                    "-i", str(video), "-frames:v", "1", str(frame)], check=True)
    img = Image.open(frame).convert("RGB")
    frame.unlink(missing_ok=True)
    return img


def make_thumbnail(video: Path, text: str, dest: Path, at_seconds: float | None = None,
                   side: str = "left") -> Path:
    """`side`: where the words go; the frame's subject should be on the other side."""
    img = _frame(video, dest, at_seconds)
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)))
    left, top = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((left, top, left + W, top + H))
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Color(img).enhance(1.3)    # top thumbnails are saturated, not dimmed

    # Dark gradient behind the text column only, so the subject stays bright.
    ramp = [int(190 * max(0.0, 1 - x / (W * 0.75))) for x in range(W)]
    if side == "right":
        ramp.reverse()
    shade = Image.new("L", (W, H))
    shade.putdata(ramp * H)
    img = Image.composite(Image.new("RGB", (W, H)), img, shade)

    draw = ImageDraw.Draw(img)
    font_path = str(ASSETS_DIR / "fonts" / "Anton-Regular.ttf")
    words = text.upper().split()
    marked = any(w.startswith("*") or w.endswith("*") for w in words)
    for size in range(200, 60, -8):
        font = ImageFont.truetype(font_path, size)
        lines = _wrap(draw, words, font, TEXT_W)
        if len(lines) <= 3 and size * 1.08 * len(lines) <= H - 100:
            break
    line_h = font.size * 1.08
    space = draw.textlength(" ", font=font)
    pad = font.size * 0.08
    y = (H - line_h * len(lines)) / 2
    hot = False
    for i, line in enumerate(lines):
        # Words between *...* are "hot": black on one yellow box. Unmarked text: the last line is yellow.
        runs = []
        for word in line:
            starts, ends = word.startswith("*"), word.endswith("*") and len(word) > 1
            hot = hot or starts
            runs.append((word.strip("*"), hot))
            hot = hot and not ends
        line_w = sum(draw.textlength(w, font=font) for w, _ in runs) + space * (len(runs) - 1)
        x = 60 if side == "left" else W - 60 - line_w
        box_start = None
        for j, (word, is_hot) in enumerate(runs):
            ww = draw.textlength(word, font=font)
            if is_hot and box_start is None:
                box_start = x
            if is_hot and (j == len(runs) - 1 or not runs[j + 1][1]):
                box_top = y + font.size * 0.12
                draw.rectangle((box_start - pad, box_top, x + ww + pad, box_top + font.size), fill=ACCENT)
                box_start = None
            x += ww + space
        x = 60 if side == "left" else W - 60 - line_w
        for word, is_hot in runs:
            if is_hot:
                draw.text((x, y), word, font=font, fill=(0, 0, 0))
            else:
                fill = ACCENT if not marked and i == len(lines) - 1 else (255, 255, 255)
                draw.text((x, y), word, font=font, fill=fill, stroke_width=9, stroke_fill=(0, 0, 0))
            x += draw.textlength(word, font=font) + space
        y += line_h
    img.save(dest, "JPEG", quality=92)
    return dest
