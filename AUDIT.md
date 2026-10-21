# YouTube API audit: draft answers

Use these at support.google.com/youtube/contact/yt_api_form (API Services audit and quota extension). Edit anything that isn't accurate.

- **Who uses the app:** Only me, the owner of the channels it uploads to. It is not offered to other users.
- **What it does:** Uploads videos I produce to my own YouTube channels and schedules them. Each video is uploaded as private, I review it, and only after my explicit approval is it scheduled to publish.
- **API methods used:** `videos.insert`, `videos.update` (status: privacy and publishAt), `thumbnails.set`.
- **Data stored:** Video IDs, titles and publish times for my own videos, stored in a private repository. No data about other users is collected or stored.
- **Human review:** Every upload is reviewed and approved by me before it can become public.
- **Expected volume:** About 2 long videos and 7 Shorts per week across 2 channels (well under default quota).
- **Content:** Original educational videos (scripts researched and written for each video, licensed stock footage from Pexels/Pixabay, AI narration disclosed in each description).
