# youtube-autopilot

Makes and uploads faceless YouTube videos on a schedule. The owner only approves.

**Pipeline (per video):** Claude researches a fresh topic with web search → writes a sourced script, shot list, title, description and tags → Kokoro (free, open-source) narrates → Pexels/Pixabay stock footage is cut to the narration with FFmpeg and captions are burned in → thumbnail is generated → uploaded to YouTube as **private** → an approval issue opens here.

**Approval:** reply `/approve` or `/reject <reason>` on the issue. Approved videos get the next free publish slot. Rejection reasons are fed into future scripts.

**Cost:** GitHub Actions free tier, free voice/footage/render. Only the Claude API is paid (roughly $0.10–0.40 per video).

| Path | What |
|---|---|
| `channels/*.yaml` | One file per channel: niche, style, voice, schedule. Add a file to add a channel. |
| `autopilot/` | Pipeline code (`run.py` is the entry point). |
| `.github/workflows/produce.yml` | Daily run; each channel produces on its own days. Can also be run by hand, incl. a dry run. |
| `.github/workflows/approvals.yml` | Handles `/approve` and `/reject` comments. |
| `data/` | History and feedback, committed automatically. |
| `assets/music/` | Optional background tracks (`.mp3`, licensed for commercial use). |

Setup: see [SETUP.md](SETUP.md). Adding a channel: copy a file in `channels/`, change `id`, `secret_suffix` and the text, add its `YT_REFRESH_TOKEN_<SUFFIX>` secret, the env line in the workflows, and the id to the matrix in `produce.yml`.
