"""Build captioned Bollywood Shorts from *authorized* source footage.

The YouTube discovery feed is research metadata only and is never a download input.
Preview is safe/offline. Publishing is disabled unless explicitly configured.
"""
import argparse
import ipaddress
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from .movie_clips import make_demo_source, render_clip
from .scene_selector import select_scenes

DEFAULT_MANIFEST = Path("data/authorized_modern_sources.json")
DEFAULT_STATE = Path("data/modern_publish_state.json")
VIDEO_LIMIT = 250 * 1024 * 1024
BLOCKED_HOSTS = ("youtube.com", "youtu.be", "googlevideo.com", "tiktok.com",
                 "instagram.com", "facebook.com", "vimeo.com")

def validate_source(item):
    """Check a pre-registered rights statement, *not* independently certify copyright."""
    if item.get("channel") != "hindi" or not item.get("enabled"):
        raise ValueError("Source not enabled for Hindi channel")
    if item.get("license_type") not in {"owned", "licensed", "public_domain"}:
        raise ValueError("License type must be owned, licensed or public_domain")
    if item.get("usage_authorized") is not True:
        raise ValueError("Rights-holder or authorized operator has not marked footage usable")
    if not (item.get("rights_reference") and item.get("source_id") and item.get("title")):
        raise ValueError("Source ID, title and a documented rights reference are required")
    url = item.get("media_url", "")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or "@" in parsed.netloc:
        raise ValueError("Source URL must be public HTTPS")
    if any(host == bad or host.endswith("." + bad) for bad in BLOCKED_HOSTS):
        raise ValueError("Video-platform uploads are not approved downloadable assets")
    if host in {"localhost", "127.0.0.1"} or host.endswith(".local"):
        raise ValueError("Private address blocked")
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("Private address blocked")
    except ValueError as exc:
        if str(exc) == "Private address blocked":
            raise
    return True

def eligible_source(manifest=DEFAULT_MANIFEST, state_file=DEFAULT_STATE):
    catalogue=json.loads(Path(manifest).read_text(encoding="utf-8"))
    state=json.loads(Path(state_file).read_text(encoding="utf-8"))
    published={x["source_id"] for x in state.get("published",[])}
    for entry in catalogue.get("sources",[]):
        if entry.get("source_id") in published or not entry.get("enabled"):
            continue
        validate_source(entry)
        return entry, state
    return None,state

def fetch_licensed_source(entry, output_dir):
    validate_source(entry)
    destination=Path(output_dir)/"authorized-source.mp4"
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists() and destination.stat().st_size>10000:
        return destination
    temp=destination.with_suffix(".partial")
    length=0
    try:
        with requests.get(entry["media_url"],stream=True,timeout=(20,100),
                          allow_redirects=False,headers={"User-Agent":"AutoShortsStudio/1.0"}) as response:
            response.raise_for_status()
            if int(response.headers.get("Content-Length",0))>VIDEO_LIMIT:
                raise ValueError("Source media larger than 250 MB")
            with temp.open("wb") as file:
                for chunk in response.iter_content(1024*512):
                    if not chunk:
                        continue
                    length+=len(chunk)
                    if length>VIDEO_LIMIT:
                        raise ValueError("Source exceeds size limit")
                    file.write(chunk)
        if length<10000:
            raise ValueError("Empty or too-small source file")
        temp.replace(destination)
        return destination
    finally:
        temp.unlink(missing_ok=True)

