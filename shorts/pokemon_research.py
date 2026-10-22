"""Bounded, fresh YouTube metadata research; no paid model or video downloads."""
import calendar
from datetime import datetime, timezone
import hashlib
import itertools
import math
import re
import unicodedata


class ResearchUnavailable(RuntimeError):
    pass


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c)).casefold()


def cutoff_time(now):
    month=now.month-4;year=now.year
    if month<=0:
        month+=12;year-=1
    return now.replace(year=year,month=month,day=min(now.day,calendar.monthrange(year,month)[1]))


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z','+00:00'))


def mentions(text,name):
    return bool(re.search(r'(?<![a-z])'+re.escape(normalize(name))+r'(?![a-z])',normalize(text)))


def relevant(item,pair=None):
    snippet=item.get('snippet',{});title=normalize(snippet.get('title',''))
    if snippet.get('defaultAudioLanguage',snippet.get('defaultLanguage','en')).split('-')[0]!='en':
        return False
    # Our videos are base-form game simulations; don't chase incompatible formats.
    if re.search(r'\b(tcg|cards?|pack opening|pokemon go|pok[eé]mon go|mega|gigantamax|dynamax|shiny|anime|ash)\b',title):
        return False
    if not re.search(r'\b(vs|versus|battle|wins?|stronger|comparison|compare|showdown)\b',title):
        return False
    return pair is None or all(mentions(title,name) for name in pair)


def evidence(items,now,own_channel=None):
    """Recheck actual video dates, identities and visible statistics after search."""
    rows=[];seen=set();cutoff=cutoff_time(now)
    for item in items:
        ident=item.get('id','');snippet=item.get('snippet',{})
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}',ident) or ident in seen:
            continue
        seen.add(ident)
        try:
            published=timestamp(snippet['publishedAt'])
            views=int(item.get('statistics',{}).get('viewCount',0))
            likes=int(item.get('statistics',{}).get('likeCount',0))
            comments=int(item.get('statistics',{}).get('commentCount',0))
        except (KeyError,ValueError,TypeError):
            continue
        if not cutoff<=published<=now or views<=0 or snippet.get('channelId')==own_channel or not relevant(item):
            continue
        days=max(1,(now-published).total_seconds()/86400)
        velocity=views/days
        # Lifetime average, not measured recent growth. Cap engagement influence.
        score=math.log1p(velocity)*(1+min(.15,(likes+comments)/views))*(1 if days<=90 else .8)
        rows.append({'id':ident,'url':'https://www.youtube.com/watch?v='+ident,
                     'title':snippet['title'],'description':snippet.get('description','')[:1500],
                     'channel_id':snippet.get('channelId'),'published_at':snippet['publishedAt'],
                     'views':views,'likes':likes,'comments':comments,
                     'average_views_per_day':round(velocity,2),'score':round(score,6)})
    return sorted(rows,key=lambda x:(-x['score'],x['id']))


def collect(youtube,queries,now):
    ids=[];requests=0
    for query in queries:
        for order in ('relevance','viewCount','date'):
            result=youtube.search().list(part='snippet',type='video',q=query,order=order,
                maxResults=50,publishedAfter=cutoff_time(now).isoformat().replace('+00:00','Z'),
                publishedBefore=now.isoformat().replace('+00:00','Z'),
                relevanceLanguage='en',safeSearch='strict').execute()
            requests+=1
            ids.extend(i.get('id',{}).get('videoId') for i in result.get('items',[]))
    ids=list(dict.fromkeys(i for i in ids if i))
    items=[]
    for start in range(0,len(ids),50):
        result=youtube.videos().list(part='snippet,statistics,contentDetails',id=','.join(ids[start:start+50])).execute()
        items.extend(result.get('items',[]))
    return items,requests


