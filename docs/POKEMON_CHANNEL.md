# Battle Logic Lab — English Pokemon Shorts

This replaces the Bollywood automation on the existing destination channel. Its `YT_HI_*` secret names are retained as a destination identifier; videos are English. It does not create a second Google account or channel.

## Current implementation

16 legal Generation 9 National Dex base-form builds give 120 non-repeating pairs. Level 100, full IVs, legal EVs, one item/ability and four moves. The fixed builds emphasize offensive stats and coverage; they are not an exhaustive peak-build optimizer. A greedy expected-damage policy selects attacks, using priority for likely knockouts. Pokemon Showdown handles actual turns, accuracy, statuses, weather, items and damage. 100 deterministic seeded simulations produce conditional win counts. One representative trial supplies the narrated attack/HP sequence. Long battles show selected turns, explicitly labelled.

Original procedural graphics include travelling attack pulses, health bars, captions and build cards, with mini character illustrations in the arena. **Mini/chibi character icons are fetched from PokeAPI and credited in each video description.** There are no anime clips or franchise music. Image availability does not grant underlying artwork rights. Names identify the subject of independent analysis and the channel avoids official branding.

CPU Kokoro narration (`am_michael`, English US) and FFmpeg require no hosted AI subscriptions. Pronunciation rules are editable in `shorts/pokemon_story.py`. The initial render is 720x1280, H.264/AAC, 24 fps; audio is normalized to -16 LUFS. No paid API or billing-enabled speech project is required. Dependencies and voice/model downloads consume free runner time and storage.

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

`pokemon-shorts.yml` renders a software integration preview when implementation files change on main; the private YouTube pilot is a separate one-time operation. It also has a daily 12:47 UTC / 18:17 IST trigger, with production dispatched only to a separately configured Linux runner labelled `pokemon-renderer`. GitHub-hosted runners are used only for software tests and the one-time private integration pilot. They are not offered as indefinite free production media hosting. Scheduled publication is initially disabled by `publication_enabled: false`, until a successful rendered pilot and YouTube connection are checked. One daily public upload, maximum 30 per calendar month (IST), is enforced in code. The exact schedule may be delayed by GitHub. A suitable production runner has not yet been connected. An existing personal always-on computer can run it without a hosting subscription, but consumes electricity and internet. A cloud runner needs a separate account and its own free-tier/billing verification; no paid host has been enabled. Public repository scheduled workflows can be disabled after 60 days of repository inactivity; successful publishing ledger commits normally provide activity, but provider/auth/account failures can still need maintenance.

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

## Verified setup status — 22 October 2026

- Local complete pilot rendered successfully: 51.875 seconds, 720x1280, H.264/AAC.
- 4 Node tests and 45 Python tests passed locally and on GitHub. All 120 starting pairs resolved in a one-trial mechanics smoke test.
- GitHub integration run 39802221855 reached Google OAuth refresh and stopped with `invalid_grant: Token has been expired or revoked`. No new upload was created; no publishing reservation was written.
- YouTube Studio requires Google sign-in in the available browser. Visible channel branding has not been changed. `Battle Logic Lab` is a prepared brand, not a claimed new channel.
- Reauthorize the existing channel once with `youtube.force-ssl` (or `youtube`), using an appropriate durable OAuth configuration. Store the new refresh token securely in `YT_HI_REFRESH_TOKEN`; never send it in chat. Client ID/secret need replacing only if the OAuth client changes.
- Production hosting is not connected. The software is free; zero-cost hosted production has not been established. See GitHub Actions terms: https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features.
- Automatic public publishing remains disabled until authentication, a private processing check and production hosting are verified.

## Standalone worker

`Dockerfile.pokemon` (not yet built/tested as a container) packages the daily worker independently of GitHub-hosted compute. Build it with `docker build -f Dockerfile.pokemon -t pokemon-shorts .`. Supply the existing YouTube OAuth values, metadata API key and a narrowly scoped token for this repository's publishing ledger through the host's secret store/environment. The container runs `python -m shorts.pokemon_main --mode daily`. Run it once daily through the host's scheduler; persisted ledger limits prevent repeated publication. Keep a cache volume at `/app/.cache/kokoro` to avoid repeated model downloads. No credentials are built into the image. A real host and runtime credentials are still required.

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

PokeAPI is free and requires no authentication: https://pokeapi.co/docs/v2. The repository licence explicitly says image copyright belongs to The Pokemon Company: https://raw.githubusercontent.com/PokeAPI/sprites/master/LICENCE.txt. This implementation records underlying rights as reserved. API access is **not** represented as a commercial artwork licence, a copyright exemption or a monetization guarantee. Public publishing remains disabled for the previously documented authorization/hosting setup.
