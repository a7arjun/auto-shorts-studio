# Battle Logic Lab — English Pokemon Shorts

This replaces the Bollywood automation on the existing destination channel. Its `YT_HI_*` secret names are retained as a destination identifier; videos are English. It does not create a second Google account or channel.

## Current implementation

16 legal Generation 9 National Dex base-form builds give 120 non-repeating pairs. Level 100, full IVs, legal EVs, one item/ability and four moves. The fixed builds emphasize offensive stats and coverage; they are not an exhaustive peak-build optimizer. A greedy expected-damage policy selects attacks, using priority for likely knockouts. Pokemon Showdown handles actual turns, accuracy, statuses, weather, items and damage. 100 deterministic seeded simulations produce conditional win counts. One representative trial supplies the narrated attack/HP sequence. Long battles show selected turns, explicitly labelled.

Original procedural graphics include 18 distinct move-type attack effects, health bars, captions and build cards, with mini character illustrations in the arena. **Mini/chibi character icons are fetched from PokeAPI and credited in each video description.** There are no anime clips or franchise music. Image availability does not grant underlying artwork rights. Names identify the subject of independent analysis and the channel avoids official branding.

CPU Kokoro narration (`am_michael`, English US) and FFmpeg require no hosted AI subscriptions. Pronunciation rules are editable in `pokemon/pronunciation.json`. The initial render is 720x1280, H.264/AAC, 24 fps; audio is normalized to -16 LUFS. No paid API or billing-enabled speech project is required. Dependencies and voice/model downloads consume free runner time and storage.

## Commands

```
npm ci --omit=optional
python -m pip install -r requirements-pokemon.txt
npm test
python -m unittest discover -s tests -p 'test_*.py'
python -m shorts.pokemon_main --mode preview
python -m shorts.pokemon_main --mode probe
python -m shorts.pokemon_main --mode pilot
python -m shorts.pokemon_main --mode daily
```

Linux packages: ffmpeg, fonts-dejavu-core, libsndfile1. Model files download once to `.cache/kokoro`, cached by Actions; never committed. The code is public; OAuth values remain in repository secrets and never enter the ledger or artifacts.

## Launch and ongoing operation

`pokemon-shorts.yml` renders a software integration preview when implementation files change on main; the private YouTube pilot is a separate one-time operation. It prepares both daily videos at 03:00 UTC (08:30 IST), ahead of the 09:30 IST review, with production dispatched only to a separately configured Linux runner labelled `pokemon-renderer`. Each processed private upload is scheduled through YouTube's `publishAt` for **10:00 AM and 10:00 PM IST** (04:30 and 16:30 UTC). GitHub-hosted runners are used only for software tests and the one-time private integration pilot. They are not offered as indefinite free production media hosting. The operator has requested scheduled publication (`publication_enabled: true`). The private pilot and renewed authorization have passed; production remains blocked by `production_runner_ready: false` until an actual runner is connected. The limits are two per IST calendar day and 62 per calendar month, allowing 56/60/62 in 28/30/31-day months. Scheduled and published videos both count; each time slot can reserve only one upload. Runs outside the morning batch window skip preparation; an unfinished video is left private after the 09:30 IST review deadline. A five-minute publication lead prevents immediate catch-up release. A delayed runner can miss a slot. A late upload that has not been scheduled stays private and is marked `missed_slot`; the next slot can proceed. Existing video IDs are reconciled without reuploading, and public visibility is checked on the next run after release. A suitable production runner has not yet been connected. An existing personal always-on computer can run it without a hosting subscription, but consumes electricity and internet. A cloud runner needs a separate account and its own free-tier/billing verification; no paid host has been enabled. Public repository scheduled workflows can be disabled after 60 days of repository inactivity; successful publishing ledger commits normally provide activity, but provider/auth/account failures can still need maintenance.

Existing secret names: `YT_HI_CLIENT_ID`, `YT_HI_CLIENT_SECRET`, `YT_HI_REFRESH_TOKEN`, `YOUTUBE_DATA_API_KEY`. `GITHUB_TOKEN` is the workflow's automatic repository token, used to persist the upload ledger with compare-and-swap. No new paid account is required.

