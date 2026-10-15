"""Search popular 2000+ comedy movie clips WITHOUT downloading/uploading copyrighted footage.

Use YOUTUBE_DATA_API_KEY to get actual YouTube results; otherwise export research
queries with clickable YouTube search links. Discovery does NOT grant reuse rights.
"""
import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import requests

CATALOGUE=Path("data/modern_movies.json")
DEFAULT_OUTPUT=Path("output/discovery")
SEARCH_API="https://www.googleapis.com/youtube/v3/search"
VIDEOS_API="https://www.googleapis.com/youtube/v3/videos"
CHANNELS=("bollywood","hollywood")

def load_movies(path=CATALOGUE):
    movies=json.loads(Path(path).read_text(encoding="utf-8"))
    for channel in CHANNELS:
        if channel not in movies or not movies[channel]:
            raise ValueError("Empty movie catalogue for "+channel)
        for movie in movies[channel]:
            if int(movie["year"]) < 2000:
                raise ValueError("Movie must be from 2000 or later: "+movie["movie"])
    return movies

def daily_picks(items,channel,date,count=2):
    """Rotate deterministically; distribute queries across different days."""
    start=int(hashlib.sha256((date+channel).encode()).hexdigest()[:10],16)%len(items)
    return [items[(start+i)%len(items)] for i in range(min(count,len(items)))]

def movie_query(movie):
    return f'{movie["movie"]} {movie["year"]} funny comedy scene movie clip'

def search_link(query):
    return "https://www.youtube.com/results?"+urlencode({"search_query":query})

def request_json(url,params):
    response=requests.get(url,params=params,timeout=35,headers={"User-Agent":"AutoShortsStudio/0.4"})
    response.raise_for_status()
    value=response.json()
    if "error" in value:raise RuntimeError(str(value["error"]))
    return value

def get_candidates(movie,channel,key,limit=10):
    query=movie_query(movie)
    search=request_json(SEARCH_API,{"part":"snippet","q":query,"type":"video",
        "maxResults":limit,"order":"viewCount","regionCode":movie["region"],
        "relevanceLanguage":movie["language"],"key":key})
    items=search.get("items",[])
    ids=[x["id"]["videoId"] for x in items if x.get("id",{}).get("videoId")]
    if not ids:return []
    details=request_json(VIDEOS_API,{"part":"statistics,snippet,status",
                                     "id":",".join(ids),"key":key})
    by_id={x["id"]:x for x in details.get("items",[])}
    rows=[]
    now=datetime.now(timezone.utc)
    for item in items:
        vid=item.get("id",{}).get("videoId")
        video=by_id.get(vid)
        if not video:continue
        snippet=video.get("snippet",{})
        views=int(video.get("statistics",{}).get("viewCount") or 0)
        try:
            published=datetime.fromisoformat(snippet["publishedAt"].replace("Z","+00:00"))
            days=max(1,(now-published).days)
        except (ValueError,KeyError):days=365
        likes=int(video.get("statistics",{}).get("likeCount") or 0)
        # Score is for discovery only, not a claim that the video is trending.
        score=round(views/max(days,7)**0.8 + likes*0.5,1)
        rows.append({"channel":channel,"movie":movie["movie"],"movie_year":movie["year"],
             "query":query,"video_id":vid,"url":"https://www.youtube.com/watch?v="+vid,
             "title":snippet.get("title",""),"uploader":snippet.get("channelTitle",""),
             "published_at":snippet.get("publishedAt",""),"views":views,"likes":likes,
             "score":score,"youtube_declared_license":video.get("status",{}).get("license","unknown"),
             "rights_verified":False,"upload_eligible":False,"source_type":"youtube_search_result"})
    return sorted(rows,key=lambda r:r["score"],reverse=True)

def run(date=None,key=None,out=DEFAULT_OUTPUT,per_channel=2):
    date=date or datetime.now(timezone.utc).date().isoformat()
    key=key or os.getenv("YOUTUBE_DATA_API_KEY")
    movies=load_movies()
    output=Path(out);output.mkdir(parents=True,exist_ok=True)
    rows=[]
    errors=[]
    for channel in CHANNELS:
        for item in daily_picks(movies[channel],channel,date,per_channel):
            q=movie_query(item)
            if not key:
                rows.append({"channel":channel,"movie":item["movie"],"movie_year":item["year"],
                   "query":q,"search_url":search_link(q),"source_type":"research_query",
                   "status":"API key required for live results",
                   "rights_verified":False,"upload_eligible":False})
                continue
            try:rows+=get_candidates(item,channel,key)
            except (requests.RequestException,RuntimeError,ValueError) as exc:
                errors.append({"channel":channel,"movie":item["movie"],"error":str(exc)})
    rows.sort(key=lambda x:float(x.get("score") or 0),reverse=True)
    result={"date":date,"mode":"live_youtube_metadata" if key else "offline_search_queries",
            "note":"Search results are research ONLY. Reuse rights are unverified, even for videos marked CC.",
            "rows":rows,"errors":errors}
    (output/"modern_movies.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    headers=["channel","movie","movie_year","query","search_url","video_id","url",
             "title","uploader","published_at","views","likes","score",
             "youtube_declared_license","rights_verified","upload_eligible","source_type","status"]
    with (output/"modern_movies.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} research entries in {output}; mode={result['mode']}; API errors={len(errors)}")
    for err in errors:print("API ERROR:",err["channel"],err["movie"],err["error"][:160])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--date",help="UTC date YYYY-MM-DD")
    p.add_argument("--per-channel",type=int,default=2,help="YouTube searches per channel per run; each search consumes quota")
    args=p.parse_args()
    if args.per_channel<1 or args.per_channel>5:p.error("per-channel must be between 1 and 5")
    run(date=args.date,per_channel=args.per_channel)
