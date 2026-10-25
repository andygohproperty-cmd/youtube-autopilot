"""Command line entry point used by the GitHub Actions workflows.

  python -m autopilot.run produce --channel weird_facts [--dry-run] [--force]
  python -m autopilot.run produce --plan-file queue/x.json   # plan written by the scheduled Claude task
  python -m autopilot.run check-plan queue/x.json
  python -m autopilot.run approve --issue 12
  python -m autopilot.run reject --issue 12 --reason "too slow"
  python -m autopilot.run release-pending
"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone

from .config import ASSETS_DIR, OUT_DIR, all_channels, append_record, history, load_channel

MARKER = re.compile(r"<!-- autopilot (\{.*?\}) -->")


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50]


def latest_status(channel_id: str) -> dict[str, dict]:
    """Most recent history record per video id."""
    state: dict[str, dict] = {}
    for rec in history(channel_id):
        if rec.get("video_id"):
            state[rec["video_id"]] = {**state.get(rec["video_id"], {}), **rec}
    return state


def load_plan_file(path: str):
    """A queued plan: {"channel": id, "research_notes": str, "plan": VideoPlan}."""
    from .plan import VideoPlan
    data = json.loads(open(path).read())
    channel = load_channel(data["channel"])
    # Style tests: a plan may override the channel's look and voice ({"visual_theme": "paper", "voice": ...}).
    for key, value in data.get("channel_overrides", {}).items():
        if not hasattr(channel, key):
            raise SystemExit(f"{path}: unknown channel override {key!r}")
        setattr(channel, key, value)
    plan = VideoPlan.model_validate(data["plan"])
    words = sum(len(s.narration.split()) for s in plan.segments)
    low = 0.6 * channel.target_words
    if not channel.is_short and 0 < channel.min_minutes <= channel.target_minutes:  # short style tests skip it
        low = max(low, channel.target_words * channel.min_minutes / channel.target_minutes)
    if not low <= words <= 1.4 * channel.target_words:
        raise SystemExit(f"{path}: {words} words, expected about {channel.target_words} (at least {int(low)})")
    if not plan.sources:
        raise SystemExit(f"{path}: no sources")
    return channel, plan, data.get("research_notes", "")


def _real_chapter_times(description: str, segments, durations: list[float]) -> str:
    """The writer can only estimate chapter timestamps; replace them with the narrated ones."""
    starts, t = [], 0.0
    for seg, dur in zip(segments, durations):
        if seg.chapter:
            starts.append((t, seg.chapter))
        t += dur
    if not starts or "Chapters:" not in description:
        return description
    head, _, rest = description.partition("Chapters:")
    tail = rest.lstrip("\n").split("\n\n", 1)
    old = tail[0].splitlines()
    first = old[0].split(" ", 1)[1] if old and old[0].startswith("0:00") and starts[0][0] > 0 else None
    lines = ([f"0:00 {first}"] if first else []) + [
        f"{'0:00' if i == 0 and not first else f'{int(s // 60)}:{int(s % 60):02d}'} {c}" for i, (s, c) in enumerate(starts)]
    return head + "Chapters:\n" + "\n".join(lines) + ("\n\n" + tail[1] if len(tail) > 1 else "")


def _packaging_problems(channel, plan) -> list[str]:
    """Title and thumbnail rules from WRITER.md ("Packaging"), checked before render."""
    out = []
    if len(plan.title) > 65:
        out.append(f"title is {len(plan.title)} characters; keep it under 65 (ideally 40-60)")
    title_words = set(plan.title.upper().replace("?", "").split())
    for field, text in (("thumbnail_text", plan.thumbnail_text), ("alt_thumbnail_text", plan.alt_thumbnail_text)):
        if field == "alt_thumbnail_text" and not text:
            continue
        words = text.replace("*", "").split()
        if not 1 <= len(words) <= 4:
            out.append(f"{field} has {len(words)} words; use 2-4")
        if text.count("*") not in (0, 2):
            out.append(f"{field}: mark exactly one word as *word*")
        if len(words) > 1 and set(w.upper() for w in words) <= title_words:
            out.append(f"{field} only repeats the title; it should add to it")
    if plan.alt_thumbnail_text and plan.alt_thumbnail_text.replace("*", "").upper() == plan.thumbnail_text.replace("*", "").upper():
        out.append("alt_thumbnail_text must differ from thumbnail_text (it is option B for Test & Compare)")
    if not channel.is_short and not plan.alt_thumbnail_text:
        out.append("give alt_thumbnail_text (thumbnail option B for Test & Compare)")
    if not channel.is_short and len(plan.alt_titles) < 2:
        out.append("give at least 2 alt_titles (runner-ups from the title shortlist)")
    if not -1 <= plan.thumbnail_segment < len(plan.segments):
        out.append(f"thumbnail_segment {plan.thumbnail_segment} is out of range")
    if not -1 <= plan.alt_thumbnail_segment < len(plan.segments):
        out.append(f"alt_thumbnail_segment {plan.alt_thumbnail_segment} is out of range")
    return out


def _visual_problems(channel, plan) -> list[str]:
    """Animated channels: every segment needs a `visual` from ANIMATION.md, using icons that exist."""
    from .animate import icon_exists

    known = {"scene", "icons", "stat", "bars", "pie", "receipt", "text", "versus", "list", "quote", "floorplan"}
    out = []
    for i, seg in enumerate(plan.segments):
        v = seg.visual
        if not v:
            out.append(f"segment {i}: missing `visual`")
            continue
        if v.get("type") not in known:
            out.append(f"segment {i}: unknown visual type {v.get('type')!r}")
        missing = sorted(n for n in _names(v) if not icon_exists(n))
        if missing:
            out.append(f"segment {i}: unknown icons {missing} (see assets/anim/icons)")
    return out


def _names(x) -> set[str]:
    """Icon names a visual mentions (same keys the renderer reads)."""
    found = set()
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ("icon", "prop") and isinstance(v, str):
                found.add(v)
            elif k in ("icons", "corners", "center") and isinstance(v, list):
                found.update(i for i in v if isinstance(i, str))
            else:
                found |= _names(v)
    elif isinstance(x, list):
        for v in x:
            found |= _names(v)
    return found


def _thumbnail(channel, plan, durations, leads, work, segment, text, dest, fallback=0.3):
    """A thumbnail from a frame late in `segment` (or `fallback` of the way in), with `text` on it."""
    from .thumbnail import make_thumbnail

    at, side = None, "left"
    if segment >= 0:   # late in the chosen segment, once its scene has played out
        at = sum(durations[:segment]) + leads[segment] + (durations[segment] - leads[segment]) * 0.6
        actors = plan.segments[segment].visual.get("actors") or []
        if actors and sum(a.get("to", a.get("x", 0.5)) for a in actors) / len(actors) < 0.5:
            side = "right"            # cartoon people on the left: words go on the right
    src = work / "silent.mp4"
    if channel.visual_style == "remotion":   # the picture has captions burned in: take a clean frame
        from .remotion import remotion_still
        src, at = remotion_still(work, sum(durations) * fallback if at is None else at,
                                 dest.with_name(dest.stem + "-src.png")), 0.0
    return make_thumbnail(src, text, dest, at, side)


def _share_thumbnails(video_id: str, files: list) -> list[str]:
    """Put the thumbnail options on the `previews` branch so the approval issue can show them."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return []
    tree = OUT_DIR / "previews-tree"
    try:
        subprocess.run(["git", "fetch", "-q", "origin", "previews"], check=True)
        subprocess.run(["git", "worktree", "add", "-q", "-f", "-B", "previews", str(tree), "origin/previews"], check=True)
        names = []
        for i, f in enumerate(files):
            name = f"thumbs/{video_id}-{'ab'[i]}.jpg"
            (tree / "thumbs").mkdir(exist_ok=True)
            (tree / name).write_bytes(f.read_bytes())
            names.append(name)
        git = ["git", "-C", str(tree), "-c", "user.name=autopilot", "-c", "user.email=autopilot@users.noreply.github.com"]
        subprocess.run(git + ["add", *names], check=True)
        subprocess.run(git + ["commit", "-qm", f"thumbnails: {video_id}"], check=True)
        for _ in range(5):
            subprocess.run(git + ["pull", "-q", "--rebase", "origin", "previews"])
            if subprocess.run(git + ["push", "-q", "origin", "HEAD:previews"]).returncode == 0:
                return [f"https://github.com/{repo}/blob/previews/{n}?raw=true" for n in names]
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"Could not share thumbnails: {e}")
    finally:
        subprocess.run(["git", "worktree", "remove", "-f", str(tree)], capture_output=True)
    return []