The token must belong to the same channel as reference video `1uvpsNPF63A`. `probe` checks that binding and records granted scope names only. For a complete private-check-then-public lifecycle, `youtube.force-ssl` (or `youtube`) authorization is required; the legacy `youtube.upload` scope alone does not grant video updates or channel rebranding. Changing the requested scope string in code cannot grant access. If renewal is needed, the owner must complete Google's consent screen once and replace only this channel's refresh-token secret through GitHub settings. OAuth Testing grants may expire after seven days; use the appropriate durable OAuth configuration for unattended operation.

Every upload starts private. Before public release the worker checks owner processing status and public API visibility, including reported regional restrictions. These API checks **do not certify Content ID clearance or future monetization**. The ledger reserves the job before upload and stores the video ID immediately afterward. A crash with an ambiguous upload outcome stops new inserts rather than creating duplicates; known video IDs are automatically reconciled on the next run. Auth failures are surfaced as failed Actions jobs. There is no automatic dispute, deletion, or spend fallback.

General audience classification is explicitly configured with a rationale for competitive teen/adult game analysis. Reassess it if the content style or intended audience changes; a franchise name alone does not determine the classification. Originality, entertainment value and copyright remain separate from whether the pipeline can run.

Channel branding draft: **Battle Logic Lab**. Description is in `data/pokemon_channel.json`. Renaming the actual channel or changing its handle requires YouTube Studio or suitable broader API authorization. Existing movie uploads and all history are preserved. Old scheduled movie/discovery workflows are retired from the active workflow directory, so they cannot race this publisher.

## Sources and licences

- Pokemon Showdown simulator: https://github.com/smogon/pokemon-showdown (MIT).
- Damage calculator: https://github.com/smogon/damage-calc (MIT).
- Kokoro model: https://huggingface.co/hexgrad/Kokoro-82M (Apache-2.0 weights).
- Kokoro ONNX wrapper: https://github.com/thewh1teagle/kokoro-onnx (MIT; retain dependency licences).
- Model exports: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1.
- FFmpeg licence depends on build: https://ffmpeg.org/legal.html. Running the tool is distinct from redistributing its binaries.
- YouTube authenticity policy: https://support.google.com/youtube/answer/1311392.
- Audience guidance: https://support.google.com/youtube/answer/9528076.

No claim is made that the simulator's software licence licenses Pokemon artwork or anime. No external footage permission is assumed by this implementation.

ONNX telemetry is disabled before initialization with `ORT_DISABLE_TELEMETRY=1` and the runtime API. Voice-model files are SHA-256 pinned.

## Initial setup history — 22 October 2026

- Local complete pilot rendered successfully: 51.875 seconds, 720x1280, H.264/AAC.
- 4 Node tests and 45 Python tests passed locally and on GitHub. All 120 starting pairs resolved in a one-trial mechanics smoke test.
- GitHub integration run 39802221855 reached Google OAuth refresh and stopped with `invalid_grant: Token has been expired or revoked`. No new upload was created; no publishing reservation was written.
- YouTube Studio requires Google sign-in in the available browser. Visible channel branding has not been changed. `Battle Logic Lab` is a prepared brand, not a claimed new channel.
- Reauthorize the existing channel once with `youtube.force-ssl` (or `youtube`), using an appropriate durable OAuth configuration. Store the new refresh token securely in `YT_HI_REFRESH_TOKEN`; never send it in chat. Client ID/secret need replacing only if the OAuth client changes.
- Production hosting is not connected. The software is free; zero-cost hosted production has not been established. See GitHub Actions terms: https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features.
- This initial authorization failure was resolved later the same day; see the verified rollout below. The production host gate remains disabled.

## Standalone worker

`Dockerfile.pokemon` (not yet built/tested as a container) packages the daily worker independently of GitHub-hosted compute. Build it with `docker build -f Dockerfile.pokemon -t pokemon-shorts .`. Supply the existing YouTube OAuth values, metadata API key and a narrowly scoped token for this repository's publishing ledger through the host's secret store/environment. The container runs `python -m shorts.pokemon_main --mode daily`. Run it once daily at 03:00 UTC (08:30 IST) through the host's scheduler to prepare both slots; persisted slot records prevent repeated publication. Use `POKEMON_REMOTE_STATE=true` and the repository-scoped `GITHUB_TOKEN` for a durable shared ledger, and prevent concurrent workers (the GitHub workflow already uses concurrency). Keep the clock synchronized. Keep a cache volume at `/app/.cache/kokoro` to avoid repeated model downloads. No credentials are built into the image. A real host and runtime credentials are still required.

## Narration and chibi refinement

