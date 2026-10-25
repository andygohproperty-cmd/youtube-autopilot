# Remotion visuals (`visual_style: remotion`)

Long videos in the dark documentary look ("Dossier": MagnatesMedia / How Money Works style), rendered
with [Remotion](https://www.remotion.dev) from `remotion/`. Remotion is free for individuals and
companies of up to 3 people. Agent skills: https://www.remotion.dev/docs/ai/skills

Each segment's `visual` is one scene, or `{"shots": [...]}` where every shot after the first has a
`cue`: the word (or start of a phrase) in the narration that starts it. Inside a scene, `at` fields
are also words ("Ray-Ban") or seconds from the scene start (0.4). `*word*` marks the accent colour.

Assets are fetched for you: `image` / `bgImage` (Wikimedia Commons "File:..." title or search, credited
in the description) and `broll` / `bgBroll` (stock footage search). Cards take `bgImage`/`bgBroll` as a
blurred background.

| type | fields |
| --- | --- |
| photo | image, tag, move (in/out/left/right/up), frame (true: framed on blur; default when not wide) |
| clip | broll, tag, bw |
| collage | items [{image or label, label, at, pos [x,y], h}], stamp {text, at} |
| text | lines [{text, at, size, color: "red", mark: "red", serif}] |
| stat | value ("€26.5 BILLION", counts up), label, sub, at, color, size |
| quote | text (with *highlight*), kicker, who, hlAt, size |
| versus | left/right {name, sub, color, at}, vs, vsAt |
| brands | items [name or {name, at}], cols, tag, converge {at, text} |
| empire | center, nodes [{label, sub, at}], radius, rx, cy |
| chain | steps [{label, owned: true or word, stamp}], ownedText, tag |
| ledger | rows [{year, name, price, at}], title |
| bars | items [{label, value, at, prefix, color}], unit, max, title, note |
| waffle | from, to (percent), at, label, fromLabel, toLabel |
| donut | value, approx, title, sub, at |
| line | direction (up/down) or points, at, label, tag |
| timeline | from, to (years), at, label |
| map | view, from (camera start), highlight [ISO numeric ids], points [{name, sub, lon, lat, at, side}], route, tag |

Map views: world, europe, italy, north_italy, usa, atlantic, australia, france_italy (or {center, scale}).
Title and chapter cards are added automatically. Captions are timed per word from the narration
(faster-whisper) and run all the way; big kinetic captions in the hook.

Preview locally: `cd remotion && npm ci && npx remotion studio`.
