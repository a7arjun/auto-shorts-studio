"""Source-backed named-version assessments, separate from measured game results."""
import json
from pathlib import Path


def assessment(pair):
    data=json.loads(Path('pokemon/anime_assessments.json').read_text())
    comparison=next((x for x in data['comparisons'] if set(x['pair'])==set(pair)),None)
    if not comparison:
        return {'status':'unresolved','scope':data['scope'],'checked_on':data['checked_on'],
                'profiles':[],'lean':None,'confidence':'insufficient evidence',
                'spoken_take':'For named anime versions, we do not have enough verified evidence to choose a winner. No anime odds are claimed.'}
    profiles=[data['profiles'][n] for n in pair]
    if any(not p.get('sources') or not p.get('trainer') for p in profiles):
        raise ValueError('Named anime analysis requires sourced trainer identities')
    return {**comparison,'status':'editorial_inference','scope':data['scope'],
            'checked_on':data['checked_on'],'profiles':profiles}


def add_assessment(story,battle):
    result=assessment([b['species'] for b in battle['builds']])
    health=story['segments'][-1]['health']
    if result['profiles']:
        evidence='Anime evidence: '+' '.join(p['feat'] for p in result['profiles'])
        story['segments'].append({'kind':'anime_evidence','heading':'ANIME EVIDENCE',
                                 'text':evidence,'health':health})
    story['segments'].append({'kind':'anime_verdict','heading':'ANIME: '+(result['lean'] or 'UNRESOLVED').upper(),
                             'text':result['spoken_take'],'health':health})
    story['anime_assessment']=result
    story['description']+='\n\nANIME ANALYSIS — SEPARATE EDITORIAL INFERENCE\n'+result['scope']+'\n'
    story['description']+='Lean: '+(result['lean'] or 'unresolved')+'; confidence: '+result['confidence']+'.\n'
    for profile in result['profiles']:
        story['description']+=profile['version']+': '+profile['feat']+'\n'
        story['description']+='\n'.join(s['url'] for s in profile['sources'])+'\n'
    story['description']+=result.get('reason','Insufficient sourced comparison.')+'\nEvidence snapshot: '+result['checked_on']
    return result
