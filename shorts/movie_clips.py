"""Select nonrepeating film excerpts, produce vertical FFmpeg video."""
import hashlib
import json
import random
import subprocess
from datetime import datetime,timezone
from pathlib import Path

CATALOGUE=Path("data/movie_sources.json")

def sources_for(channel):
    return [x for x in json.loads(CATALOGUE.read_text(encoding="utf-8"))[channel] if x.get("enabled")]

def select_item(channel,history,today=None):
    today=today or datetime.now(timezone.utc).date().isoformat()
    items=sources_for(channel)
    if not items:raise RuntimeError("No enabled sources")
    used={(v["source_id"],int(v["start_second"])) for v in history}
    offset=int(hashlib.sha256((today+channel).encode()).hexdigest()[:8],16)%len(items)
    for source in items[offset:]+items[:offset]:
        length=min(26,max(12,int(source["duration_seconds"])-2))
        upper=max(0,int(source["duration_seconds"])-length-4)
        starts=list(range(min(60,upper),upper+1,30)) or [0]
        random.Random(today+channel+source["id"]).shuffle(starts)
        for start in starts:
            if (source["id"],start) not in used:return source,start,length
    raise RuntimeError("Exhausted available source windows")

def render_clip(source,dest,start,duration,keep_audio=True):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    filters=("[0:v]split=2[back][front];"
             "[back]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=28:2[blur];"
             "[front]scale=720:1280:force_original_aspect_ratio=decrease[main];"
             "[blur][main]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    command=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-ss",str(start),
             "-i",str(source),"-t",str(duration),"-filter_complex",filters,"-map","[v]"]
    command+=["-map","0:a?","-c:a","aac","-b:a","96k"] if keep_audio else ["-an"]
    command+=["-r","24","-c:v","libx264","-preset","veryfast","-crf","28",
              "-pix_fmt","yuv420p","-movflags","+faststart","-shortest",str(dest)]
    subprocess.run(command,check=True,timeout=420)
    if not dest.exists() or dest.stat().st_size<20000:raise RuntimeError("Render failed")
    return dest

def make_metadata(source,channel,start):
    tag="#IndianClassicCinema" if channel=="hindi" else "#ClassicHollywood"
    return {"title":f"{source['film']} ({source['year']}) | Classic Movie Moments #Shorts"[:100],
            "description":f"Excerpt: {source['film']} ({source['year']}).\nSource: {source['source_page']}\nRights: {source['rights_basis']}\nAt {start} seconds.\n#Shorts {tag}"}

def make_demo_source(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-f","lavfi",
       "-i","testsrc2=size=480x270:rate=15","-f","lavfi","-i","sine=frequency=440:sample_rate=22050",
       "-t","9","-c:v","libx264","-preset","ultrafast","-crf","35",
       "-c:a","aac","-shortest",str(path)],check=True,timeout=90)
    return path
