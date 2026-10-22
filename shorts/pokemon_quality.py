"""Editorial selection only. Never alter HP, reroll seeds or cap measured wins."""
from .pokemon_story import battle_events

class BattleRejected(ValueError):
    pass


def assess_battle(battle):
    names=[b['species'] for b in battle['builds']]
    reasons=[]
    if battle['trials']!=100:
        reasons.append('Require exactly 100 seeded trials')
    if any(battle['wins'][n]>=battle['trials'] for n in names):
        reasons.append('Unanimous trial winner')
    if any(battle['wins'][n]==0 for n in names):
        reasons.append('Both Pokemon must win at least one trial')
    events=battle_events(battle)
    winner=battle['representative'].get('winner')
    if winner not in names:
        reasons.append('Representative battle has no winner')
    else:
        side=names.index(winner)
        if sum(e['actor']==side and e['damage']>0 for e in events)<2:
            reasons.append('Winner needs two successful damaging move uses')
        if not any(e['actor']!=side for e in events):
            reasons.append('Opponent must get an attack attempt')
    if any(not e.get('move_type') for e in events):
        reasons.append('Missing resolved move type')
    return {'eligible':not reasons,'reasons':reasons,'wins':battle['wins'].copy(),
            'policy':'Skip unbalanced or short examples; preserve every measured outcome and exact HP.'}


def require_battle(battle):
    quality=assess_battle(battle)
    if not quality['eligible']:
        raise BattleRejected('; '.join(quality['reasons']))
    return quality


def require_story(story,battle):
    names=[b['species'] for b in battle['builds']]
    winner=names.index(battle['representative']['winner'])
    shown={s['event']['sequence'] for s in story['segments'] if s.get('event') and
           s['event']['actor']==winner and s['event']['damage']>0}
    if len(shown)<2:
        raise BattleRejected('Video must show two distinct successful winning attacks')
