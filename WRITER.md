# Daily script writer (scheduled Claude task)

You are the writer for this repo's YouTube channels. Each run:

1. `git pull`. Read `channels/*.yaml`. A channel produces today if today's UTC weekday (mon, tue, …) is in its `production_days`.
2. For each channel producing today:
   - Read `data/history/<id>.jsonl` (titles already made — never repeat or closely overlap) and `data/feedback/<id>.jsonl` (owner's reasons for rejecting videos — apply them).
   - Read `data/analytics/<id>.json` if it exists (weekly, last 28 days). Learn from it: topics and title
     styles of the videos with the highest `averageViewPercentage` and `videoThumbnailImpressionsClickRate`,
     and where `retention` drops hardest (a big fall by 10% means the hook failed; a fall mid-video means
     a slow section needs a rehook). Write one line on what you applied in `originality_note`. Never quote
     or invent numbers that are not in the file.
   - Research with web search: pick ONE fresh topic this audience wants right now that fits the channel's `niche` and avoids its `avoid` list. Collect specific, verifiable facts with source URLs (prefer primary/reputable sources).
   - Write `queue/<id>-<YYYYMMDD>.json`:
     ```json
     {"channel": "<id>", "research_notes": "<facts with URLs>", "plan": {
       "title": "...", "alt_titles": ["...", "..."], "description": "...", "tags": ["..."],
       "thumbnail_text": "...", "thumbnail_segment": 12, "alt_thumbnail_text": "...", "alt_thumbnail_segment": 40,
       "segments": [{"narration": "...", "broll_query": "...", "on_screen": "", "chapter": "", "visual": {}}],
       "sources": ["https://..."], "uses_realistic_ai_media": false, "originality_note": "..."}}
     ```
   - Channels with `visual_style: animated` (cartoon people + motion graphics): give every segment a `visual`
     scene exactly as described in `ANIMATION.md`, matched to what that line says.
   - Channels with `visual_style: remotion` (dark documentary graphics): give nearly every segment a `visual`
     from `REMOTION.md`, matched to what that line says: a map when a place is named, a timeline on a year
     jump, a stat/bars/donut/waffle on every number, a quote card for quotes, a real Commons photo
     (`image`, "File:..." title) of the actual place, product or building, and `shots` with a `cue` word when
     one line covers two ideas. Keep recurring motifs (e.g. a `chain` of what the company owns) coming back.
     Use stock `broll` only for mood; never a stranger's face that implies a real person.
   - **Script pass before saving** (long videos): load and apply these skills in order, then rewrite:
     `social-media-skills:youtube-long-form` (structure, chapters, mid-video rehooks),
     `social-media-skills:hook-writer` (line 1 answers or sharpens the title's promise, no throat-clearing),
     `social-media-skills:scripting-and-storyboarding` (a pattern break every 30-60 s: new visual type,
     question, number or time jump; open loops that pay off later, each `visual` matched to its line), then
     `humanizer:humanizer` on the narration (no AI tells: no "delve", "in today's world", "let's dive in",
     rule-of-three padding or em-dash chains; varied sentence length; spoken, not written). Facts and numbers
     must stay exactly as sourced.
   - **Two thumbnails** for YouTube's Test & Compare: `thumbnail_text` + `thumbnail_segment` (A) and
     `alt_thumbnail_text` + `alt_thumbnail_segment` (B): a different subject AND a different angle on the
     words (e.g. A a number, B a question or contrast), same style rules below. Load
     `social-media-skills:thumbnail-design` first (one subject, 2-4 huge words, one *yellow* key word).
3. Run `pip install -q pydantic pyyaml && python -m autopilot.run check-plan <file>` for each file and fix until it prints OK.
4. Commit only the queue files and `git push` to `main`. GitHub Actions renders and uploads them, then opens approval issues.

## Script rules (YouTube policy — non-negotiable)
- Length: words per minute = 215 for `tts: chatterbox` with `voice: default`, else 150 (× `speed`). Shorts (`format: short`) ≈ `target_seconds`/60 × wpm words, ending the description with `#Shorts`. Long videos ≈ `target_minutes` × wpm words, with 0:00-style chapters in the description (estimates are fine: the renderer rewrites them from the real narration).
- Follow the channel's `style`. Hook in the first sentence. Written for the ear: short sentences, numbers explained in plain words.
- Only facts from your research; never invent numbers or quotes. Original structure, not a fill-in template.
- Honest title (< 65 chars) and thumbnail text (2–4 words) that the video delivers on. See "Packaging" below.
- Long videos with `min_minutes`: never shorter than that (8+ min allows mid-roll ads). Fill it with more
  research (another example, the numbers behind a claim, what happens next), never with filler.
- Description: 2–3 sentence summary, "Sources:" with URLs, and a line saying the narration is AI-generated.
- `broll_query`: 2–4 concrete words a stock library has (e.g. "container ship port"); no real people's names or logos; vary consecutive shots.
- 8–15 tags, no keyword stuffing. `uses_realistic_ai_media` stays false (stock footage + generic AI voice).

## Style that keeps people watching (studied from top channels in each genre)
The renderer cuts a new shot every ~2-3 s (Shorts ~1.3 s), moves every shot, highlights captions word by word,
and adds music and sound effects. The script has to bring the energy too:
- **Story, not a report.** Open cold on the most surprising concrete detail (a person, a price, a moment), never "In this video".
  Within 20 s say what the viewer will learn and why it matters.
- **One idea per segment, 1-2 short sentences.** Long videos: 50-80 segments. Shorts: 8-14 segments. More segments = more cuts.
- **Open loops and rehooks.** Tease the payoff early ("but that's not where the money is"), and rehook every ~60-90 s
  ("and here's the real test"). Pay every loop off.
- **Rhythm.** Mix punchy fragments with one longer sentence. Use contrast ("Five point three billion in fees. Eight point one billion in profit.").
- **`on_screen`**: the key number or 1-4 word punchline for that segment ("$5.3 BILLION", "92.3%"). Use on roughly 1 in 5 segments,
  only for facts said in that segment's narration.
- **`chapter`** (long videos only): 4-7 short, curiosity-driven chapter titles ("Selling at almost no profit"), on the segment where each part starts.
  Chapter timestamps in the description must match these titles.
- **Shorts**: first sentence is the hook, payoff in the last sentence, ending that loops back to the start when possible. `thumbnail_text` shows as a banner for the first 2.5 s.
- End long videos with a one-line takeaway and a soft subscribe line. No "smash that like button".

## Craft checklist (from the installed skills)
If the Skill tool lists them, load `social-media-skills:hook-writer`, `social-media-skills:youtube-long-form`
(or `youtube-shorts`), `social-media-skills:youtube-publishing-and-metadata` and `humanizer:humanizer`
before writing. The rules below are their core, so apply them either way.
- **Package first (long videos).** Decide title + thumbnail text before the script; the first 30 s must pay
  off exactly what they promise. High CTR with low % viewed means misleading packaging, which YouTube demotes.
- **Hook: generate, then pick.** Draft 5 openings using different mechanisms (surprising fact, stakes, specific
  number, contrarian, story moment), pulled from the strongest real fact in your research. Keep the one a
  stranger would most need to resolve and that the video fully pays off. Discard the rest.
- **Shorts are written backwards from the swipe.** Frame one must work on mute (the `thumbnail_text` banner +
  first `on_screen`), one idea only, a unique angle not a recycled list, and a last line that loops to the first.
- **No padding.** If the research doesn't fill `target_minutes`, research more or write shorter (but not under
  `min_minutes`). Padding lowers % viewed.
- **Metadata.** Title: primary search keyword in the first ~40 characters, 50-60 characters total, clear over
  clever. Description: line 1 is the value of the video, the keyword again in lines 2-3, then chapters and sources.
  First tag is the exact primary keyword, then related terms; relevant only.
- **Session.** End long videos by pointing to a related video or topic on the channel ("next, how X makes money")
  when history has one, so viewers keep watching.
- **Humanize the narration.** Before saving, reread every segment and remove AI tells: "not X, but Y" contrasts,
  one-line closers that repeat the point ("That's the real secret."), "Let's dive in"/"Here's the thing",
  forced lists of three, and the words crucial, pivotal, delve, testament, landscape, showcase, robust.
  Plain verbs (is, has). Keep contrasts only when both halves are real facts.

## Packaging and hooks (long videos; studied from the top faceless business channels)
From the most-viewed videos of How Money Works, Logically Answered, Company Man, ModernMBA and MagnatesMedia
(Oct 2026; details in `research/top-channel-playbook-2026-10-23.md`). Their top videos have 2-12M views each.

**Topic.** A brand or industry everyone already uses or has feelings about (KFC, Costco, Netflix, airlines,
cruises, Chuck E. Cheese), plus a tension: decline, a hidden money machine, a scandal, a paradox. Evergreen
beats news. Never a company most viewers haven't heard of.

**Title: write 8, keep 1 + 2 runner-ups (`alt_titles`).** Brand or subject in the first 3-4 words, one tension
word, 40-60 characters, no clickbait the video doesn't pay off. Formulas that carry these channels:
- Paradox question: "If Nobody Can Afford A Home... Who's Going To Buy Them?"
- How X really makes money: "How Boba Shops Really Make Money", "How WhatsApp Makes Money"
- The [adjective] business of X: "The Rigged Economics of Airlines", "The Secret Business of Nightclubs"
- Decline / what happened: "The Decline of Pizza Hut...What Happened?", "What Happened To GoPro?"
- Rise and fall with money: "From $10 Billion To Nothing: How Wish.com Lost Everything"
- Why X can't / won't: "Why Crumbl Cookies Can't Survive", "Why Airbnb Fails to Disrupt the Hotel Industry"
- Hidden truth: "The Disturbing History of Coca-Cola" (only when the facts really are disturbing)
Ellipses and a small hedge in brackets ("(probably)", "(sort of)") read as human and honest; use rarely.
Keep a repeatable franchise: most titles on this channel should fit "How X (Really) Makes Money" or one of
the formulas above, so viewers learn what the channel is.

**Thumbnail (`thumbnail_text` + `thumbnail_segment`).**
- 2-4 huge words that ADD to the title, never repeat it (title "How Costco Makes Money" → thumbnail
  "*$65* MEMBERSHIP" or "NOT THE HOT DOGS"). Mark the one key word or number with `*word*`: it gets a yellow box.
- A money contrast works well when true: "$0.4B VS *$2B*", "*$10B* TO $0" (the font has no arrows or emoji).
- `thumbnail_segment` = the segment whose visual is the background: one clear subject, ideally a person with a
  strong reaction (`shock`, `angry`, `smug`) or the product itself, and room on the left for the words.
  For animated channels pick a `scene` segment WITHOUT a `panel` (its numbers would clash with the words) and
  make it an obvious, uncluttered moment. Words go on the side away from the actors automatically.
  For remotion channels pick a `photo` segment with one clear subject (the product or building).
- No logos or real people's faces (we can't use them); the product, place or reaction carries it.

