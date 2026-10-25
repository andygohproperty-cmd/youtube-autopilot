# Music

Licensed tracks only: the **YouTube Audio Library** (Studio > Audio Library, Content-ID safe).
Without tracks here, videos get original generated music (`autopilot/musicgen.py`), which is also safe.

- Put MP3s in a mood folder that matches the channel's `music_mood`, e.g. `documentary/`.
- Prefer tracks marked "No attribution required". If a track needs attribution, add its credit line
  to `credits.json` keyed by file name without `.mp3`; it is added to the description:
  `{"Hidden Agenda": "Hidden Agenda by Kevin MacLeod (YouTube Audio Library)"}`
- The mix ducks the music under the voice and keeps it low; sound effects are generated in `autopilot/sound.py`.