The updated sample uses `pokemon/pronunciation.json` for explicit IPA, including Charizard/Blastoise and possessive forms. It no longer feeds artificial spaced spellings such as `Char iz ard` into TTS. `shorts/pokemon_speech.py` gives every catalogue attack and item a 350 ms post-name pause; segment endings have a 280 ms pause. Spoken phrase timing keeps captions from advancing through an inserted pause. Display names retain their correct spellings. The selected voice remains `am_michael`, slowed to speed 1.0. These are pronunciation targets for listening review, not a claim that every voice rendering is perfect.

The renderer automatically retrieves transparent PNG/WebP mini/chibi icons through **PokeAPI**, using `GET https://pokeapi.co/api/v2/pokemon/{name}/`. It first selects BDSP mini-icons, then Scarlet/Violet mini-icons, then pixel icon fallbacks. All 16 starting Pokemon were resolved and visually checked; 14 use BDSP mini-icons, Greninja and Sylveon use Scarlet/Violet mini-icons. These are game mini-icons, not newly commissioned chibi drawings. Images replace the elemental markers, face the opposing side and retain gentle motion.

## Permanent image retrieval

- No API key, login, paid image generation or manual image search is required.
- Cache requested API data locally, following PokeAPI's fair-use policy. Store images with Pokemon name/ID, exact source URL, hash, retrieval time and copyright status.
- Reuse verified image files without network requests. A valid cached image still works when the API or image host is unavailable.
- On a cold run with the API unavailable, use the bundled API-discovered URL snapshot in `pokemon/image_catalogue.json` for the 16 starting species. This helps if the metadata API is down; it cannot guarantee the image host will always be available.
- Try another supported icon set when the preferred image is missing. Never silently use another Pokemon or unrelated artwork.
- Reject wrong identities, unexpected hosts/redirects, invalid images and corrupted cache files. Retry transient network failures within a bounded limit.
- `assets/pokemon/manifest.json` selects the provider and still supports local sourced overrides. The default has no manual per-Pokemon entries.
- `python -m shorts.pokemon_assets --warm-roster` downloads/verifies the starting roster. Persistent cache path is `.cache/pokemon-images`; Actions restores/saves it, and a standalone worker should mount a persistent volume there.
- The completed job writes `output/pokemon/assets.json`, and its description includes the actual image URLs. Image caches and image binaries are not committed to the repository.

PokeAPI is free and requires no authentication: https://pokeapi.co/docs/v2. The repository licence explicitly says image copyright belongs to The Pokemon Company: https://raw.githubusercontent.com/PokeAPI/sprites/master/LICENCE.txt. This implementation records underlying rights as reserved. API access is **not** represented as a commercial artwork licence, a copyright exemption or a monetization guarantee. See the rollout below for current authorization, publication and hosting status.

## Fresh research before each upload

`shorts/pokemon_research.py` researches public YouTube metadata before every pilot/daily upload, using the existing metadata API key and no paid model or scraping service. Two broad queries, each ordered by relevance, views and date, sample up to 300 search results. They rank unused validated roster matchups. Mechanically eligible candidates are checked with up to three exact matchup queries in the same three orders: at most fifteen bounded search calls per video, thirty for two daily videos. Results are deduplicated and fetched in batches for current visible views/likes/comments. This is a sample, not every matching YouTube video and not YouTube's Trending chart. No video/transcript download is performed, and `videoDuration=short` is not used to mislabel everything under four minutes as a Short.

The cutoff is **four calendar months**, recalculated per run. Publication dates are rechecked after retrieval. References within 90 days receive preference, with older references allowed only inside the four-month window. Queries prefer English; explicitly non-English metadata is excluded, but missing language metadata cannot verify English audio. Exclude the destination channel, zero-view/deleted results, irrelevant formats such as cards/GO and transformations incompatible with our base-form videos. Exact matchup references must mention both Pokemon in a battle/comparison context. Search ranking uses lifetime average views per day, capped visible engagement and recency; this is a popularity proxy, not measured recent growth or proof of an emerging trend. The strongest result per channel contributes to broad topic selection.

Create an original, grounded title from observed relevant phrase patterns, align the spoken opening, and retain the simulated builds/results unchanged. Relevant species/battle hashtags are ordered using observed use within the reference sample; unrelated viral/anime/other-game hashtags are excluded. Keep five hashtags and a short backend tag list. Research does not guarantee reach or monetization. No suitable recent references or an API failure stops the upload before rendering instead of claiming the content is trend-backed. Offline previews deliberately retain the baseline title and are not labelled researched.

