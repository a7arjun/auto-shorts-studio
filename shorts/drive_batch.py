"""Private Drive Shorts pipeline. Never put credentials or Drive IDs in Git."""
import argparse,json,os,re,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
from shorts.scene_selector import select_scenes
from shorts.modern_factory import write_srt,add_captions,write_upload_package
from shorts.movie_clips import render_clip
from shorts.seo import build_metadata

STATE=Path("data/drive_publish_state.json")
OUT=Path("output/drive-batch")
FILMS=[("Hera Pheri",2000),("Hulchul",2004)]
CAP=30

def state():
    d=json.loads(STATE.read_text(encoding="utf-8"))
    for k in ("published","private_tests","reservations"):d.setdefault(k,[])
    return d
def save(d): STATE.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def ids():
    parts=[s.strip() for s in os.getenv("GDRIVE_SOURCE_FILE_IDS","").split(",")]
    if len(parts)!=2 or not all(re.fullmatch(r"[A-Za-z0-9_-]{20,128}",s) for s in parts):
        raise RuntimeError("Set GDRIVE_SOURCE_FILE_IDS GitHub secret with two file IDs")
    return parts
def drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    client=os.environ["YT_HI_CLIENT_ID"];secret=os.environ["YT_HI_CLIENT_SECRET"]
    token=os.environ["GDRIVE_REFRESH_TOKEN"]
    creds=Credentials(None,refresh_token=token,token_uri="https://oauth2.googleapis.com/token",
                      client_id=client,client_secret=secret,scopes=["https://www.googleapis.com/auth/drive.readonly"])
    creds.refresh(Request())
    return build("drive","v3",credentials=creds,cache_discovery=False)
def check(api,file_ids):
    for i,id in enumerate(file_ids):
        data=api.files().get(fileId=id,fields="name,mimeType,size,capabilities/canDownload").execute()
        if data.get("mimeType")!="video/mp4" or int(data.get("size",0))>1200*1024*1024:
            raise ValueError("Source is not a valid MP4 under 1.2GB")
        if data.get("capabilities",{}).get("canDownload") is False:
            raise PermissionError("Drive file cannot be downloaded")
        print("SOURCE CHECK:",FILMS[i][0],data["name"],data.get("size"))
def download(api,file_id):
    from googleapiclient.http import MediaIoBaseDownload
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"source.mp4";tmp=OUT/"source.partial"
    try:
        with tmp.open("wb") as f:
            dl=MediaIoBaseDownload(f,api.files().get_media(fileId=file_id),chunksize=8*1024*1024)
            done=False
            while not done:
                _,done=dl.next_chunk(num_retries=3)
                if f.tell()>1200*1024*1024:raise ValueError("Source too large")
        if tmp.stat().st_size<100000:raise RuntimeError("Incomplete movie")
        tmp.replace(path)
    finally:tmp.unlink(missing_ok=True)
    return path
def guard(mode,d):
    if mode!="public":return
    for key in ("BOLLYWOOD_PUBLIC_ENABLED","BOLLYWOOD_RIGHTS_CONFIRMED","BOLLYWOOD_PRIVATE_TEST_VERIFIED"):
        if os.getenv(key)!="true":raise RuntimeError("Public release blocked: "+key)
    if not d["private_tests"]:raise RuntimeError("Private test not recorded")
    if len(d["published"])>=CAP:raise RuntimeError("30 public Shorts already published")
def pick(d):
    counts=[sum(x["movie_index"]==i for kind in ("published","reservations","private_tests")
                for x in d[kind]) for i in range(2)]
    available=[i for i in range(2) if counts[i]<16]
    return min(available,key=lambda i:counts[i]) if available else None
