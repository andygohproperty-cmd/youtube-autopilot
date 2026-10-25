# Top faceless business channels: what their best videos do (2026-10-23)

Studied the 12 most-viewed videos of each channel (YouTube "Popular" tab) and the opening 60-75 s
transcripts of 7 of them. Applied in `channels/biz_explainers.yaml`, `WRITER.md` ("Packaging and hooks"),
`autopilot/llm.py`, `autopilot/thumbnail.py` and `check-plan`.

## The channels' top videos

| Channel | Subs | Top videos (views) | Typical length |
|---|---|---|---|
| How Money Works | 1.76M | Your Job Achieves Nothing... (probably) 6.1M · How The Wolf of Wall Street Scam Actually Worked 4.8M · If Nobody Can Afford A Home... Who's Going To Buy Them? 4.0M · The (Overdue) Collapse Of Short Term Rentals 3.9M | 10-14 min |
| Logically Answered | 929K | Here's What Happened To The Pirate Bay's Founders 6.2M · Why Dubai Has to Truck Poop Out From the Burj Khalifa 4.1M · From Bankruptcy To Billions: The Rebirth Of Nokia 2.6M · From $10 Billion To Nothing: How Wish.com Lost Everything 1.9M | 8-17 min |
| Company Man | 1.8M | The Decline of Chuck E. Cheese's...What Happened? 6.4M · The Decline of Kmart...What Happened? 5.3M · The Decline of Pizza Hut...What Happened? 4.4M (9 of top 12 use this exact title) | 11-14 min |
| ModernMBA | 834K | Fried Chicken Wars: The Fall of KFC in America 3.5M · The Timeless Business of Steakhouses 3.4M · Why Airbnb Fails to Disrupt the Hotel Industry 3.4M · How Boba Shops Really Make Money 1.6M | 25-30+ min |
| MagnatesMedia | 1.86M | The Secret Chinese Company That Owns Everything 12M · Rockefeller: The World's First Billionaire 7.7M · The Disturbing History of Coca-Cola 7.6M · How WhatsApp Makes Money 5.2M | 15-75 min |

## Findings

**Topics**
- Brands everyone knows and has feelings about (fast food, retail, apps), or a money question about the viewer's own life (jobs, homes).
- A tension in every one: decline, collapse, scandal, hidden money machine, paradox. Evergreen, not news.

**Titles**
- Subject in the first 3-4 words, one tension word, mostly 40-60 characters.
- Repeatable franchises win: Company Man's "The Decline of X...What Happened?" is 9 of his top 12; ModernMBA's "The [adjective] Business of X".
- Formulas: paradox question ("If nobody can afford... who's going to buy?"), "How X (really) makes money", "What happened to X", "From $10B to nothing", "Why X can't survive", "The secret/rigged/disturbing X".
- How Money Works adds human hedges: "(probably)", "(sort of)", "(Overdue)", ellipses.

**Thumbnails**
- One subject, 2-4 huge condensed all-caps words, thick black outline; text adds to the title, never repeats it ("THE RISE OF BULLS\*\*T JOBS" on "Your Job Achieves Nothing").
- A highlighted key word or number on a yellow box (Logically Answered: "I AM *WORTH* ?", "$0.4B vs $2B").
- Bright, saturated images; MagnatesMedia goes red/fire/dark for "dark truth" stories.
- Company Man uses one fixed template for the whole series (instant recognition).

**Hooks (first 30-60 s)**
- Line 1 states the title's promise: "How does WhatsApp make money?", "What do you do for a living?", "If nobody can afford to buy a house, how do they keep getting more expensive?"
- Make it about the viewer: "affects every single one of us", "if you're in the 75% of my audience that doesn't own a home".
- Hard numbers early (Company Man: 56% of sales from games, 44% food, by ~20 s).
- Tease: "a rabbit hole much darker than I would have imagined"; "at times inspiring, at times chilling".
- Jump into the story with a date: "It's 2009. The iPhone came out a couple of years ago..."
- ModernMBA is the exception: slow, personal opening, but its videos are 25-30 min deep dives.

**Pacing and visuals**
- Narration roughly 160-200 words per minute, conversational, first person allowed ("I used to love this place").
- How Money Works / Logically Answered: stock footage + charts/maps on every number; MagnatesMedia: cinematic dark grade, dramatic music, chapter cards; ModernMBA: clean, bright motion graphics and maps.
- Long-form, no Shorts on the main channels' top lists (fits the long-only rule).

## What changed in the pipeline
- `biz_explainers.yaml`: 10-min target (8-min minimum for mid-roll ads), new style brief with the hook shape and story arc. Visual style untouched (Meta A/B/C pick is still open).
- `WRITER.md`: "Packaging and hooks" section: topic rule, 8 titles → 1 + 2 runner-ups, title formulas, thumbnail rules, 5-step hook, story-arc structure, pacing.
- Plan fields: `alt_titles` (shown on the approval issue for a swap or Studio title test), `thumbnail_segment` (which scene becomes the thumbnail), `*word*` highlight in `thumbnail_text`.
- `thumbnail.py`: brighter, saturated frame; dark gradient only behind the words; words on the side away from the cartoon people; yellow box on the key word.
- `check-plan`: title ≤ 65 chars, 2-4 thumbnail words that don't just repeat the title, 2+ alt titles, minimum length.
