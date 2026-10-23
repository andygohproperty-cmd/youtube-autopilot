"""The video plan: everything needed to render and publish one video."""
from pydantic import BaseModel


class Segment(BaseModel):
    narration: str        # what the narrator says, 1-2 short sentences
    broll_query: str      # 2-4 word stock-footage search, concrete and visual
    on_screen: str = ""   # optional big stat/keyword card, max ~4 words ("$5.3 BILLION")
    chapter: str = ""     # optional chapter title card shown as this segment starts (long videos)
    visual: dict = {}     # animated channels: the motion-graphics scene for this segment (see ANIMATION.md)
    image: str = ""       # stock channels: a real photo from Wikimedia Commons, as a search or "File:..." title


class VideoPlan(BaseModel):
    title: str
    description: str
    tags: list[str]
    thumbnail_text: str   # 2-4 words, all caps friendly; *word* marks the one word on a yellow box
    segments: list[Segment]
    sources: list[str]    # URLs the facts came from
    uses_realistic_ai_media: bool
    originality_note: str  # what makes this video different from what's already on YouTube
    alt_titles: list[str] = []      # runner-up titles (shown on the approval issue for a swap or a Studio A/B test)
    thumbnail_segment: int = -1     # segment whose visual is the thumbnail background (-1: 30% into the video)
