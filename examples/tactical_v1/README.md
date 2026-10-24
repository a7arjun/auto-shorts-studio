# Gyarados vs Greninja — tactical video sample

One illustrated three-round battle with six different moves and a decisive winner/loser shot. A planned teaching sequence is resolved by Pokémon Showdown 0.11.11 using Generation 9 National Dex mechanics, fixed seed `[2026,10,24,1]`, level 100, 31 IVs, no held items, no switching and no transformations. Full builds, EVs, legal sets and the engine log are in battle.json. This is not a competitive optimal-play claim, universal species ranking, canon anime outcome or aggregate win probability.

## The six actions

1. Greninja uses **Grass Knot**. Gyarados weighs 235 kg, so Grass Knot has 120 base power. Protean turns Greninja into Grass type, providing a same-type attack bonus. Grass damage against Water/Flying is neutral: 2× against Water and 0.5× against Flying cancel. This hit removes 145/394 HP, **36.8%** of Gyarados's maximum HP.
2. Gyarados uses **Dragon Dance**, raising Attack and Speed one stage. Its Speed becomes 391, overtaking Greninja's 377.
3. Gyarados now acts first and uses **Ice Fang** against the new Grass typing. It is super effective, with 95% base accuracy. It removes 206/286 HP, **72.0%**, leaving Greninja on 80 HP.
4. Greninja uses **Rock Slide**, exploiting Gyarados's Flying weakness. Its base accuracy is 90%; this seeded attempt hits for 116/394 HP, **29.4%**. Greninja's physical Attack is lower than its Special Attack; super effectiveness does not by itself guarantee the largest hit.
5. Greninja uses priority **Water Shuriken**, moving before the faster Gyarados. Gyarados resists Water. The engine resolves two hits of six HP each: 12/394 HP, **3.0%** in total. Protean does not change Greninja again in this battle because Generation 9 permits one activation per switch-in.
6. Gyarados uses **Crunch**. It has 100% base accuracy and neutral effectiveness against Grass. The calculator gives 117–138 potential damage here, enough to remove Greninja's remaining 80 HP. Actual HP removed is 80, not the uncapped potential roll. Greninja faints. **Gyarados wins with 121/394 HP, 30.7%.**

All spoken percentages are rounded from exact engine HP changes. Base accuracy is shown for this unchanged-accuracy setup; it is not a promise across every possible field condition.

## Move catalogue prototype

| Pokémon | Four equipped moves | Additional verified reserve |
|---|---|---|
| Gyarados | Dragon Dance, Ice Fang, Crunch, Waterfall | Earthquake |
| Greninja | Grass Knot, Rock Slide, Water Shuriken, Dark Pulse | Ice Beam |

`move-catalogue.json` includes type, category, power, base accuracy and priority. Both equipped sets and each reserve substitution passed the simulator's legality validator for this format. This completes the two-Pokémon prototype; a proposed 50-Pokémon catalogue has not been claimed as complete. A future selector should account for the target's current typing, STAB, physical/special stats, HP needed to KO, accuracy, priority, setup effects and defensive consequences of type changes, rather than rotating attacks merely for variety.

## Visuals and delivery

Seven original generated full-scene illustrations: three Greninja actions, three Gyarados actions, and a Gyarados victory portrait. The result frame combines that portrait with a crop of Greninja from the finishing Crunch scene, labelled with its actual zero HP and fainted state. A separate resting-opponent portrait was unavailable. Motion consists of framing, camera moves, cuts, impact effects and HP animation over these images. Character motion is limited. The art is a stylized illustration of mechanics, not official footage or a literal claim that Grass Knot creates visible vines in every game.

This is a review file. Nothing was uploaded to YouTube or used to replace an accepted release schedule for this sample.

## Sources checked 24 October 2026

- https://www.smogon.com/dex/sv/pokemon/gyarados/
- https://www.smogon.com/dex/sv/pokemon/greninja/
- https://www.smogon.com/dex/sv/abilities/protean/
- https://github.com/smogon/pokemon-showdown
- https://github.com/smogon/pokemon-showdown/blob/master/data/moves.ts
- https://github.com/smogon/pokemon-showdown/blob/master/data/abilities.ts

The actual numerical results come from the pinned locally executed engine, not invented narrative percentages. Built-in image generation made the artwork; no paid external API or billing was enabled. Full prompts are in image-prompts.json.

## Reproduce

Install the package-lock.json dependencies with `npm ci --ignore-scripts --omit=optional`, then run `node simulate_tactical.cjs` and `node compare_finisher.cjs`. The included narration.wav and story.json can be reused for rendering. The renderer uses Python, Pillow, numpy, soundfile and FFmpeg; speech regeneration additionally uses Kokoro ONNX. Source model weights are not included. The companion render-support files provide the existing pronunciation rules and speech setup.