Each run saves `output/pokemon/research.json` with the cutoff, reference URLs/dates, visible statistics, scoring method and selected metadata. The durable publishing ledger stores selected reference IDs, title and hashtags. The workflow's existing two-day output artifact includes the research evidence; the ledger keeps a compact decision record.

For renewed authorization follow [the current connection guide](RENEW_YOUTUBE_AUTH.md). Legacy Bollywood connection instructions describe a retired upload-only test and are not the current authorization procedure.


## Review-first publication and cancellation

Both 10:00 AM and 10:00 PM IST videos are prepared in the morning. The daily review reminder reads the ledger at 09:30 AM IST, displays private preview links and the verified YouTube publication times, or reports an actual readiness blocker. A verified native YouTube schedule releases without a later approval. A reminder is not a live cancellation listener and does not guarantee delivery before release.

To stop an already scheduled video directly, open its YouTube Studio edit page and change Visibility to Private with the schedule removed. Disabling `publication_enabled` alone does not revoke schedules already accepted by YouTube. Chat cancellation is only complete after an explicit API or Studio cancellation has been verified.

`data/pokemon_control.json` supports an explicit `publish` of the existing verified first pilot or `cancel` of a recorded video. Change `request_id`, `action` and `video_id` for the operator's current request; the publication-control workflow updates that existing video ID, checks ownership and verifies the result. It never calls videos.insert. To stop all queued releases, cancel every scheduled video and disable new publication. Cancelled videos retain their records; a replacement may occupy the vacated slot under a new revision key. Occupied active slots still block duplicates.

Shorts eligibility is determined by the uploaded media and YouTube's classification, not a separate upload endpoint or a title hashtag. The publication integration check reads owner file details and requires a square/vertical file no longer than three minutes. This is media eligibility evidence, not an API Shorts classification flag. The current pilot is approximately 55 seconds at 720×1280.


## Verified rollout on 22 October 2026

- Renewed OAuth refresh, exact destination channel ownership and `youtube.force-ssl` scope passed.
- First pilot `p54dCIM9LOY` was processed privately, then made public at the operator's request. Owner media details confirmed 720×1280 and approximately 54.6 seconds; public API visibility was verified.
- One-time review integration staged two private videos for 23 October: `_kepcZR8V6g` (Lucario vs Greninja) at 10:00 IST and `_-EW1-ZZuAc` (Charizard vs Pikachu) at 22:00 IST. Each native `publishAt` was verified before marking its ledger row scheduled. The initial status read lag was recovered without duplicate uploads; verification now uses bounded retries.
- A daily 09:30 AM IST reminder was created to display recorded previews, publication times and direct Studio cancellation links, starting 23 October.
- The date-fixed review integration workflow is now manual-only with non-interrupting concurrency. It is not an ongoing production host.
- **Still required for generation after the staged day:** a connected production host. `publication_enabled` expresses the operator's authorization; `production_runner_ready` remains false. GitHub scheduled production is skipped before queuing until that actual resource is ready. Already accepted native YouTube schedules are independent of this gate.


## Elemental effects and presentation rules — v2

The renderer uses each move’s resolved simulator type, after abilities such as Pixilate. All 18 types have distinct original procedural effects: flame jets, water streams, lightning, leaves, shards, rocks, wind, rings, blades and other elemental motifs. HP loss follows the impact cue. Misses pass above the target; immunity dissipates the effect without impact. No footage or paid effects API is needed.

Before downloading images, synthesizing speech or uploading, reject matchups with a unanimous 100/100 result. Both Pokemon must have won at least one of the same 100 deterministic trials. Select a trial where the eventual winner lands at least two damaging move uses and the opponent attempts an attack. The finished story must show at least two distinct successful attacks by that winner. Multi-hit moves count as one move use. Damage, HP and aggregate outcomes are never changed; unsuitable matchups are skipped rather than rerolled. Narration distinguishes the selected example’s winner from the aggregate favorite and explains a final recoil knockout.

An initial 120-pair screen with key `quality-v2-screen` found 32 eligible matchups. This is seed-specific screening evidence, not a promise that every daily selection or all 120 pairs can produce a compliant video. Fresh research and the daily key still have to pass.

The two previously staged videos (`_kepcZR8V6g`, `_-EW1-ZZuAc`) were held private and their native release schedules cancelled after failing the new rules. The already-public pilot remains public. Cancellation now waits for bounded owner-status consistency before recording success.