def transcript(video):
    from faster_whisper import WhisperModel
    model=WhisperModel("tiny",device="cpu",compute_type="int8")
    info=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(video)])
    duration=float(json.loads(info)["format"]["duration"])
    phrases=[]
    for i,fraction in enumerate((.12,.30,.48,.66,.82)):
        start=max(0,min(duration-241,duration*fraction))
        wav=OUT/f"sample_{i}.wav"
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-ss",str(start),"-i",str(video),
                        "-t","240","-vn","-ar","16000","-ac","1",str(wav)],check=True,timeout=260)
        try:
            segments,_=model.transcribe(str(wav),language="hi",word_timestamps=True,vad_filter=True,beam_size=2)
            for segment in segments:
                words=list(segment.words or [])
                if not words:
                    if segment.text.strip():phrases.append({"start":start+segment.start,"end":start+segment.end,"text":segment.text.strip()})
                    continue
                group=[]
                for w in words:
                    if w.start is None or w.end is None:continue
                    group.append(w)
                    if w.end-group[0].start>=3.5 or len(group)>=9 or w.word.strip().endswith(("।","?","!",".")):
                        phrases.append({"start":start+group[0].start,"end":start+group[-1].end,"text":" ".join(v.word.strip() for v in group)})
                        group=[]
                if group:phrases.append({"start":start+group[0].start,"end":start+group[-1].end,"text":" ".join(v.word.strip() for v in group)})
        finally:wav.unlink(missing_ok=True)
    return sorted([s for s in phrases if s["end"]>s["start"] and s["text"]],key=lambda s:s["start"])
def prepare(mode):
    d=state();guard(mode,d)
    if len(d["published"])>=CAP:print("Batch complete");return False
    movie_i=pick(d)
    if movie_i is None:print("All source allocations exhausted");return False
    file_ids=ids();api=drive();check(api,file_ids)
    video=download(api,file_ids[movie_i]);segments=transcript(video)
    ranked=select_scenes(segments,min_seconds=15,max_seconds=40,count=100)
    used=[x for kind in ("published","private_tests","reservations") for x in d[kind] if x["movie_index"]==movie_i]
    scene=next((s for s in ranked if all(max(0,min(s["end"],u["end"])-max(s["start"],u["start"]))<=1 for u in used)),None)
    if not scene:raise RuntimeError("No unused dialogue scene available")
    start,end=scene["start"],scene["end"]
    raw=render_clip(video,OUT/"raw.mp4",start,end-start,keep_audio=True)
    subtitle=write_srt(segments,start,end,OUT/"captions.srt")
    rendered=add_captions(raw,subtitle,OUT/"short.mp4")
    title,year=FILMS[movie_i]
    metadata=build_metadata(title,year=year,scene_label="Funny Scene")
    write_upload_package(OUT,rendered,metadata)
    job={"key":hashlib.sha256(f"{movie_i}:{start}:{end}".encode()).hexdigest()[:16],
         "movie_index":movie_i,"start":start,"end":end,"kind":mode,
         "created_at":datetime.now(timezone.utc).isoformat()}
    d["reservations"].append(job);save(d)
    (OUT/"job.json").write_text(json.dumps(job),encoding="utf-8")
    return True
def upload():
    d=state();job=json.loads((OUT/"job.json").read_text())
    if not any(x["key"]==job["key"] for x in d["reservations"]):raise RuntimeError("No reservation")
    guard(job["kind"],d)
    from shorts.youtube import upload as yt_upload
    meta=json.loads((OUT/"upload_package.json").read_text())["youtube"]
    os.environ["YT_PRIVACY_STATUS"]="public" if job["kind"]=="public" else "private"
    url=yt_upload("hindi",OUT/"short.mp4",meta)
    d["reservations"]=[x for x in d["reservations"] if x["key"]!=job["key"]]
    job.update({"youtube_url":url,"privacy":os.environ["YT_PRIVACY_STATUS"]})
    d["published" if job["kind"]=="public" else "private_tests"].append(job)
    save(d);print("UPLOADED",url,job["privacy"])
def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("check","private","public","upload"),required=True)
    mode=p.parse_args().mode
    if mode=="check":check(drive(),ids())
    elif mode=="upload":upload()
    else:prepare(mode)
if __name__=="__main__":main()
