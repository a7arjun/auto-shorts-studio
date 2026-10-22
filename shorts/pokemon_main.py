"""Free English Pokemon factory: select, simulate, narrate, render, upload."""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
from .pokemon_publish import Ledger, can_start, today, services, upload_private, check_processed, publish_existing
from .pokemon_story import make_story

OUT=Path('output/pokemon')


def choose_pair(state,date):
    builds=json.loads(Path('pokemon/builds.json').read_text())
    used={tuple(sorted(j['pair'])) for j in state['jobs'] if j.get('pair')}
    pairs=[p for p in itertools.combinations([b['species'] for b in builds],2) if tuple(sorted(p)) not in used]
    if not pairs:
        raise RuntimeError('All validated matchups used; expand the build catalogue')
    # Stable daily selection: retries use the same pair, never a random duplicate.
    return sorted(pairs,key=lambda p:hashlib.sha256((date+'|'.join(p)).encode()).hexdigest())[0]


def prepare(pair,key,config):
    OUT.mkdir(parents=True,exist_ok=True)
    result=subprocess.run(['node','pokemon/simulate.cjs',*pair,key,str(config['trials'])],
                          check=True,capture_output=True,text=True,timeout=120)
    battle=json.loads(result.stdout)
    (OUT/'battle.json').write_text(json.dumps(battle,indent=2))
    story=make_story(battle,config['brand'])
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


def run(mode):
    config=json.loads(Path('data/pokemon_channel.json').read_text()); date=today()
    ledger=Ledger()
    OUT.mkdir(parents=True,exist_ok=True)
    if mode=='probe':
        _,_,info=services(config)
        (OUT/'connection.json').write_text(json.dumps(info,indent=2))
        print(json.dumps(info)); return
    # Reconcile a known upload before considering another video. Never repeat insert.
    pending=[j for j in ledger.data['jobs'] if j['status'] in ('uploaded','processing_pending','publishing')]
    if pending and mode!='preview':
        youtube,public,info=services(config)
        job=pending[0]
        check_processed(youtube,job['video_id'],info['channel_id'])
        if job['mode']=='daily':
            if not config['publication_enabled'] or not info['can_manage']:
                raise RuntimeError('Publication disabled or management scope missing')
            publish_existing(youtube,public,job['video_id'],config,info['channel_id'])
            job['status']='published'
        else:
            job['status']='private_verified';ledger.data['pilot_verified']=True
        ledger.save('Reconcile Pokemon upload '+job['key'])
        print('Reconciled https://youtu.be/'+job['video_id']);return
    if not can_start(ledger.data,config,date,mode):
        print('No upload due: pilot, publication or daily/monthly limit');return
    youtube=public=info=None
    if mode!='preview':
        youtube,public,info=services(config)
        (OUT/'connection.json').write_text(json.dumps(info,indent=2))
        if mode=='daily' and not info['can_manage']:
            raise RuntimeError('Existing OAuth needs youtube.force-ssl authorization for verified public publishing')
    pair=('Charizard','Blastoise') if mode in ('pilot','preview') and not ledger.data['jobs'] else choose_pair(ledger.data,date)
    key='pilot-v1' if mode in ('pilot','preview') else date+'-'+'-'.join(pair).lower()
    story=prepare(pair,key,config)
    if mode=='preview':
        print('Preview ready:',OUT/'short.mp4');return
    job={'key':key,'pair':list(pair),'mode':mode,'date':date,'status':'uploading',
         'created_at':datetime.now(timezone.utc).isoformat(),'channel_id':info['channel_id']}
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
        job['status']='publishing'; ledger.save('Publish verified Pokemon Short '+key)
        publish_existing(youtube,public,video_id,config,info['channel_id'])
        job['status']='published'
    ledger.save('Verify Pokemon upload '+key)
    print(job['status']+': https://youtu.be/'+video_id)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['preview','probe','pilot','daily'],default='preview')
    run(parser.parse_args().mode)
