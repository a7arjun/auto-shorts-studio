"""Operate on a recorded video ID; never insert or reupload a video."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from .pokemon_publish import Ledger, services, check_processed, verify_public


def short_eligibility(item):
    details=item.get('fileDetails',{})
    streams=details.get('videoStreams',[])
    if not streams:
        raise RuntimeError('Owner media dimensions unavailable; cannot verify Shorts eligibility')
    stream=streams[0]
    width=int(stream['widthPixels']);height=int(stream['heightPixels'])
    if stream.get('rotation') in ('clockwise','counterClockwise'):
        width,height=height,width
    duration=float(details['durationMs'])/1000
    if width>height or not 0<duration<=180:
        raise RuntimeError('Uploaded media does not meet square/vertical, up-to-three-minute Shorts criteria')
    return {'width':width,'height':height,'duration':duration,
            'note':'Eligible media format; YouTube controls actual Shorts classification.'}


def operate(request,ledger,config,youtube,public,info):
    action=request['action'];video_id=request['video_id']
    if action not in ('publish','cancel'):
        raise ValueError('Unknown video action')
    job=next((j for j in ledger.data['jobs'] if j.get('video_id')==video_id),None)
    if not job or job.get('channel_id')!=info['channel_id']:
        raise RuntimeError('Control request must target a recorded video on the bound channel')
    if not info['can_manage']:
        raise RuntimeError('Missing video-management authorization')
    item=check_processed(youtube,video_id,info['channel_id'])
    if action=='publish':
        if job['mode']!='pilot' or job['status'] not in ('private_verified','published'):
            raise RuntimeError('This publish operation is restricted to the verified first pilot')
        media=youtube.videos().list(part='snippet,status,fileDetails',id=video_id).execute().get('items',[])
        if not media or media[0]['snippet']['channelId']!=info['channel_id']:
            raise RuntimeError('Cannot verify uploaded media owner')
        job['short_eligibility']=short_eligibility(media[0])
        if item['status'].get('privacyStatus')!='public':
            youtube.videos().update(part='status',body={'id':video_id,'status':{
                'privacyStatus':'public','selfDeclaredMadeForKids':config['made_for_kids']}}).execute()
        verify_public(public,video_id,info['channel_id'])
        job['status']='published'
        job['public_verified_at']=datetime.now(timezone.utc).isoformat()
    else:
        # Omitting publishAt while updating status removes the scheduled release.
        youtube.videos().update(part='status',body={'id':video_id,'status':{
            'privacyStatus':'private','selfDeclaredMadeForKids':config['made_for_kids']}}).execute()
        items=youtube.videos().list(part='snippet,status',id=video_id).execute().get('items',[])
        if (not items or items[0]['snippet']['channelId']!=info['channel_id'] or
            items[0]['status'].get('privacyStatus')!='private' or items[0]['status'].get('publishAt')):
            raise RuntimeError('Cancellation not verified')
        job['status']='cancelled'
        job['cancelled_at']=datetime.now(timezone.utc).isoformat()
    job['control_request_id']=request['request_id']
    ledger.save('Verify Pokemon video '+action+' '+video_id)
    print('VERIFIED '+action+': https://www.youtube.com/shorts/'+video_id)
    if action=='publish':
        print('MEDIA:',json.dumps(job['short_eligibility']))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',default='data/pokemon_control.json')
    args=parser.parse_args()
    config=json.loads(Path('data/pokemon_channel.json').read_text())
    request=json.loads(Path(args.request).read_text())
    youtube,public,info=services(config)
    operate(request,Ledger(),config,youtube,public,info)


if __name__=='__main__':
    main()