def produce(channel_id: str | None, dry_run: bool, force: bool, plan_file: str | None = None) -> None:
    from .render import render
    from .voice import narrate_cached as narrate

    if plan_file:
        channel, plan, notes = load_plan_file(plan_file)
    else:
        from .llm import research, write_plan
        channel = load_channel(channel_id)
        if not force and not channel.produces_today():
            print(f"{channel.id}: not a production day, skipping")
            return
        notes = research(channel)
        plan = write_plan(channel, notes)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    work = OUT_DIR / channel.id / f"{stamp}-{_slug(plan.title)}"
    work.mkdir(parents=True, exist_ok=True)
    (work / "research.md").write_text(notes)
    (work / "plan.json").write_text(plan.model_dump_json(indent=2))

    from .render import leads_for
    texts = [s.narration for s in plan.segments]
    leads = leads_for(channel, plan.segments)
    durations = narrate(channel, texts, work / "narration.wav", leads)
    video, tracks, photo_credits = render(channel, plan.segments, durations, leads, work / "narration.wav", work,
                                          hook_text=plan.thumbnail_text.replace("*", ""), title=plan.title)
    thumb = _thumbnail(channel, plan, durations, leads, work, plan.thumbnail_segment, plan.thumbnail_text,
                       work / "thumbnail.jpg")
    thumb_b = None
    if plan.alt_thumbnail_text:   # option B for YouTube's thumbnail Test & Compare
        seg = plan.alt_thumbnail_segment if plan.alt_thumbnail_segment >= 0 else plan.thumbnail_segment
        thumb_b = _thumbnail(channel, plan, durations, leads, work, seg, plan.alt_thumbnail_text,
                             work / "thumbnail-b.jpg", fallback=0.55)
    if tracks:  # licensed tracks from assets/music may need credit (assets/music/credits.json)
        credits_file = ASSETS_DIR / "music" / "credits.json"
        credits = json.loads(credits_file.read_text()) if credits_file.exists() else {}
        plan.description += "\n\nMusic: " + "; ".join(credits.get(t, t) for t in tracks)
    if photo_credits:  # Wikimedia Commons photos: licences require credit
        lines = [f"- {c}" for c in dict.fromkeys(photo_credits)]
        while lines and len(plan.description) + sum(len(x) + 1 for x in lines) > 4700:   # YouTube max is 5000
            lines.pop()
        plan.description += "\n\nPhotos (Wikimedia Commons):\n" + "\n".join(lines)
    plan.description = _real_chapter_times(plan.description, plan.segments, durations)
    print(f"Rendered {video} ({sum(durations):.0f}s)")
    if dry_run:
        return

    from .youtube import upload_private
    video_id, thumb_set = upload_private(channel, video, thumb, plan.title, plan.description, plan.tags,
                              plan.uses_realistic_ai_media)
    append_record("history", channel.id, {
        "video_id": video_id, "title": plan.title, "status": "awaiting_approval",
        "synthetic": plan.uses_realistic_ai_media, "seconds": round(sum(durations)),
    })
    meta = {"channel": channel.id, "video_id": video_id, "synthetic": plan.uses_realistic_ai_media}
    sources = "\n".join(f"- {u}" for u in plan.sources)
    thumbs = ""
    if thumb_b:
        urls = _share_thumbnails(video_id, [thumb, thumb_b])
        pics = " ".join(f"![{k}]({u})" for k, u in zip("AB", urls)) if urls else "(thumbnail.jpg and thumbnail-b.jpg in the run)"
        thumbs = (f"\n**Thumbnails** A (set) and B: {pics}\nRun both in Studio > Test & Compare: "
                  f"https://studio.youtube.com/video/{video_id}/edit\n")
    body = f"""**{channel.name}** · {"Short" if channel.is_short else "Long video"} · {sum(durations) / 60:.1f} min

▶️ Watch (private): https://youtu.be/{video_id}
✏️ Edit in Studio: https://studio.youtube.com/video/{video_id}/edit
{"" if thumb_set or channel.is_short else "⚠️ Custom thumbnail not set: verify the channel at https://www.youtube.com/verify, then upload thumbnail.jpg in Studio."}

**Why it's original:** {plan.originality_note}
{thumbs}{"" if not plan.alt_titles else chr(10) + "**Other titles** (swap in Studio, or run them as a title test): " + " · ".join(plan.alt_titles) + chr(10)}
**Description**
{plan.description}

**Fact sources**
{sources}

---
Reply **/approve** to schedule it, or **/reject your reason** to drop it (the reason trains the next videos).

<!-- autopilot {json.dumps(meta)} -->"""
    _gh("issue", "create", "--title", f"[{channel.name}] {plan.title}", "--body", body,
        "--label", "approval")