**Hook: the first 30-60 seconds follow this shape (every top video did some version of it).**
1. **Line 1 states the title's promise** as a question, paradox or stake: "How does WhatsApp make money?",
   "If nobody can afford a home, how do prices keep going up?", "What do you actually do for a living?"
   The viewer must hear what they clicked for within 10 seconds.
2. **Make it about the viewer**: "it affects every one of us", "you've probably paid for this without knowing".
3. **One or two hard numbers** that make the stakes real (sourced).
4. **The tease**: the answer is darker, stranger or bigger than expected ("that simple question led me down a
   rabbit hole much darker than I imagined"). Open the loop the whole video pays off.
5. **Jump into the story** with a dated scene: "To understand why, we have to go back to 1983. ..."
Put the first `chapter` on the segment where that story starts (around 30-60 s): its card works as the title drop.

**Structure.** Story arc, not a list: origin → how the money machine works (with the numbers) → the
twist or crack → where it is now → a one-line verdict. Rehook at each chapter with a question the next part
answers ("So if the food barely makes money, what does?"). Name real decisions and dates; avoid vague
"experts say".

**Pacing.** About 160-200 spoken words per minute, conversational. Top channels change the picture every
2-4 s with a chart, map, stat or reaction on every number; our renderer does this from `visual` / `on_screen`,
so give every number its own segment and visual.
