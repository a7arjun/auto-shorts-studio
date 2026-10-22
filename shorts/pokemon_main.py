"""Free English Pokemon factory: select, simulate, narrate, render, upload."""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
from .pokemon_publish import Ledger, can_start, today, services, upload_private, check_processed, schedule_existing, verify_public, publication_slot, require_future_slot, parse_time, MissedPublicationSlot, daily_review_slots, require_review_deadline
from .pokemon_story import make_story
from .pokemon_research import select_researched_pair, apply_metadata
from .pokemon_quality import assess_battle, require_battle, require_story, BattleRejected

OUT=Path('output/pokemon')


def choose_pair(state,date):
    builds=json.loads(Path('pokemon/builds.json').read_text())
    used={tuple(sorted(j['pair'])) for j in state['jobs'] if j.get('pair')}
    pairs=[p for p in itertools.combinations([b['species'] for b in builds],2) if tuple(sorted(p)) not in used]
    if not pairs:
        raise RuntimeError('All validated matchups used; expand the build catalogue')
    # Stable daily selection: retries use the same pair, never a random duplicate.
    return sorted(pairs,key=lambda p:hashlib.sha256((date+'|'.join(p)).encode()).hexdigest())[0]


def simulate_pair(pair,key,config):
    result=subprocess.run(['node','pokemon/simulate.cjs',*pair,key,str(config['trials'])],
                          check=True,capture_output=True,text=True,timeout=120)
    return json.loads(result.stdout)


def prepare(pair,key,config,research=None,battle=None):
    battle=battle or simulate_pair(pair,key,config)
    presentation=require_battle(battle)
    from .pokemon_assets import ensure_characters
    assets=ensure_characters(pair)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'presentation_quality.json').write_text(json.dumps(presentation,indent=2))
    (OUT/'battle.json').write_text(json.dumps(battle,indent=2))
    story=make_story(battle,config['brand'],visual_assets=assets)
    require_story(story,battle)
    if research:
        apply_metadata(story,battle,research)
        (OUT/'research.json').write_text(json.dumps(research,indent=2))
    (OUT/'assets.json').write_text(json.dumps(assets,indent=2))
    from .pokemon_voice import synthesize
    from .pokemon_render import render
    synthesize(story,OUT/'voice.wav',config['voice'],config['voice_speed'])
    # Long narration fails quality checks before reserving or uploading anything.
    if not 20 <= story['duration'] <= 90:
        raise RuntimeError('Narration outside the supported Short length')
    (OUT/'story.json').write_text(json.dumps(story,indent=2))
    quality=render(battle,story,OUT/'voice.wav',OUT/'short.mp4')
    (OUT/'quality.json').write_text(json.dumps(quality,indent=2))
    return story