def select_researched_pair(youtube,builds,state,key,own_channel=None,fixed_pair=None,now=None,candidate_filter=None):
    now=now or datetime.now(timezone.utc)
    used={tuple(sorted(j['pair'])) for j in state['jobs'] if j.get('pair')}
    pairs=[p for p in itertools.combinations([b['species'] for b in builds],2) if tuple(sorted(p)) not in used]
    if fixed_pair:
        pairs=[tuple(fixed_pair)]
    if not pairs:
        raise ResearchUnavailable('All validated matchups have been used')
    try:
        items,calls=collect(youtube,['Pokemon battle versus who wins','Pokemon battle comparison'],now)
        rows=evidence(items,now,own_channel)
        def pair_score(pair):
            matches=[r for r in rows if all(mentions(r['title'],n) for n in pair)]
            # Only the strongest result per channel contributes to ranking.
            channels={}
            for row in matches:
                channels.setdefault(row['channel_id'],row['score'])
            return sum(sorted(channels.values(),reverse=True)[:5])
        pairs.sort(key=lambda p:(-pair_score(p),hashlib.sha256((key+'|'.join(p)).encode()).hexdigest()))
        exact_attempts=0;matches=[];rejected=[]
        for pair in pairs:
            if candidate_filter is not None and not candidate_filter(pair):
                rejected.append(list(pair));continue
            exact_attempts+=1
            more,extra=collect(youtube,[f'Pokemon {pair[0]} vs {pair[1]} battle'],now)
            calls+=extra
            rows=evidence(items+more,now,own_channel)
            matches=[r for r in rows if all(mentions(r['title'],n) for n in pair)]
            if matches:
                break
            if exact_attempts>=3:
                break
        if not matches:
            raise ResearchUnavailable('No eligible multi-attack matchup with recent references; skip upload')
    except ResearchUnavailable:
        raise
    except Exception:
        # Don't expose credential-bearing request URLs from client exceptions.
        raise ResearchUnavailable('Recent YouTube research failed; no video will be uploaded') from None
    return pair,{'status':'researched','checked_at':now.isoformat(),
                 'published_after':cutoff_time(now).isoformat(),'pair':list(pair),
                 'search_calls':calls,'mechanically_rejected_pairs':rejected,'matched_video_count':len(matches),'references':matches[:20],
                 'method':'Relevant public metadata; lifetime average views/day, capped engagement and recency. Not verified recent growth or a complete census.',
                 'language_note':'English query preference; explicitly non-English metadata excluded; missing language is not proof of English audio.'}


def apply_metadata(story,battle,research):
    a,b=[r['species'] for r in battle['builds']]
    if research.get('status')!='researched' or research['pair']!=[a,b] or not research.get('references'):
        raise ResearchUnavailable('Missing matching research evidence')
    refs=research['references']
    candidates=[('test',f'{a} vs {b}: We Tested {battle["trials"]} Battles'),
                ('question',f'{a} vs {b}: Who Wins at Level 100?'),
                ('comparison',f'{a} vs {b}: Battle Simulation Explained')]
    cues={'test':('test','simulation','simulated'),'question':('who wins','stronger','versus',' vs '),
          'comparison':('comparison','compare','explained','showdown')}
    scored=[(sum(r['score'] for r in refs if any(c in normalize(r['title']) for c in cues[k])),title,k)
            for k,title in candidates]
    _,title,kind=max(scored,key=lambda x:x[0])
    title=title[:100]
    # Observed hashtags influence order only within this video's relevant whitelist.
    hashes=['#Pokemon','#PokemonBattle','#'+a,'#'+b,'#Shorts']
    observed=' '.join(r['title']+' '+r['description'] for r in refs).casefold()
    hashes.sort(key=lambda tag:(-len(re.findall(re.escape(tag.casefold())+r'(?![a-z0-9_])',observed)),tag))
    story['title']=title
    story['description']=re.sub(r'#Pokemon #PokemonBattle #Shorts','',story['description']).strip()
    story['description']=f'{a} vs {b}: a level-100 game battle simulation using the stated builds.\n\n'+story['description']+'\n\n'+' '.join(hashes)
    story['tags']=['Pokemon',a,b,f'{a} vs {b}','Pokemon battle','battle simulation','Pokemon Showdown']
    story['hashtags']=hashes
    story['segments'][0]['text']=f'{a} versus {b}. We tested {battle["trials"]} battles with these builds. Who comes out ahead?'
    story['segments'][0]['heading']='WHO WINS?'
    story['research']={'checked_at':research['checked_at'],'reference_count':len(refs),'title_angle':kind}
    research['metadata']={'selected_title':title,'title_candidates':[t for _,t in candidates],
                          'angle':kind,'hashtags':hashes,'tags':story['tags'],
                          'note':'Original titles based on relevant phrase patterns; no claim of guaranteed reach.'}
    return story
