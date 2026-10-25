"""Blind voice test: the same ~60 s of script read by each free TTS engine, labelled A/B/C in a random
order, with the pipeline's voice polish and -14 LUFS loudness. The key is printed to the log only.

python tools/voice_test.py versions/<plan>.json out_dir
"""
import json
import random
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autopilot.run import load_plan_file  # noqa: E402
from autopilot.sound import loudnorm  # noqa: E402
from autopilot.voice import narrate  # noqa: E402

ENGINES = {   # all MIT or Apache-2.0: fine for a monetised channel
    "chatterbox (current, voice 3)": dict(tts="chatterbox", voice="default", exaggeration=0.6, speed=1.0),
    "chatterbox-turbo (built-in voice)": dict(tts="chatterbox-turbo", voice="default", speed=1.0),
    "kokoro-82m (af_heart)": dict(tts="kokoro", voice="af_heart", speed=1.0),
}


def main(plan_file: str, out: str) -> None:
    channel, plan, _ = load_plan_file(plan_file)
    texts, words = [], 0
    for seg in plan.segments:   # ~60 s: about 170 words of the hook
        texts.append(seg.narration)
        words += len(seg.narration.split())
        if words >= 165:
            break
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(ENGINES)
    random.shuffle(names)
    key = {}
    for label, name in zip("ABC", names):
        wav = out_dir / f"{label}.wav"
        try:
            narrate(replace(channel, **ENGINES[name]), texts, wav)
        except Exception as e:   # one engine failing should not sink the test
            print(f"{label}: {name} failed: {type(e).__name__}: {e}")
            continue
        loudnorm(wav)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "160k",
                        str(out_dir / f"voice-{label}.mp3")], check=True)
        wav.unlink()
        key[label] = name
    (out_dir / "script.txt").write_text(" ".join(texts))
    print("KEY " + json.dumps(key))


if __name__ == "__main__":
    main(*sys.argv[1:3])
