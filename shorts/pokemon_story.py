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
    attack_index=0
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
            metadata=battle['representative'].get('attacks',[])
            if attack_index<len(metadata):
                move=metadata[attack_index]
                if move['actor']!=actor or move['move']!=parts[3]:
                    raise ValueError('Move metadata does not match the simulator log')
                current.update(move_type=move['type'],move_category=move['category'])
            current['sequence']=attack_index
            attack_index+=1
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
                    current['self_damage_source']=next((p.replace('[from] ','') for p in parts[4:] if p.startswith('[from] ')), 'follow-up damage')
        elif current and kind in ('-miss', '-crit', '-supereffective', '-resisted', '-immune'):
            current[{'-miss': 'miss', '-crit': 'critical', '-supereffective': 'super_effective',
                     '-resisted': 'resisted', '-immune': 'immune'}[kind]] = True
    return events


def make_story(battle, brand, visual_assets=None):
    a, b = [row['species'] for row in battle['builds']]
    events = battle_events(battle)
    if not events or not battle['representative']['winner']:
        raise ValueError('No resolved representative battle; skip this matchup')
    hook=f'{a} or {b}? Game battle, then anime verdict.'
    segments = [{'kind':'intro','heading':'WHO WINS?', 'text':hook,'health':[1,1]}]
    # Show every move in order. Never skip an opponent's intervening attack.
    actual_winner=battle['representative']['winner']
    selected=events
    previous = None
    for event in selected:
        actor = event['actor']; target = 1 - actor
        names = [a, b]
        jump = events.index(event)>0 and (previous is None or events.index(event)>events.index(previous)+1)
        lead = f"Later, on turn {event['turn']}, " if jump else ''
        if event['miss']:
            text = f"{names[actor]} uses {event['move']}, but misses!"
        elif event['immune']:
            text = f"{lead}{names[actor]} tries {event['move']}, but {names[target]} is immune."
        else:
            text = f"{names[actor]} uses {event['move']}!"
            if event['knockout']:
                text += ' That secures the knockout.'
            elif event['super_effective']:
                text += ' It hits for super effective damage.'
            elif event['resisted']:
                text += ' The target resists this attack.'
            if event['critical']:
                text += ' This hit was critical.'
        if event['recoil'] and event['after'][actor]==0:
            source=event.get('self_damage_source','follow-up damage')
            source='Life Orb recoil' if source=='item: Life Orb' else source.removeprefix('item: ')
            text += f' {names[actor]} then faints from {source}.'
        segments.append({'kind': 'attack', 'heading': event['move'].upper(),
                         'text': text, 'health': event['after'], 'event': event})
        previous = event
    winner = battle['favorite']
    if winner:
        won = battle['wins'][winner]
        verdict = f"The game test favors {winner}. These are tested builds, not an overall power ranking."
        heading = f'{winner.upper()} FAVORED'
    else:
        verdict = f"Across {battle['trials']} seeded simulations, neither side leads. This matchup depends on the builds, the strategy, and the rolls."
        heading = 'NO CLEAR FAVORITE'
    verdict=f'{actual_winner} wins this example. '+verdict
    segments.append({'kind': 'verdict', 'heading': heading, 'text': verdict,
                     'health': events[-1]['after']})
    title = f'{a} vs {b}: Who Wins This Build Matchup? #Shorts'
    description = (f'{brand}: independent English Pokemon game analysis.\n\n'
                   f"{battle['trials']} seeded simulations; wins: {json.dumps(battle['wins'])}.\n"
                   f"Rules: {battle['format']}, level 100. {battle['assumptions']}\n"
                   f"Strategy: {battle['policy']}\n\n"
                   'The video shows every attack in one selected simulated battle, in order. A multi-attack example is selected when available; aggregate trial results include all runs. Visual HP is rounded from exact HP, not invented. '
                   'This is a conditional game simulation, not a canonical anime result or proof of absolute peak strength.\n\n'
                   'Builds:\n' + '\n'.join(f"{r['species']}: {r['nature']}; {r['ability']}; {r['item']}; EVs {r['evs']}; moves {', '.join(r['moves'])}." for r in battle['builds']) +
                   '\n\nOriginal layout and synthesized narration. No anime clips or franchise music. '
                   'Not affiliated with or endorsed by The Pokemon Company, Nintendo, Game Freak or Creatures.\n'
                   'Simulator: Pokemon Showdown (MIT); damage calculator: @smogon/calc (MIT); voice: Kokoro (Apache-2.0 weights).\n'
                   '#Pokemon #PokemonBattle #Shorts')
    if battle.get('tested_builds'):
        description+='\nGame test: '+str(battle['build_sampling']['combination_count'])+' build combinations, balanced round-robin allocation. No popularity weighting.\n'
        for options in battle['tested_builds']:
            description+='; '.join(o['set']['species']+' / '+o['id']+' / '+o['set']['item']+' / '+o['set']['nature']+' / EVs '+json.dumps(o['set']['evs']) for o in options)+'\n'
    if visual_assets:
        description += '\n\nPokemon mini-icons retrieved through PokeAPI; underlying character artwork remains with its respective rights holders.\nCharacter image sources:\n' + '\n'.join(a['species']+': '+a['source_url'] for a in visual_assets)
    return {'title': title[:100], 'description': description, 'segments': segments,
            'tags': ['Pokemon', 'Pokemon battle', a, b, 'game mechanics', 'battle simulation'],
            'language': 'en', 'brand': brand, 'visual_assets': visual_assets or []}
