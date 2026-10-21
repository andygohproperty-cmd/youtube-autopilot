# One-time setup (about 1 hour)

These steps need your own accounts, so only you can do them. After this, everything runs by itself and your only job is approving videos.

## 1. Accounts and keys (15 min)

| What | Where | Cost |
|---|---|---|
| Claude API key | console.anthropic.com → Settings → API keys → Create key. Add $10 credit under Billing. | ~$0.10–0.40 per video |
| Pexels key (stock video) | pexels.com/api → "Get started" | Free |
| Pixabay key (backup stock, optional) | pixabay.com/api/docs (shown when logged in) | Free |

## 2. YouTube channels (10 min)

1. On YouTube, profile picture → Settings → **Add or manage your channels** → **Create a channel**. Do this twice (one per channel in `channels/`). Names are in each file; change them if you like.
2. Verify your phone at youtube.com/verify (unlocks custom thumbnails and videos over 15 min).

## 3. Google Cloud project (20 min)

1. console.cloud.google.com → create project **youtube-autopilot**.
2. APIs & Services → Library → **YouTube Data API v3** → Enable.
3. APIs & Services → OAuth consent screen → External. App name "youtube-autopilot", your email. Add yourself as a test user. Then click **Publish app** so it shows "In production" (otherwise access expires every 7 days).
4. Credentials → Create credentials → **OAuth client ID** → type **Web application**.
   Under "Authorized redirect URIs" add: `https://developers.google.com/oauthplayground`
   Copy the **Client ID** and **Client secret**.

## 4. Connect each channel (5 min per channel)

1. Open developers.google.com/oauthplayground → gear icon (top right) → tick **Use your own OAuth credentials** → paste Client ID and secret.
2. Left box "Input your own scopes", paste:
   `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube`
3. **Authorize APIs** → sign in → **pick the channel** → Allow (click "Advanced → continue" on the unverified warning; it's your own app).
4. **Exchange authorization code for tokens** → copy the **Refresh token**.
5. Repeat for the second channel.

## 5. Put the keys in GitHub (5 min)

Repo → Settings → Secrets and variables → Actions:

**Secrets** (New repository secret):

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `PEXELS_API_KEY` | Pexels key |
| `PIXABAY_API_KEY` | Pixabay key (optional) |
| `YT_CLIENT_ID` | Google client ID |
| `YT_CLIENT_SECRET` | Google client secret |
| `YT_REFRESH_TOKEN_BIZ` | refresh token for the business explainer channel |
| `YT_REFRESH_TOKEN_FACTS` | refresh token for the facts Shorts channel |

**Variables** tab: `AUDIT_PASSED` = `false`

## 6. Apply for the YouTube API audit (10 min)

Until Google audits the app, anything it uploads is locked private. Apply at support.google.com/youtube/contact/yt_api_form using the answers in [AUDIT.md](AUDIT.md). Approval usually takes a few weeks; use that time to tune quality. When it passes: set `AUDIT_PASSED` to `true` and run the **Release approved videos** workflow once.

## 7. Approvals on your phone

Install the GitHub mobile app and turn on notifications for this repo. Each new video opens an issue with a private watch link. Reply `/approve` or `/reject <reason>`.
