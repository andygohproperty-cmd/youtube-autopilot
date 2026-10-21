"""The video plan: everything needed to render and publish one video."""
from pydantic import BaseModel


class Segment(BaseModel):
    narration: str        # what the narrator says, 1-2 short sentences
    broll_query: str      # 2-4 word stock-footage search, concrete and visual
    on_screen: str = ""   # optional big stat/keyword card, max ~4 words ("$5.3 BILLION")
    chapter: str = ""     # optional chapter title card shown as this segment starts (long videos)


class VideoPlan(BaseModel):
    title: str
    description: str
    tags: list[str]
    thumbnail_text: str   # 2-5 words, all caps friendly
    segments: list[Segment]
    sources: list[str]    # URLs the facts came from
    uses_realistic_ai_media: bool
    originality_note: str  # what makes this video different from what's already on YouTube