def _issue_meta(issue: int) -> dict:
    body = json.loads(_gh("issue", "view", str(issue), "--json", "body"))["body"]
    m = MARKER.search(body)
    if not m:
        raise SystemExit(f"Issue #{issue} is not an autopilot approval issue")
    return json.loads(m.group(1))


def _schedule(channel_id: str, video_id: str, synthetic: bool) -> datetime:
    from .youtube import next_slot, schedule
    channel = load_channel(channel_id)
    taken = [r["publish_at"] for r in latest_status(channel_id).values() if r.get("publish_at")]
    slot = next_slot(channel, taken)
    schedule(channel, video_id, slot, synthetic)
    append_record("history", channel_id, {"video_id": video_id, "status": "scheduled",
                                          "publish_at": slot.isoformat()})
    return slot


def approve(issue: int) -> None:
    meta = _issue_meta(issue)
    if os.environ.get("AUDIT_PASSED", "").lower() == "true":
        slot = _schedule(meta["channel"], meta["video_id"], meta["synthetic"])
        msg = f"✅ Approved. Goes public {slot:%a %d %b %H:%M} UTC."
    else:
        append_record("history", meta["channel"], {"video_id": meta["video_id"],
                                                   "status": "approved_pending_audit"})
        msg = ("✅ Approved. It stays private until the YouTube API audit passes, "
               "then it is scheduled automatically.")
    _gh("issue", "comment", str(issue), "--body", msg)
    _gh("issue", "close", str(issue))


