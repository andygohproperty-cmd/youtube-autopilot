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

from .config import OUT_DIR, all_channels, append_record, history, load_channel

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
    plan = VideoPlan.model_validate(data["plan"])
    words = sum(len(s.narration.split()) for s in plan.segments)
    if not 0.6 * channel.target_words <= words <= 1.4 * channel.target_words:
        raise SystemExit(f"{path}: {words} words, expected about {channel.target_words}")
    if not plan.sources:
        raise SystemExit(f"{path}: no sources")
    return channel, plan, data.get("research_notes", "")


def produce(channel_id: str | None, dry_run: bool, force: bool, plan_file: str | None = None) -> None:
    from .render import render
    from .thumbnail import make_thumbnail
    from .voice import narrate

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

    texts = [s.narration for s in plan.segments]
    durations = narrate(channel, texts, work / "narration.wav")
    video = render(channel, [s.broll_query for s in plan.segments], texts, durations,
                   work / "narration.wav", work)
    thumb = make_thumbnail(work / "silent.mp4", plan.thumbnail_text, work / "thumbnail.jpg")
    print(f"Rendered {video} ({sum(durations):.0f}s)")
    if dry_run:
        return

    from .youtube import upload_private
    video_id = upload_private(channel, video, thumb, plan.title, plan.description, plan.tags,
                              plan.uses_realistic_ai_media)
    append_record("history", channel.id, {
        "video_id": video_id, "title": plan.title, "status": "awaiting_approval",
        "synthetic": plan.uses_realistic_ai_media, "seconds": round(sum(durations)),
    })
    meta = {"channel": channel.id, "video_id": video_id, "synthetic": plan.uses_realistic_ai_media}
    sources = "\n".join(f"- {u}" for u in plan.sources)
    body = f"""**{channel.name}** · {"Short" if channel.is_short else "Long video"} · {sum(durations) / 60:.1f} min

▶️ Watch (private): https://youtu.be/{video_id}
✏️ Edit in Studio: https://studio.youtube.com/video/{video_id}/edit

**Why it's original:** {plan.originality_note}

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
    cp = sub.add_parser("check-plan")
    cp.add_argument("plan_file")
    a = p.parse_args()
    if a.cmd == "produce":
        if not (a.channel or a.plan_file):
            p.error("produce needs --channel or --plan-file")
        produce(a.channel, a.dry_run, a.force, a.plan_file)
    elif a.cmd == "check-plan":
        channel, plan, _ = load_plan_file(a.plan_file)
        print(f"OK: {channel.id} · {plan.title}")
    elif a.cmd == "approve":
        approve(a.issue)
    elif a.cmd == "reject":
        reject(a.issue, a.reason)
    else:
        release_pending()


if __name__ == "__main__":
    main()