def run(mode,requested_slot=None):
    config=json.loads(Path('data/pokemon_channel.json').read_text()); date=today()
    ledger=Ledger()
    OUT.mkdir(parents=True,exist_ok=True)
    if mode=='probe':
        _,_,info=services(config)
        (OUT/'connection.json').write_text(json.dumps(info,indent=2))
        print(json.dumps(info)); return
    # Reconcile known IDs before allocating another slot. No second insert on retry.
    pending=[j for j in ledger.data['jobs'] if j['status'] in ('uploaded','processing_pending','publishing') or
             (j['status']=='scheduled' and parse_time(j['publish_at'])<=datetime.now(timezone.utc))]
    if pending and mode!='preview':
        youtube,public,info=services(config)
        for job in pending:
            existing=check_processed(youtube,job['video_id'],info['channel_id'])
            if job['mode']=='daily':
                if not config['publication_enabled'] or not info['can_manage']:
                    raise RuntimeError('Publication disabled or management scope missing')
                if not job.get('publish_at'):
                    raise RuntimeError('Legacy upload needs an explicit publication slot')
                if parse_time(job['publish_at'])<=datetime.now(timezone.utc):
                    if existing['status'].get('privacyStatus')=='private' and not existing['status'].get('publishAt'):
                        job['status']='missed_slot'  # Leave a late unscheduled upload private.
                    else:
                        verify_public(public,job['video_id'],info['channel_id'])
                        job['status']='published'
                else:
                    try:
                        schedule_existing(youtube,job['video_id'],config,info['channel_id'],job['publish_at'])
                        job['status']='scheduled'
                    except MissedPublicationSlot:
                        job['status']='missed_slot'
            else:
                job['status']='private_verified';ledger.data['pilot_verified']=True
            ledger.save('Reconcile Pokemon upload '+job['key'])
            print('Reconciled https://youtu.be/'+job['video_id'])
    slot=(requested_slot or publication_slot(config)) if mode=='daily' else None
    if mode=='daily' and slot is None:
        print('No upload due: outside preparation window');return
    if slot:
        date=slot['date']
    if not can_start(ledger.data,config,date,mode,slot['slot'] if slot else None):
        print('No upload due: pilot, publication, occupied slot or daily/monthly limit');return
    youtube=public=info=None
    if mode!='preview':
        youtube,public,info=services(config)
        (OUT/'connection.json').write_text(json.dumps(info,indent=2))
        if mode=='daily' and not info['can_manage']:
            raise RuntimeError('Existing OAuth needs youtube.force-ssl authorization for verified public publishing')
    pair=('Charizard','Blastoise') if mode in ('pilot','preview') and not ledger.data['jobs'] else choose_pair(ledger.data,date)
    key='pilot-v1' if mode in ('pilot','preview') else slot['slot']
    if slot:
        revisions=sum(j.get('slot')==slot['slot'] for j in ledger.data['jobs'])
        if revisions:
            key+='-r'+str(revisions+1)
    research=None;cache={};rejections=[]
    def eligible(candidate):
        identity=tuple(candidate)
        if identity not in cache:
            cache[identity]=simulate_pair(candidate,key,config)
        quality=assess_battle(cache[identity])
        if not quality['eligible']:
            rejections.append({'pair':list(candidate),'reasons':quality['reasons'],'wins':quality['wins']})
        return quality['eligible']
    if mode!='preview':
        pair,research=select_researched_pair(public,json.loads(Path('pokemon/builds.json').read_text()),
                    ledger.data,key,info['channel_id'],fixed_pair=pair if mode=='pilot' else None,
                    candidate_filter=eligible)
        (OUT/'research.json').write_text(json.dumps(research,indent=2))
    else:
        # Offline software preview follows the same editorial checks, without a trend claim.
        selection={'jobs':list(ledger.data['jobs'])}
        while not eligible(pair):
            selection['jobs'].append({'pair':list(pair)})
            pair=choose_pair(selection,key)
    (OUT/'rejected_matchups.json').write_text(json.dumps(rejections,indent=2))
    story=prepare(pair,key,config,research=research,battle=cache.get(tuple(pair)))
    if mode=='preview':
        print('Preview ready:',OUT/'short.mp4');return
    if slot:
        try:
            require_future_slot(slot['publish_at'])
            require_review_deadline(config,slot['publish_at'])
        except MissedPublicationSlot:
            print('Preparation missed slot; no upload');return
    job={'key':key,'pair':list(pair),'mode':mode,'date':date,'status':'uploading',
         'created_at':datetime.now(timezone.utc).isoformat(),'channel_id':info['channel_id']}
    if research:
        job['research']={'checked_at':research['checked_at'],'video_ids':[r['id'] for r in research['references']],
                         'title':story['title'],'hashtags':story.get('hashtags',[])}
    if slot:
        job.update(slot)
    ledger.data['jobs'].append(job)
    ledger.save('Reserve Pokemon upload '+key)
    video_id=upload_private(youtube,OUT/'short.mp4',story,config)
    job.update(video_id=video_id,status='uploaded')
    (OUT/'upload.json').write_text(json.dumps(job,indent=2))
    ledger.save('Record private Pokemon upload '+key)
    check_processed(youtube,video_id,info['channel_id'])
    if mode=='pilot':
        job['status']='private_verified'; ledger.data['pilot_verified']=True
    else:
        try:
            schedule_existing(youtube,video_id,config,info['channel_id'],slot['publish_at'])
            job['status']='scheduled'
        except MissedPublicationSlot:
            job['status']='missed_slot'
    ledger.save('Verify Pokemon upload '+key)
    print(job['status']+': https://youtu.be/'+video_id)


def run_daily_batch():
    config=json.loads(Path('data/pokemon_channel.json').read_text())
    if not config['publication_enabled'] or not config.get('production_runner_ready',False):
        print('Daily posting requested but production runner is not ready; no upload');return
    slots=daily_review_slots(config)
    if not slots:
        print('Outside the morning preparation window; no upload');return
    for slot in slots:
        run('daily',requested_slot=slot)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['preview','probe','pilot','daily'],default='preview')
    mode=parser.parse_args().mode
    run_daily_batch() if mode=='daily' else run(mode)
