"""Free PokéAPI mini-icons: discover, validate, cache, attribute and render.

API availability is not a licence to the underlying Pokémon artwork.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlparse
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSET_ROOT=ROOT/'assets/pokemon'
CACHE_ROOT=ROOT/'.cache/pokemon-images'
API_BASE='https://pokeapi.co/api/v2/pokemon/'
API_TTL=30*86400
SNAPSHOT_PATH=ROOT/'pokemon/image_catalogue.json'
MAX_BYTES=5*1024*1024
INDEX_LOCK=threading.RLock()
ICON_FIELDS=[
    ('bdsp-mini',('versions','generation-viii','brilliant-diamond-shining-pearl','icons','front_default')),
    ('sv-mini',('versions','generation-ix','scarlet-violet','icons','front_default')),
    ('swsh-pixel',('versions','generation-viii','sword-shield','icons','front_default')),
    ('gen8-pixel',('versions','generation-viii','icons','front_default')),
    ('gen7-pixel',('versions','generation-vii','icons','front_default')),
]
RIGHTS_NOTE=('Pokemon character images remain copyright their respective owners. '
             'Retrieved as reference illustrations for independent battle commentary; '
             'PokeAPI access and the repository licence do not establish a commercial artwork licence.')

class ImageSourceError(RuntimeError):
    pass

def slug(species):
    value=species.lower().strip().replace(' ','-')
    if not re.fullmatch('[a-z0-9-]+',value):
        raise ImageSourceError('Unsupported Pokemon name: '+species)
    return value

def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+str(threading.get_ident())+'.tmp')
    temp.write_text(json.dumps(data,indent=2)+'\n')
    os.replace(temp,path)

def image_candidates(data):
    for style,field in ICON_FIELDS:
        value=data.get('sprites',{})
        for key in field:
            value=value.get(key) if isinstance(value,dict) else None
        if isinstance(value,str) and value:
            parsed=urlparse(value)
            if parsed.scheme=='https' and parsed.hostname=='raw.githubusercontent.com' and parsed.path.startswith('/PokeAPI/sprites/') and parsed.path.endswith(('.png','.webp')) and Path(parsed.path).stem==str(data.get('id')):
                yield style,value

def validate_image(content):
    if not content or len(content)>MAX_BYTES:
        raise ImageSourceError('Missing or oversized Pokemon image')
    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in ('PNG','WEBP') or not (1<=image.width<=2048 and 1<=image.height<=2048):
                raise ImageSourceError('Unexpected Pokemon image format or dimensions')
            image.load()
            if not image.convert('RGBA').getchannel('A').getbbox():
                raise ImageSourceError('Empty Pokemon image')
            return image.format,list(image.size)
    except (OSError,ValueError) as exc:
        raise ImageSourceError('Invalid Pokemon image') from exc

class PokeAPIImages:
    def __init__(self,cache_root=None,session=None):
        self.root=Path(cache_root) if cache_root is not None else CACHE_ROOT
        self.session=session or requests.Session()
        self.session.headers.update({'User-Agent':'BattleLogicLab/1.0 (cached Pokemon mini-icon reference images)'})
        self.root.mkdir(parents=True,exist_ok=True)

    def get(self,url,image=False):
        last=None
        for attempt in range(3):
            try:
                with self.session.get(url,timeout=(10,30),stream=True,allow_redirects=False) as response:
                    response.raise_for_status()
                    if 300<=response.status_code<400:
                        raise ImageSourceError('Unexpected image-source redirect')
                    chunks=[];size=0
                    for chunk in response.iter_content(65536):
                        size+=len(chunk)
                        if size>MAX_BYTES:
                            raise ImageSourceError('Image-source response exceeds limit')
                        chunks.append(chunk)
                    content=b''.join(chunks)
                    return content if image else json.loads(content)
            except (requests.RequestException,ValueError,ImageSourceError) as exc:
                last=exc
                code=getattr(getattr(exc,'response',None),'status_code',None)
                if code and code not in (429,500,502,503,504):
                    break
                if attempt<2:
                    time.sleep(2**attempt)
        raise ImageSourceError('Pokemon image source unavailable') from last

    def index(self):
        path=self.root/'index.json'
        try:
            data=json.loads(path.read_text())
            if isinstance(data.get('entries'),dict):
                return data
        except (OSError,ValueError,AttributeError):
            pass
        return {'version':1,'entries':{}}

    def valid_record(self,record,species):
        if not isinstance(record,dict) or not isinstance(record.get('file'),str) or record.get('species')!=species or record.get('api_name')!=slug(species):
            return False
        path=(self.root/record['file']).resolve()
        if self.root.resolve() not in path.parents or not path.is_file():
            return False
        content=path.read_bytes()
        return hashlib.sha256(content).hexdigest()==record.get('sha256')

    def resolve(self,species):
        name=slug(species)
        with INDEX_LOCK:
            existing=self.index()['entries'].get(species)
        if self.valid_record(existing,species):
            return {**existing,'path':str(self.root/existing['file']),'cache_hit':True}
        metadata=self.root/'api'/(name+'.json')
        data=None;origin='cached-api'
        if metadata.exists() and time.time()-metadata.stat().st_mtime<API_TTL:
            try:
                data=json.loads(metadata.read_text())
            except (OSError,ValueError):
                pass
        if data is None:
            origin='live-api'
            try:
                data=self.get(API_BASE+name+'/')
            except ImageSourceError:
                snapshot=json.loads(SNAPSHOT_PATH.read_text())
                data=snapshot.get('entries',{}).get(species)
                if data is None:
                    raise
                origin='bundled-api-snapshot'
            if not isinstance(data,dict) or data.get('name')!=name or not isinstance(data.get('id'),int):
                raise ImageSourceError('API returned the wrong Pokemon identity')
            atomic_json(metadata,data)
        if not isinstance(data,dict) or data.get('name')!=name or not isinstance(data.get('id'),int):
            raise ImageSourceError('Cached API identity mismatch')
        failures=[]
        for style,url in image_candidates(data):
            try:
                content=self.get(url,image=True)
                format,size=validate_image(content)
                suffix='.png' if format=='PNG' else '.webp'
                relative='images/'+name+'-'+style+suffix
                path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True)
                temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(content);os.replace(temp,path)
                record={'species':species,'api_name':name,'pokemon_id':data['id'],'file':relative,
                        'provider':'pokeapi','style':style,'api_url':API_BASE+name+'/','metadata_origin':origin,
                        'source_url':url,'original_size':size,'sha256':hashlib.sha256(content).hexdigest(),
                        'retrieved_at':time.time(),'rights_status':'underlying_pokemon_rights_reserved',
                        'usage_basis':RIGHTS_NOTE,'copyright':'The Pokemon Company / Nintendo / Creatures / GAME FREAK'}
                with INDEX_LOCK:
                    index=self.index();index['entries'][species]=record;atomic_json(self.root/'index.json',index)
                return {**record,'path':str(path),'cache_hit':False}
            except ImageSourceError as exc:
                failures.append(str(exc))
        raise ImageSourceError('No usable mini/chibi icon for '+species+': '+'; '.join(failures))

@lru_cache(maxsize=64)
def asset_record(species):
    manifest=json.loads((ASSET_ROOT/'manifest.json').read_text())
    entry=manifest.get('entries',{}).get(species)
    if entry:
        if not entry.get('source_url') or not entry.get('usage_basis'):
            raise ImageSourceError('Local override needs its source and documented usage basis')
        file=(ASSET_ROOT/entry['file']).resolve()
        if ASSET_ROOT.resolve() not in file.parents or file.suffix.lower() not in ('.png','.webp'):
            raise ImageSourceError('Invalid local character image path')
        validate_image(file.read_bytes())
        return {**entry,'species':species,'provider':'local-override','path':str(file)}
    if manifest.get('provider')=='pokeapi':
        return PokeAPIImages().resolve(species)
    return None

@lru_cache(maxsize=64)
def character_image(species):
    record=asset_record(species)
    if record is None:
        return None
    with Image.open(record['path']) as source:
        image=source.convert('RGBA')
        image=image.crop(image.getchannel('A').getbbox())
        scale=min(230/image.width,230/image.height)
        resample=Image.Resampling.NEAREST if record.get('style','').endswith('pixel') else Image.Resampling.LANCZOS
        return image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),resample)

def ensure_characters(pair):
    records=[]
    for species in pair:
        record=asset_record(species)
        if record is None:
            raise ImageSourceError('Character image unavailable for '+species)
        records.append({key:value for key,value in record.items() if key not in ('path','file','cache_hit')})
    return records

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--warm-roster',action='store_true');args=parser.parse_args()
    names=[b['species'] for b in json.loads((ROOT/'pokemon/builds.json').read_text())]
    if not args.warm_roster:
        names=['Charizard','Blastoise']
    with ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(lambda name:PokeAPIImages().resolve(name),names))
    for record in records:
        print(record['species']+': '+record['style']+' / '+('cached' if record['cache_hit'] else 'downloaded'))
    print('Verified images: '+str(len(records)))