Keep the requested two releases per day. YouTube’s 24-hour channel upload cap varies by channel history and region and also applies to API uploads; there is no documented universal allowance of 50. Bulk publication can suppress notifications, and subscribers receive at most three new-video notifications per channel per 24 hours. There is no supported fixed SEO penalty for exactly 50 uploads; assess audience response and avoid generic repetitive content. YouTube’s monetization rules exclude mass-produced/inauthentic content, so varied substantive analysis matters beyond different names in a template. A 50-video buffer would cover 25 days at two per day, but the current screened pool is smaller and has not been rendered as a batch.

Official references: https://support.google.com/youtube/answer/10383400 ; https://support.google.com/youtube/answer/7389684 ; https://support.google.com/youtube/answer/1311392 .

Validation for v2: 81 Python tests plus 5 Node tests passed; GitHub integration rendered the updated software preview successfully. The local Charizard–Sylveon preview is approximately 70.8 seconds at 720×1280 with AAC audio.

The v2 replacement integration completed successfully (run 39832097273): `a5PWKN9vZXg` (Charizard–Tyranitar) is verified scheduled for 23 October 2026 at 10:00 IST, and `KfRaJ0nQWMM` (Charizard–Garchomp) at 22:00 IST. Both passed recent public-metadata research and the new presentation checks before rendering and upload. The production host gate remains false for subsequent daily generation.


## Full-turn, faster dual-verdict presentation — v3 (23 October 2026)

Every move from the selected example appears exactly once in simulator order, including misses and the opponent’s intervening attacks. The publication check compares the complete move sequence with the simulator log and rejects omissions. Narration no longer reads HP damage percentages; visible HP still comes from exact game health. Rules and build items remain on screen/in the description instead of delaying the first attack with spoken setup.

Output playback is 1.5×: visual timestamps advance at 1.5× and FFmpeg uses `atempo=1.5` for audio without raising pitch. The voice synthesizer stays at its original rate; acceleration is applied once. Final duration, captions, impact effects and both media streams are checked after retiming.

The game experiment now uses a declared build catalogue. Charizard, Garchomp and Tyranitar each have three legal builds, giving nine equally allocated build combinations per matchup; 100 trials allocate 11 or 12 runs to each combination. The displayed example uses its actual sampled items/natures/EVs. Other catalogue species still have their original one build and are identified by their actual coverage. All variants are legal offensive/bulky examples, not an exhaustive peak optimizer or measured ladder-usage distribution. The existing greedy policy, no-switching and no-transformations restrictions remain. Nothing is weighted by popularity or adjusted to get appealing counts. Source data, per-combination counts and wins are in `battle.json`.

For keys `2026-10-23T10:00+05:30-r3` and `2026-10-23T22:00+05:30-r3`, the preflight measured Tyranitar 64–36 Charizard and Garchomp 80–20 Charizard. The previous 85/100 results were genuine single-build samples, not overall strength estimates.

A separate anime section names trainer individuals. The current sourced comparisons are Ash’s Charizard vs Cynthia’s Garchomp, and Ash’s Charizard vs Alain’s Tyranitar. Their feat summaries cite official episode synopses and an episode-outcome cross-check. Anime leans are explicitly editorial, low confidence, and never expressed as simulated wins or exact odds. No transformations or another trainer’s feats are silently combined. The game build is not claimed to reproduce the named anime Pokemon. During the anime section, trainer names replace the game HP/item cards.

The initial anime evidence catalogue covers these two comparisons. For an uncovered pairing the automatic fallback says the named anime verdict is unresolved; it never invents a feat or a probability. This avoids a human approval dependency but is a real coverage limit, not completed universal anime research. Evidence snapshot: 23 October 2026. `pokemon/anime_assessments.json` stores source URLs, scope, named versions and the reasoning behind each inference.

Research recommendation: use a short immediate question, show the complete exchange, then resolve the game and anime questions separately. YouTube’s creator/product discussion recommends immediate hooks and concise mini-stories: https://blog.youtube/creator-and-artist-stories/youtube-shorts-deep-dive/ . At 1.5×, measure actual viewer retention/readability before raising speed further; no fixed viral performance is promised.

Both v2 schedules were cancelled and verified private before revision. The first public pilot remains public. Production hosting is still not connected; a one-time date-fixed integration handles only the authorized replacements.
