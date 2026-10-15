# Phase 2 — Selecting Scenes and Publishing

## Current state
- Modern film DISCOVERY works using YouTube Data API (video links, descriptions, published date, views and likes).
- A pure-Python dialogue-window ranker now estimates interesting 15–40-second moments **from an actual timestamped transcript**.
- The dialogue-window ranker is **heuristic**. It has no scene-level vision or audio emotion understanding and is not a trained humor model.
- FFmpeg rendering and a YouTube API upload client exist from phase 1; actual YouTube channel OAuth is not connected yet.
- No 2000+ commercial film footage is licensed or loaded. **Discovering a YouTube video gives neither media-file access nor reuse rights**.

## Planned full pipeline
1. Daily YouTube trend discovery, ideas only.
2. Identify a licensed local or provider source file of the relevant footage and associated rights metadata. Only process approved-source files (rights can be pre-cleared; no per-video review needed).
3. Transcribe Hindi/English source audio with local Whisper/faster-whisper, preserving segment timestamps; for dialogues with captions, read rights-cleared SRT/VTT.
4. Use the scene selector to generate 15–40-second windows with dialogue completeness; incorporate visual-cut timing, audio peaks, and laughter audio later.
5. Optionally score the shortlist with an LLM using timed transcript + keyframe descriptions, especially setup and punchline completeness. User must configure the relevant API key and monitor free-tier usage.
6. FFmpeg cuts the selected authorized footage, formats 9:16, adds safe-margin burned-in captions, title, original voiceover/analysis if used, and optional cleared music.
7. Automatic quality checks (duration, video dimensions, audio presence, repeated-source dedupe).
8. YouTube Data API OAuth per channel, automatically publish when explicitly enabled. Save upload IDs/history.

## OAuth for two channels (one-time setup)
The existing YouTube API discovery key is not enough for uploading.
Google Cloud → Google Auth Platform (Branding/Audience/Data Access/Clients) → configure OAuth consent.
Create an OAuth client and request scope https://www.googleapis.com/auth/youtube.upload.
For each Hindi and English channel, authorize the intended channel and securely obtain a refresh token.
Store **only** in GitHub Actions Secrets (not this public repo):
YT_HI_CLIENT_ID, YT_HI_CLIENT_SECRET, YT_HI_REFRESH_TOKEN
YT_EN_CLIENT_ID, YT_EN_CLIENT_SECRET, YT_EN_REFRESH_TOKEN

Google OAuth apps in external **Testing** status typically expire certain refresh tokens after seven days; plan audience/publishing status before unattended use. Google API documentation currently contains conflicting descriptions of unverified-project public upload availability: test an upload as PRIVATE before considering public. No user approval is required on subsequent uploads after first-time consent and stable authorization.

## Important limitations
- Modern Bollywood/Hollywood movie clips generally carry rights. Cropping/subtitles alone does not create upload permission or satisfy reused-content monetization rules.
- YouTube Data API does not return downloadable movies or transcripts of arbitrary third-party uploads. Avoid attempting to treat metadata as authorization.
- A true automated 2000s film-clip publishing pipeline cannot operate until we have properly licensed assets or choose a different original commentary/footage strategy.

## Test the current selector
python -m unittest discover -s tests -p 'test_scene_selector.py' -v
python -m shorts.scene_selector --transcript data/demo_dialogue.json --output output/scenes/scene_candidates.json
