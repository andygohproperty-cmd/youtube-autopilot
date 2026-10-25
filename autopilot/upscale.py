"""Photo upscaling with Real-ESRGAN (realesr-general-x4v3, BSD-3), on CPU through spandrel.

Commons photos are often 800-1600 px wide; full-screen on a 1440p video they look soft. Photos below
MIN_WIDTH are upscaled 4x in tiles, then resized to TARGET_WIDTH. Needs torch + spandrel; without
them, or if anything fails, the photo is used as it is.
"""
import urllib.request
from pathlib import Path

from PIL import Image

from .config import ROOT

MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth"
MODEL = ROOT / "models" / "realesr-general-x4v3.pth"
MIN_WIDTH = 2000
TARGET_WIDTH = 2560
TILE, PAD = 384, 16

_model = None
_failed = False


def _load():
    global _model, _failed
    if _model is not None or _failed:
        return _model
    try:
        import torch
        from spandrel import ModelLoader

        if not MODEL.exists():
            MODEL.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(MODEL_URL, MODEL)
        _model = ModelLoader().load_from_file(str(MODEL)).eval()
        torch.set_grad_enabled(False)
    except Exception as e:
        print(f"photo upscaling unavailable ({type(e).__name__}: {e})")
        _failed = True
    return _model


def _run(model, im: Image.Image) -> Image.Image:
    """4x upscale in overlapping tiles, so memory stays small whatever the photo size."""
    import numpy as np
    import torch

    x = torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0)
    _, _, h, w = x.shape
    s = model.scale
    out = torch.zeros(1, 3, h * s, w * s)
    for top in range(0, h, TILE):
        for left in range(0, w, TILE):
            t0, l0 = max(top - PAD, 0), max(left - PAD, 0)
            t1, l1 = min(top + TILE + PAD, h), min(left + TILE + PAD, w)
            y = model(x[:, :, t0:t1, l0:l1])
            bh, bw = min(TILE, h - top), min(TILE, w - left)
            out[:, :, top * s:(top + bh) * s, left * s:(left + bw) * s] = \
                y[:, :, (top - t0) * s:(top - t0 + bh) * s, (left - l0) * s:(left - l0 + bw) * s]
    arr = (out[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255.0).round().astype("uint8")
    return Image.fromarray(arr)


def upscale(path: Path) -> bool:
    """Upscale a small photo in place; True if it was changed."""
    with Image.open(path) as im:
        if im.width >= MIN_WIDTH or im.width < 200 or im.width * im.height > 2_500_000:
            return False
        im = im.convert("RGB")
    model = _load()
    if model is None:
        return False
    try:
        big = _run(model, im)
        if big.width > TARGET_WIDTH:
            big = big.resize((TARGET_WIDTH, round(big.height * TARGET_WIDTH / big.width)), Image.LANCZOS)
        big.save(path, quality=92)
        print(f"upscaled {path.name}: {im.width}px -> {big.width}px")
        return True
    except Exception as e:
        print(f"upscale failed for {path.name}: {e}")
        return False
