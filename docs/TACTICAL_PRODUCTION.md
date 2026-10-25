# Approved daily tactical Pokémon Shorts

Approved in chat on 24 October 2026 for two daily releases beginning 25 October: 10:00 and 22:00 Asia/Kolkata. The existing ChatGPT production task starts at 09:30. This is the 62.75-second Gyarados/Greninja tactical sample format, replacing the earlier short fictional story format for new production. It uses illustrated scenes, natural English commentary, matchup reasoning, exact simulated HP and a decisive result.

## Sources that survive scratch cleanup

Read `data/pokemon_channel.json`, `data/pokemon_state.json`, this file and `pokemon/tactical_moves.json`. The catalogue contains 50 species with five curated legal move options each. All 250 four-of-five subsets were validated for the declared ability and baseline build with Pokémon Showdown 0.11.11, Generation 9 National Dex. It is not a popularity ranking or optimal-play recommendation. Equip four moves at a time and validate the final actual nature, EVs, ability and move combination again.

`examples/tactical_v1/` contains the tested Gyarados/Greninja simulator, renderer, pronunciation/voice setup, battle, timed script, move bank and quality report. It is a reference fixture with hardcoded names, HP, seed and dialogue. Adapt those values for every new pair; never copy its damage percentages, winner or result into another battle. Root package.json/package-lock.json pin the simulator and calculator dependencies. Use the existing hash-verified Kokoro downloader. The reference does not need hosted inference or paid API keys.

## Build the battle before the narration

1. Reconcile the ledger and Studio first. Preserve an existing accepted schedule and ID. Select two distinct unused matchups from the catalogue; reserve each slot with the pair and deterministic simulation key before any upload. Do not repeat a used matchup just to fill a slot, or upload the review batch as extra daily releases.
2. Keep the existing bounded public title/topic research requirement: at least one relevant public battle/comparison reference within four calendar months, with real title/date/link and any observed counts. Try at most two alternative eligible pairs if references are unavailable. Research informs topic/title framing, never fabricated damage or a forced winner.
3. Declare legal level-100 builds and four equipped moves per Pokémon. Keep five options in the catalogue, not five equipped moves. Explain relevant differences: current type and form, physical versus special stats, STAB, weight-dependent power, ability changes, accuracy, priority, speed order, setup moves and remaining HP needed to finish. Revalidate changed abilities because some abilities are banned by the selected format.
4. Choose a coherent teaching policy or planned sequence before resolving the battle. Every turn needs a matchup-based reason. Do not mechanically rotate moves or claim every move is optimal. Use a seed derived from the date/slot/pair and record it; keep it on retries. Resolve the sequence using the real engine, including misses, multi-hit counts, abilities, recoil, healing and residual effects if any are present. Simplify the build rather than silently omitting effects the adapted recorder cannot represent.
5. Aim for about three genuine rounds and at least two different moves per side, preferably three including a useful setup move. Do not prolong a fainted battle or invent extra rounds. If a candidate ends too quickly, choose another eligible pair within the bounded attempt limit rather than rerolling the same pair until it produces a desired winner.
6. Write the script from the resolved log and exact HP snapshots. Round percentages from actual HP lost divided by maximum HP; distinguish HP removed from uncapped potential damage. Show and explain current typing, not just the species' starting typing. Explain why a super-effective move may still do less damage than another move. Identify a setup/coverage/accuracy turning point and conclude with the actual winner and defeated opponent.

Describe the result as a scripted tactical example with engine-resolved damage for the declared builds. Do not claim a canon anime result, species-wide superiority, perfect play or a measured win probability. The old 100-trial/two-sided-win requirement belongs to the legacy analysis mode and does not gate this single-example mode. Do not attach invented simulation counts to it.

## Visual and voice standard

Use full-scene generated cinematic anime illustrations: both opponents and the move visible, consistent designs/arena, distinct action poses. Target three or four illustrations featuring each Pokémon, usually six action scenes plus a result portrait/composition. Include actual victory and defeat labels. A result composition can reuse an existing generated opponent scene if a new portrait is unavailable, as the approved sample did. Do not keep resampling a rejected depiction; use a permissible sporting portrait or existing approved art, otherwise report the missing asset.

This is image-based motion-comic animation: camera movement, cuts, readable move/accuracy/effectiveness labels, exact HP animation, modest effects and a clear final frame. Do not promise continuous character animation. Never silently substitute the old mini-icons or a six-panel grid for the approved full-scene format.

Use concise natural English Kokoro narration, the pronunciation lexicon and short captions. Spoken HP percentages are approved when useful to explain the tactics. Remove filler instead of accelerating everything to 1.5x. Target roughly 45–75 seconds, with 720×1280 or better, 24 fps or better, H.264/AAC, readable captions and normalized speech near -16 LUFS. Keep all actual move events in order. Use original or properly licensed audio.

Before upload: validate legal moves/builds, exact HP conservation and hit counts; fully decode the finished video; check audio/duration/dimensions; inspect action and result frames. The script, HUD and images must agree. No invented success after a failed check.

## Scheduling, reporting and limits

Follow `docs/CHAT_PRODUCTION.md` for the authoritative upload, reservation, channel and cancellation controls. Generate in the ChatGPT workspace and upload through the authorized Studio session. Do not use recurring GitHub-hosted video production, enable Google Cloud billing, buy anything, extract credentials or turn on the legacy `production_runner_ready` flag.

At 09:30, prioritize any missing morning video and finish its native schedule by 09:55 IST. Then prepare the 22:00 video. If the morning cutoff is missed, leave its draft private and report the blocker; do not publish it late. Generation can exceed the available window, and session/image/usage limits can interrupt work. The task must report the actual partial result here and may not call an unscheduled draft confirmed. The approved format and schedule are configured; the first unattended tactical production run remains unverified.

Limit public releases to two per IST calendar date and 62 per month. Existing approved native schedules continue independently of host readiness or app configuration. Provide both titles, owner preview links, verified dates/times and Studio edit links. Save actual IDs, seed, builds, move decisions, art provenance and verified statuses in the ledger. Report generation, processing, upload or schedule failures in this chat with the exact blocker and recovery attempted.

## Delayed prior-day release accounting — clarification on 25 October 2026

Keep editorial slot/date separate from the actual public timestamp. The user clarified that E8PsFuSoHPo is the delayed 24 October 22:00 post and does not substitute for the new 25 October evening video. Complete the 25 October 22:00 slot as this specific one-day exception to the two actual-publications cap. Preserve the real publication date and all IDs; do not rewrite history or republish the sample. The usual two-release daily and 62 monthly limits remain in force otherwise. For a future cross-date exception, flag the conflict rather than silently counting an old slot as a new scheduled slot.

## Matchup opening — approved 26 October 2026

Begin each upcoming new Short with a concise 3–5 second spoken introduction naming both Pokémon and saying they face each other, over a clear pre-battle face-off. Only then start the resolved battle. Show full starting HP and no attacks or HP loss during the introduction. Include it within the existing 45–75 second runtime; all remaining tactical requirements stay unchanged. Already accepted schedules and IDs are preserved.
