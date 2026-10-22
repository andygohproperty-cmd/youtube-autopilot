# Animated visuals (channels with `visual_style: animated`)

Every segment of an animated channel needs a `visual`: one scene shown while that segment is narrated.
`broll_query` is still required by the schema but unused (write 2-3 words). `python -m autopilot.run check-plan`
rejects missing visuals, unknown types and icon names that are not in `assets/anim/icons/` (Lucide names, e.g.
`shopping-cart`, `piggy-bank`, `trending-up`; check with `ls assets/anim/icons | grep <word>`).

Chapter cards are added automatically from `chapter`; don't write a `chapter` visual.

## Rules that keep it watchable
- Never the same type twice in a row. Roughly half the segments should be `scene` (cartoon people), the rest
  a mix of the motion-graphic types. Put each big number in `stat`, `bars` or `pie` on the segment that says it.
- Every text label is 1-4 words; the captions already show the narration.
- The visual must match the line: people react to what is being said (shock at a big number, happy at a deal).
- Never draw a real person's likeness or a company logo. The cast are generic characters; a "founder" or "CEO"
  is just `exec`.

## Scene: cartoon people
```json
{"type": "scene", "bg": "store", "camera": "in",
 "actors": [{"cast": "you", "x": 0.1, "to": 0.45, "cart": true, "expr": "happy",
             "then": "point", "then_expr": "shock", "switch": 0.6, "react": "jump",
             "bubble": {"text": "Wait, what?", "at": 0.3}}],
 "items": [{"icon": "gem", "x": 0.75, "y": 0.35, "label": "Diamonds", "color": "blue", "fall": true, "at": 0.4}],
 "panel": {"type": "stat", "value": 5.3, "prefix": "$", "suffix": "B", "decimals": 1, "label": "in fees"},
 "panel_side": "right", "panel_at": 0.3, "punch": 0.8}
```
- `bg`: `store`, `city`, `office`, `plain`. `camera`: `in` / `out` (slow zoom). `pan`: `right`. `punch`: time (0-1) of a quick zoom hit.
- `cast`: `you` (yellow, the viewer), `friend` (teal), `exec` (blazer: bosses, founders, executives), `expert` (red: analysts).
  Use 1 actor, at most 3. Keep the same cast for the same role through the video.
- Position: `x` 0-1 across the frame; `to` makes them walk there (`cart: true` pushes a trolley).
- `pose`: standing `stand`, `walk`, `point`, `cross`, `easy`, `shrug`, `shirt`; close-up busts `explain`, `coffee`,
  `laptop`, `paper`, `idea`, `arms`, `whatever`. Busts suit someone talking or thinking; standing poses suit action.
- `expr`: `happy`, `grin`, `laugh`, `shock`, `fear`, `worried`, `sad`, `tired`, `smug`, `angry`, `rage`, `think`,
  `neutral`, `love`, `serious`, `driven`, `cute`. `talk: true` animates the mouth.
- `then` / `then_expr` switch pose / face at `switch` (0-1 through the segment); `react`: `jump` or `shake` at that moment.
- `bubble`: speech (`think: true` for a thought bubble), 2-6 words, `at` = when it appears (0-1).
- `items`: up to 4 icons that drop in (`fall`) at `x`,`y` (0-1) with a short `label`; colors `yellow`, `teal`, `red`, `blue`.
- `panel`: any motion-graphic visual below shown on a card beside the actor (actor on the left, so keep `x` ≤ 0.3).

## Motion graphics
- `stat`: `{"type": "stat", "value": 92, "suffix": "%", "label": "renew every year"}` (number counts up; `prefix`, `decimals`).
- `bars`: `{"type": "bars", "items": [{"label": "Fees", "value": 5.3, "display": "$5.3B"}, {"label": "Profit", "value": 8.1, "display": "$8.1B", "color": "teal"}]}` (2-4 bars).
- `pie`: `{"type": "pie", "fraction": 0.66, "display": "2/3", "label": "of the profit", "color": "yellow"}`.
- `versus`: `{"type": "versus", "left": {"icon": "piggy-bank", "label": "You save"}, "right": {"icon": "shopping-cart", "label": "You splurge"}}`.
- `icons`: `{"type": "icons", "icons": ["ban", "truck"], "labels": ["No shelves", "No trucks"], "caption": "optional line"}` (2-4).
- `list`: `{"type": "list", "items": ["Bring a list", "Go straight to the back"], "icon": "check"}` (2-4 rows).
- `receipt`: `{"type": "receipt", "title": "COSTCO", "items": [["Milk", "$3.99"], ["Kayak", "$229.99"]], "total": "$233.98"}`.
- `quote`: `{"type": "quote", "text": "exact sourced quote", "who": "role, year"}` (only real, sourced quotes).
- `text`: `{"type": "text", "lines": ["Not an", "accident"], "highlight": 1}` (big words, 1-3 short lines).
- `floorplan`: `{"type": "floorplan", "corners": ["milk", "toilet", "drumstick", "shopping-cart"], "center": ["tv", "gem"]}` (a store map: path past the middle).