def transcribe_audio(media_path, model_name="tiny"):
    """Optional free local speech recognition; GitHub preview tests use a fixed transcript."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install faster-whisper>=1.1,<2") from exc
    model=WhisperModel(model_name,device="cpu",compute_type="int8")
    segments,_=model.transcribe(str(media_path),language="hi",beam_size=1,
                                vad_filter=True,condition_on_previous_text=False)
    values=[{"start":float(s.start),"end":float(s.end),"text":s.text.strip()}
            for s in segments if s.text.strip()]
    if len(values)<2:
        raise RuntimeError("Too little intelligible Hindi speech to select a comedy scene")
    return values

def srt_time(t):
    milliseconds=max(0,int(round(t*1000)))
    hours,rest=divmod(milliseconds,3600000)
    minutes,rest=divmod(rest,60000)
    seconds,millis=divmod(rest,1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def write_srt(segments, start, end, destination):
    lines=[]
    for seg in segments:
        seg_start=max(start,float(seg["start"]))
        seg_end=min(end,float(seg["end"]))
        if seg_end-seg_start<0.12:
            continue
        text=re.sub(r"\s+"," ",str(seg["text"])).strip()
        if not text:continue
        # Keep Unicode Hindi text and original punctuation.
        lines.extend([str(len(lines)//4+1),
                      f"{srt_time(seg_start-start)} --> {srt_time(seg_end-start)}",
                      text,""])
    path=Path(destination)
    path.parent.mkdir(parents=True,exist_ok=True)
    if not lines:
        raise RuntimeError("Selected scene had no valid caption segments")
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return path

def add_captions(rendered,subtitles,output):
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    # Run with captions directory as working dir so filter paths contain no unsafe chars.
    subs=Path(subtitles).resolve()
    video=Path(rendered).resolve()
    font="Noto Sans Devanagari"
    style=(f"FontName={font},FontSize=21,Bold=1,"
           "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
           "BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=170")
    filter_arg=f"subtitles={subs.name}:force_style='{style}'"
    command=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-i",str(video),"-vf",filter_arg,
             "-c:v","libx264","-preset","veryfast","-crf","27",
             "-c:a","copy","-movflags","+faststart",str(output)]
    subprocess.run(command,cwd=str(subs.parent),check=True,timeout=360)
    if not output.exists() or output.stat().st_size<20000:
        raise RuntimeError("Caption rendering failed")
    return output

def check_export(video):
    result=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                           "-show_entries","stream=width,height",
                           "-of","json",str(video)],capture_output=True,
                           text=True,check=True,timeout=30)
    data=json.loads(result.stdout)
    stream=data["streams"][0]
    if (stream["width"],stream["height"])!=(720,1280):
        raise RuntimeError("Wrong output dimensions")
    return stream

def process_video(video,segments,output_dir,source_details=None):
    root=Path(output_dir)
    root.mkdir(parents=True,exist_ok=True)
    ranked=select_scenes(segments,min_seconds=15,max_seconds=40,count=3)
    if not ranked:
        raise RuntimeError("Could not identify a 15–40-second dialogue scene")
    winner=ranked[0]
    start=winner["start"];end=winner["end"]
    raw=render_clip(video,root/"uncaptioned.mp4",start,end-start,keep_audio=True)
    sub=write_srt(segments,start,end,root/"captions.srt")
    finished=add_captions(raw,sub,root/"bollywood_short.mp4")
    stream=check_export(finished)
    meta={"type":"captioned_comedy_scene","scene":winner,
          "other_candidates":ranked[1:],"video_path":str(finished),
          "dimensions":stream,
          "source":source_details or {"type":"original synthetic demo"}}
    (root/"render_report.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Rendered {finished} | start={start}s | duration={end-start}s | bytes={finished.stat().st_size}")
    return finished,meta

def demo():
    output=Path("output/modern-demo")
    output.mkdir(parents=True,exist_ok=True)
    # Original synthetic video test pattern; no studio footage / film dialogue.
    media=output/"synthetic-source.mp4"
    command=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-f","lavfi","-i","testsrc2=size=640x360:rate=15",
             "-f","lavfi","-i","sine=frequency=420:sample_rate=22050",
             "-t","43","-c:v","libx264","-preset","ultrafast","-crf","36",
             "-c:a","aac","-shortest",str(media)]
    subprocess.run(command,check=True,timeout=90)
    transcript=json.loads(Path("data/demo_dialogue.json").read_text(encoding="utf-8"))["segments"]
    video,report=process_video(media,transcript,output)
    # This test video is original synthetic footage, not a Bollywood scene.
    metadata={
        "title":"Original Test Pattern | Auto Shorts Studio #Shorts",
        "description":"Original synthetic test footage to validate Shorts rendering and captions. Not a movie scene.\n#Shorts",
        "tags":["Shorts","Video pipeline test","Original footage"]
    }
    write_upload_package(output,video,metadata)
    # Separate illustrative SEO example; deliberately NOT the demo video's metadata.
    from .seo import build_metadata
    sample=build_metadata("Hera Pheri",scene_label="Baburao Comedy Moment",
                          featured_characters=["Baburao"])
    (output/"example_film_seo_only.json").write_text(
        json.dumps({"example_only_not_used_for_demo":True,"metadata":sample},
                   ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return video,report

def prepare_upload_metadata(entry):
    """Build film-specific YouTube metadata only for a verified source manifest.

    This does not infer characters or actors from a film-level cast list.
    The entry's 'verified_featured_characters' must be clip-specific.
    """
    validate_source(entry)
    from .seo import build_metadata
    return build_metadata(
        film=entry.get("film") or entry["title"],
        year=entry.get("film_year"),
        scene_label=entry.get("scene_label"),
        featured_characters=entry.get("verified_featured_characters",[]),
        source_credit=entry.get("source_credit") or entry["rights_reference"],
        rights_text=entry["rights_reference"])

def write_upload_package(output_dir,video,metadata):
    """Produce inspectable video+SEO output without calling YouTube."""
    output=Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    check_export(video)
    required=("title","description","tags")
    if any(not metadata.get(key) for key in required):
        raise ValueError("Upload metadata must have title, description and tags")
    if len(metadata["title"])>100 or len(metadata["description"])>5000:
        raise ValueError("YouTube text limits exceeded")
    payload={"video_path":str(video),"youtube":metadata,"upload_executed":False}
    (output/"upload_package.json").write_text(
        json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SEO PACKAGE PREPARED:",metadata["title"])
    print("TAGS:",", ".join(metadata["tags"]))
    return payload

def run_authorized(publish=False):
    entry,state=eligible_source()
    if entry is None:
        print("No enabled, authorized modern Bollywood footage is configured; nothing to publish.")
        return None
    root=Path("output/authorized-modern")
    media=fetch_licensed_source(entry,root)
    transcript=transcribe_audio(media,os.getenv("WHISPER_MODEL","tiny"))
    short,report=process_video(media,transcript,root,entry)
    metadata=prepare_upload_metadata(entry)
    write_upload_package(root,short,metadata)
    if not publish:
        return short
    if os.getenv("MODERN_AUTOPUBLISH_ENABLED")!="true":
        raise RuntimeError("MODERN_AUTOPUBLISH_ENABLED must be true for unattended uploads")
    from .youtube import upload
    video_url=upload("hindi",short,metadata)
    state.setdefault("published",[]).append({
        "source_id":entry["source_id"],"url":video_url,
        "timestamp":datetime.now(timezone.utc).isoformat()})
    DEFAULT_STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("UPLOADED AUTHORIZED VIDEO:",video_url)
    return video_url

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true",help="Synthetic movie-free test and captions")
    p.add_argument("--publish",action="store_true",help="Publish one pre-authorized film source; private by default")
    args=p.parse_args()
    if args.demo and args.publish:
        p.error("Cannot publish the synthetic demo with this command")
    if args.demo:
        demo()
    else:
        run_authorized(publish=args.publish)
if __name__=="__main__":
    main()
