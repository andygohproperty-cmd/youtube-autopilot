"""Claude: topic research and the full video plan (script, shots, metadata)."""
import os

import anthropic
from pydantic import BaseModel

from .config import Channel, feedback, history

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()


class Segment(BaseModel):
    narration: str        # what the narrator says, 1-3 sentences
    broll_query: str      # 2-4 word stock-footage search, concrete and visual


class VideoPlan(BaseModel):
    title: str
    description: str
    tags: list[str]
    thumbnail_text: str   # 2-5 words, all caps friendly
    segments: list[Segment]
    sources: list[str]    # URLs the facts came from
    uses_realistic_ai_media: bool
    originality_note: str  # what makes this video different from what's already on YouTube


def _past_titles(channel: Channel, limit: int = 60) -> list[str]:
    return [h["title"] for h in history(channel.id)][-limit:]


def _feedback_notes(channel: Channel, limit: int = 15) -> list[str]:
    return [f"- {f['title']}: {f['reason']}" for f in feedback(channel.id)][-limit:]


def research(channel: Channel) -> str:
    """Pick a fresh topic and gather sourced facts with web search."""
    past = "\n".join(f"- {t}" for t in _past_titles(channel)) or "(none yet)"
    prompt = f"""You are the researcher for the YouTube channel "{channel.name}".

Niche: {channel.niche}
Avoid: {channel.avoid}

Topics already covered (do not repeat or closely overlap):
{past}

1. Search the web for what this audience is curious about right now and pick ONE fresh topic
   with strong viewer interest that the channel hasn't covered.
2. Research it properly: collect specific, verifiable facts, numbers, dates and quotes,
   each with its source URL. Prefer primary or reputable sources.
3. Note one angle that makes this take more useful or surprising than existing videos.

Reply with: TOPIC, ANGLE, then a bullet list of facts with source URLs."""
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}]
    for _ in range(5):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "medium"},
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"Research refused: {resp.stop_details}")
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": resp.content})
    return "\n".join(b.text for b in resp.content if b.type == "text")


def write_plan(channel: Channel, notes: str) -> VideoPlan:
    """Turn research notes into a complete, policy-safe video plan."""
    fb = "\n".join(_feedback_notes(channel)) or "(none yet)"
    if channel.is_short:
        length = (f"A YouTube Short of about {channel.target_seconds} seconds "
                  f"(~{channel.target_words} spoken words) in 5-8 segments.")
    else:
        length = (f"A long-form video of about {channel.target_minutes:g} minutes "
                  f"(~{channel.target_words} spoken words) in 25-45 segments.")
    prompt = f"""Write the complete video plan for the YouTube channel "{channel.name}".

Format: {length}
Niche: {channel.niche}
Style: {channel.style}
Avoid: {channel.avoid}

Feedback from the channel owner on earlier videos (apply it):
{fb}

Research notes:
{notes}

Rules (YouTube policy, non-negotiable):
- Use only facts from the research notes; never invent numbers or quotes.
- Original script and structure; not a template others could swap a noun into.
- Title and thumbnail text must be honest about what the video delivers. Title under 70 characters.
- Description: 2-3 sentence summary, then "Sources:" with the URLs{", then chapters with 0:00-style timestamps estimated at 150 words per minute" if not channel.is_short else ""}.
  Mention that narration is AI-generated.{" Add #Shorts at the end." if channel.is_short else ""}
- broll_query: concrete things a stock library has (e.g. "container ship port", "city traffic night").
  Never real people's names or logos. Vary shots; no two consecutive queries alike.
- 8-15 tags, no keyword stuffing.
- uses_realistic_ai_media is false (we only use real stock footage and a generic AI narrator)."""
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=VideoPlan,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Plan refused: {resp.stop_details}")
    return resp.parsed_output
