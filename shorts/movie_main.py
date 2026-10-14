"""Automatic film excerpt generation / publishing entry point."""
import argparse
import json
import os
from datetime import datetime,timezone
from pathlib import Path
from .commons_media import download_commons
from .movie_clips import make_demo_source,make_metadata,render_clip,select_item

STATE=Path("data/movie_state.json")
def run(channel,dry_run):
    state=json.loads(STATE.read_text(encoding="utf-8"))
    if not dry_run and os.getenv("AUTOPUBLISH_ENABLED")!="true":
        raise RuntimeError("AUTOPUBLISH_ENABLED is not true")
    item,start,duration=select_item(channel,state.get(channel,[]))
    folder=Path("output")/channel
    folder.mkdir(parents=True,exist_ok=True)
    if dry_run:
        src=make_demo_source(folder/"test-source.mp4")
        start,duration=0,8
        rights={"dry_run":True}
    else:
        src,rights=download_commons(item,Path(".cache/movie_sources"))
    out=render_clip(src,folder/(item["id"]+"-clip.mp4"),start,duration,
                    keep_audio=item.get("keep_audio",True))
    metadata=make_metadata(item,channel,start)
    (folder/"metadata.json").write_text(json.dumps({**metadata,"rights":rights,"dry_run":dry_run},indent=2),encoding="utf-8")
    if dry_run:
        print("DRY RUN: "+str(out))
        return
    from .youtube import upload
    url=upload(channel,out,metadata)
    state.setdefault(channel,[]).append({"source_id":item["id"],"start_second":start,
       "video_url":url,"published_at":datetime.now(timezone.utc).isoformat()})
    STATE.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    print("PUBLISHED "+url)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--channel",choices=["both","hindi","english"],default="both")
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    errors=[]
    for name in (["hindi","english"] if args.channel=="both" else [args.channel]):
        try:run(name,args.dry_run)
        except Exception as exc:
            print("FAILED "+name+": "+str(exc),flush=True)
            errors.append(name)
    if errors:raise SystemExit("Failed: "+",".join(errors))
if __name__=="__main__":main()