def reject(issue: int, reason: str) -> None:
    meta = _issue_meta(issue)
    title = latest_status(meta["channel"]).get(meta["video_id"], {}).get("title", "")
    append_record("history", meta["channel"], {"video_id": meta["video_id"], "status": "rejected"})
    append_record("feedback", meta["channel"], {"title": title, "reason": reason or "no reason given"})
    _gh("issue", "comment", str(issue), "--body", "❌ Rejected. Feedback saved for future videos.")
    _gh("issue", "close", str(issue), "--reason", "not planned")


def release_pending() -> None:
    for channel in all_channels():
        for vid, rec in latest_status(channel.id).items():
            if rec.get("status") == "approved_pending_audit":
                slot = _schedule(channel.id, vid, rec.get("synthetic", False))
                print(f"{channel.id}: {vid} scheduled {slot.isoformat()}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("produce")
    pr.add_argument("--channel")
    pr.add_argument("--plan-file")
    pr.add_argument("--dry-run", action="store_true")
    pr.add_argument("--force", action="store_true")
    ap = sub.add_parser("approve")
    ap.add_argument("--issue", type=int, required=True)
    rj = sub.add_parser("reject")
    rj.add_argument("--issue", type=int, required=True)
    rj.add_argument("--reason", default="")
    sub.add_parser("release-pending")
    na = sub.add_parser("narrate")       # voice only (fills NARRATION_CACHE for a later render job)
    na.add_argument("--plan-file", required=True)
    cp = sub.add_parser("check-plan")
    cp.add_argument("plan_file")
    a = p.parse_args()
    if a.cmd == "produce":
        if not (a.channel or a.plan_file):
            p.error("produce needs --channel or --plan-file")
        produce(a.channel, a.dry_run, a.force, a.plan_file)
    elif a.cmd == "narrate":
        from .render import leads_for
        from .voice import narrate_cached
        channel, plan, _ = load_plan_file(a.plan_file)
        out = OUT_DIR / "narration.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        durations = narrate_cached(channel, [s.narration for s in plan.segments], out, leads_for(channel, plan.segments))
        print(f"narrated {sum(durations):.0f}s")
    elif a.cmd == "check-plan":
        channel, plan, _ = load_plan_file(a.plan_file)
        problems = _packaging_problems(channel, plan)
        problems += _visual_problems(channel, plan) if channel.visual_style == "animated" else []
        if channel.visual_style == "remotion":
            from .remotion import plan_problems
            problems += plan_problems(plan)
        if problems:
            raise SystemExit("Fix the plan:\n" + "\n".join(problems))
        print(f"OK: {channel.id} · {plan.title}")
    elif a.cmd == "approve":
        approve(a.issue)
    elif a.cmd == "reject":
        reject(a.issue, a.reason)
    else:
        release_pending()


if __name__ == "__main__":
    main()
