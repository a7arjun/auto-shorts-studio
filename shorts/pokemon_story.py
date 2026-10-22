"""English analysis grounded in the simulator's exact HP log, without an LLM API."""
import hashlib
import json
import re


def hp_value(text):
    if 'fnt' in text:
        return 0.0
    value = text.split()[0]
    if '/' in value:
        current, maximum = map(float, value.split('/'))
        return current / maximum
    return float(value) / 100


def battle_events(battle):
    health = [1.0, 1.0]
    events = []
    turn = 0
    current = None
    for line in battle['representative']['log']:
        parts = line.split('|')
        kind = parts[1] if len(parts) > 1 else ''
        if kind == 'turn':
            turn = int(parts[2])
        elif kind == 'move':
            actor = 0 if parts[2].startswith('p1') else 1
            current = {'turn': turn, 'actor': actor, 'move': parts[3],
                       'before': health.copy(), 'after': health.copy(),
                       'miss': False, 'critical': False, 'super_effective': False,
                       'resisted': False, 'immune': False, 'recoil': False, 'damage': 0.0, 'knockout': False}
            events.append(current)
        elif kind in ('-damage', '-heal'):
            side = 0 if parts[2].startswith('p1') else 1
            before_hp = health[side]
            health[side] = hp_value(parts[3])
            if current and side != current['actor'] and kind == '-damage' and not any('[from]' in p for p in parts[4:]):
                current['damage'] += max(0, before_hp - health[side])
                current['knockout'] = health[side] == 0
            if current:
                current['after'] = health.copy()
                if side == current['actor'] and kind == '-damage':
                    current['recoil'] = True
        elif current and kind in ('-miss', '-crit', '-supereffective', '-resisted', '-immune'):
            current[{'-miss': 'miss', '-crit': 'critical', '-supereffective': 'super_effective',
                     '-resisted': 'resisted', '-immune': 'immune'}[kind]] = True
    return events


def make_story(battle, brand, visual_assets=None):
    a, b = [row['species'] for row in battle['builds']]
    events = battle_events(battle)
    if not events or not battle['representative']['winner']:
        raise ValueError('No resolved representative battle; skip this matchup')
    seed = int(hashlib.sha256(battle['key'].encode()).hexdigest()[:8], 16)
    hook = [f'{a} versus {b}. Who wins when we test the actual game mechanics?',
            f'Can {a} beat {b}? We ran the matchup instead of guessing.',
            f'{a} or {b}? Type advantage is only part of this battle.'][seed % 3]
    segments = [{'kind': 'intro', 'heading': 'WHO TAKES IT?', 'text': hook, 'health': [1, 1]}]
    segments.append({'kind': 'rules', 'heading': 'THE CONDITIONS',
                     'text': 'Both are level one hundred, with legal offensive builds. Base forms only. No switching or special transformations.',
                     'health': [1, 1]})
    first, second = battle['builds']
    if first['item'] == 'Assault Vest' or second['item'] == 'Assault Vest':
        vest = first if first['item'] == 'Assault Vest' else second
        other = second if vest is first else first
        detail = f"{vest['species']}'s Assault Vest boosts special defense by fifty percent."
        if other['item'] == 'Life Orb':
            detail += f" {other['species']}'s Life Orb boosts damage, but costs health after successful attacks."
        elif other['item'] == 'Light Ball':
            detail += " Pikachu's Light Ball doubles both attacking stats."
        else:
            detail = 'Both carry Assault Vest, boosting special defense by fifty percent. This protects against special attacks.'
    elif first['item'] == 'Light Ball' or second['item'] == 'Light Ball':
        detail = "Pikachu's Light Ball doubles both attacking stats. Its opponent carries Life Orb, boosting damage at a health cost."
    else:
        detail = f"Both carry Life Orb, boosting damage at a health cost. {a} has {first['ability']}; {b} has {second['ability']}."
    segments.append({'kind': 'builds', 'heading': 'THE LOADOUT', 'health': [1, 1], 'text': detail})
    # Show a contiguous prefix and the final decisive event. Clearly label omitted turns.
    selected = events if len(events) <= 3 else [events[0], events[1], events[-1]]
    previous = None
    for event in selected:
        actor = event['actor']; target = 1 - actor
        names = [a, b]
        jump = previous is not None and events.index(event) > events.index(previous) + 1
        lead = f"Later, on turn {event['turn']}, " if jump else ''
        if event['miss']:
            text = f"{lead}{names[actor]} uses {event['move']}, but misses. Accuracy can change the result."
        elif event['immune']:
            text = f"{lead}{names[actor]} tries {event['move']}, but {names[target]} is immune."
        else:
            lost = round(event['damage'] * 100)
            remaining = round(event['after'][target] * 100)
            text = f"{lead}{names[actor]} uses {event['move']}, removing {lost} percent of {names[target]}'s maximum health."
            if event['knockout']:
                text += ' That secures the knockout.'
            elif event['super_effective']:
                text += ' It hits for super effective damage.'
            elif event['resisted']:
                text += ' The target resists this attack.'
            if event['critical']:
                text += ' This hit was critical.'
        segments.append({'kind': 'attack', 'heading': event['move'].upper(),
                         'text': text, 'health': event['after'], 'event': event})
        previous = event
    winner = battle['favorite']
    if winner:
        won = battle['wins'][winner]
        verdict = f"Across {battle['trials']} seeded simulations, {winner} wins {won}. That's with these builds and our attack selection strategy. Change the setup, and the answer can change."
        heading = f'{winner.upper()} FAVORED'
    else:
        verdict = f"Across {battle['trials']} seeded simulations, neither side leads. This matchup depends on the builds, the strategy, and the rolls."
        heading = 'NO CLEAR FAVORITE'
    segments.append({'kind': 'verdict', 'heading': heading, 'text': verdict,
                     'health': events[-1]['after']})
    title = f'{a} vs {b}: Who Wins This Build Matchup? #Shorts'
    description = (f'{brand}: independent English Pokemon game analysis.\n\n'
                   f"{battle['trials']} seeded simulations; wins: {json.dumps(battle['wins'])}.\n"
                   f"Rules: {battle['format']}, level 100. {battle['assumptions']}\n"
                   f"Strategy: {battle['policy']}\n\n"
                   'The video shows selected turns from one representative simulation. Percentages are rounded from exact HP, not invented. '
                   'This is a conditional game simulation, not a canonical anime result or proof of absolute peak strength.\n\n'
                   'Builds:\n' + '\n'.join(f"{r['species']}: {r['nature']}; {r['ability']}; {r['item']}; EVs {r['evs']}; moves {', '.join(r['moves'])}." for r in battle['builds']) +
                   '\n\nOriginal layout and synthesized narration. No anime clips or franchise music. '
                   'Not affiliated with or endorsed by The Pokemon Company, Nintendo, Game Freak or Creatures.\n'
                   'Simulator: Pokemon Showdown (MIT); damage calculator: @smogon/calc (MIT); voice: Kokoro (Apache-2.0 weights).\n'
                   '#Pokemon #PokemonBattle #Shorts')
    if visual_assets:
        description += '\n\nPokemon mini-icons retrieved through PokeAPI; underlying character artwork remains with its respective rights holders.\nCharacter image sources:\n' + '\n'.join(a['species']+': '+a['source_url'] for a in visual_assets)
    return {'title': title[:100], 'description': description, 'segments': segments,
            'tags': ['Pokemon', 'Pokemon battle', a, b, 'game mechanics', 'battle simulation'],
            'language': 'en', 'brand': brand, 'visual_assets': visual_assets or []}
