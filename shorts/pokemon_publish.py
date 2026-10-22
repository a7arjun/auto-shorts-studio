"""Persistent upload ledger and explicit destination-channel binding."""
import base64
from datetime import datetime
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo
import requests

STATE_PATH = Path('data/pokemon_state.json')
TERMINAL = {'published', 'private_verified', 'failed_before_upload', 'skipped'}


def today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()


class Ledger:
    def __init__(self, path=STATE_PATH):
        self.path=path; self.sha=None
        self.remote=os.getenv('GITHUB_ACTIONS')=='true'
        self.token=os.getenv('GITHUB_TOKEN')
        self.repository=os.getenv('GITHUB_REPOSITORY','a7arjun/auto-shorts-studio')
        if self.remote:
            if not self.token or self.repository!='a7arjun/auto-shorts-studio':
                raise RuntimeError('Missing repository-scoped state credential')
            r=requests.get(self.url,headers=self.headers,params={'ref':'main'},timeout=30)
            r.raise_for_status(); data=r.json(); self.sha=data['sha']
            self.data=json.loads(base64.b64decode(data['content']))
        else:
            self.data=json.loads(path.read_text())

    @property
    def url(self):
        return f'https://api.github.com/repos/{self.repository}/contents/{self.path.as_posix()}'

    @property
    def headers(self):
        return {'Authorization':f'Bearer {self.token}','Accept':'application/vnd.github+json',
                'X-GitHub-Api-Version':'2022-11-28'}

    def save(self, message):
        content=json.dumps(self.data,indent=2)+'\n'
        if self.remote:
            # A failed/ambiguous state write stops the job, never repeats an upload.
            r=requests.put(self.url,headers=self.headers,json={'message':message,'branch':'main',
                           'sha':self.sha,'content':base64.b64encode(content.encode()).decode()},timeout=30)
            r.raise_for_status(); self.sha=r.json()['content']['sha']
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(content)


def can_start(state,config,date,mode):
    if mode=='preview':
        return True
    unresolved=[j for j in state['jobs'] if j['status'] not in TERMINAL]
    if unresolved:
        raise RuntimeError('An earlier upload needs reconciliation; refusing a possible duplicate')
    if mode=='pilot':
        return not any(j['mode']=='pilot' and j['status']=='private_verified' for j in state['jobs'])
    if not config['publication_enabled'] or not state.get('pilot_verified'):
        return False
    public=[j for j in state['jobs'] if j['mode']=='daily' and j['status']=='published']
    return (sum(j['date']==date for j in public)<config['daily_limit'] and
            sum(j['date'][:7]==date[:7] for j in public)<config['monthly_limit'])


def services(config):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    prefix=config['credential_prefix']
    values=[os.getenv(prefix+'_'+x) for x in ('CLIENT_ID','CLIENT_SECRET','REFRESH_TOKEN')]
    if not all(values):
        raise RuntimeError('Missing existing destination YouTube credentials')
    # Refresh the existing grant, without pretending a wider scope was granted.
    credentials=Credentials(None,refresh_token=values[2],token_uri='https://oauth2.googleapis.com/token',
                            client_id=values[0],client_secret=values[1])
    credentials.refresh(Request())
    key=os.getenv('YOUTUBE_DATA_API_KEY')
    if not key:
        raise RuntimeError('Missing existing YouTube metadata API key')
    private=build('youtube','v3',credentials=credentials,cache_discovery=False)
    public=build('youtube','v3',developerKey=key,cache_discovery=False)
    scopes=requests.get('https://oauth2.googleapis.com/tokeninfo',params={'access_token':credentials.token},timeout=30)
    scopes.raise_for_status()
    granted=scopes.json().get('scope','').split()
    # No token values are recorded or printed.
    info={'granted_scopes':granted,'can_manage':any(s.endswith('/youtube') or s.endswith('/youtube.force-ssl') for s in granted)}
    reference=public.videos().list(part='snippet',id=config['reference_video_id']).execute()
    if not reference.get('items'):
        raise RuntimeError('Cannot resolve the existing channel from its known video')
    info['channel_id']=reference['items'][0]['snippet']['channelId']
    info['channel_name']=reference['items'][0]['snippet']['channelTitle']
    Path('output/pokemon').mkdir(parents=True,exist_ok=True)
    Path('output/pokemon/connection.json').write_text(json.dumps(info,indent=2))
    print('Destination:',info['channel_id'],info['channel_name'])
    print('OAuth scopes:',', '.join(granted))
    # Proves the refresh token belongs to this channel BEFORE uploading anything.
    mine=private.channels().list(part='id,snippet',mine=True).execute()
    if not any(c['id']==info['channel_id'] for c in mine.get('items',[])):
        raise RuntimeError('OAuth channel does not match the existing Bollywood channel')
    return private,public,info


def check_processed(youtube, video_id, channel_id):
    for attempt in range(18):
        data=youtube.videos().list(part='snippet,status,processingDetails,contentDetails',id=video_id).execute()
        if not data.get('items'):
            raise RuntimeError('Uploaded video unavailable to owner')
        item=data['items'][0]
        if item['snippet']['channelId']!=channel_id:
            raise RuntimeError('Unexpected upload destination')
        status=item.get('status',{}); processing=item.get('processingDetails',{}).get('processingStatus')
        if status.get('uploadStatus') in ('failed','rejected','deleted') or processing in ('failed','terminated'):
            raise RuntimeError('YouTube processing rejected the upload')
        if item.get('contentDetails',{}).get('regionRestriction',{}).get('blocked'):
            raise RuntimeError('YouTube reports regional playback restrictions')
        if processing=='succeeded' or status.get('uploadStatus')=='processed':
            return item
        time.sleep(10)
    raise RuntimeError('Processing still pending; preserve video ID for reconciliation')


def upload_private(youtube,video,story,config):
    from googleapiclient.http import MediaFileUpload
    body={'snippet':{'title':story['title'],'description':story['description'],'tags':story['tags'],
                     'categoryId':'20','defaultLanguage':'en','defaultAudioLanguage':'en'},
          'status':{'privacyStatus':'private','selfDeclaredMadeForKids':config['made_for_kids']}}
    request=youtube.videos().insert(part='snippet,status',body=body,
                    media_body=MediaFileUpload(str(video),mimetype='video/mp4',resumable=True,chunksize=4*1024*1024))
    result=None
    while result is None:
        # The client retries resumable chunks, not a second videos.insert call.
        _,result=request.next_chunk(num_retries=3)
    if not result.get('id'):
        raise RuntimeError('YouTube did not return an upload ID')
    return result['id']


def publish_existing(youtube,public,video_id,config,channel_id):
    check_processed(youtube,video_id,channel_id)
    youtube.videos().update(part='status',body={'id':video_id,'status':{
        'privacyStatus':'public','selfDeclaredMadeForKids':config['made_for_kids']}}).execute()
    # Verify actual public API visibility; an upload ID alone is not success.
    for attempt in range(12):
        result=public.videos().list(part='snippet,status,contentDetails',id=video_id).execute()
        if result.get('items'):
            item=result['items'][0]
            if item['snippet']['channelId']==channel_id and item['status']['privacyStatus']=='public':
                restrictions=item.get('contentDetails',{}).get('regionRestriction',{})
                if restrictions.get('blocked') or restrictions.get('allowed'):
                    raise RuntimeError('Public video has reported regional restrictions')
                return item
        time.sleep(5)
    raise RuntimeError('Public visibility not verified')
