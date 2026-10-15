"""Generate a rights-first Bollywood clip and in-app YouTube Remix research queue.

YouTube Data API exposes public metadata, not a clip download, copyright license,
or guaranteed YouTube Shorts Remix eligibility.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_INPUT=Path("output/discovery/modern_movies.json")
DEFAULT_OUTPUT=Path("output/source_screening")
PARTNERS=Path("data/bollywood_licensing_contacts.json")
FIELDS=("priority","movie","year","title","video_url","uploader","views","likes",
        "score","declared_license","rights_owner_confirmed","license_status",
        "automated_repost_eligible","remix_eligibility","remix_action","licensing_action")

def correct_film_candidate(item):
    """A conservative title filter, not a copyright or content authenticity check."""
    expected=str(item.get("movie") or "").casefold()
    title=str(item.get("title") or "").casefold()
    if not expected or not title:
        return False
    # Reject promotional videos and results from different franchise installments.
    if re.search(r"\b(trailer|teaser|reaction|review|explained|interview|behind the scenes|promo)\b",title):
        return False
    if expected=="dhamaal":
        return bool(re.search(r"\bdhamaal\b",title)) and not re.search(
            r"\b(total|double|dhamaal\s*[234]|dhamaal\s*(two|three|four))\b",title)
    if expected=="golmaal: fun unlimited":
        return "golmaal" in title and not re.search(
            r"\bgolmaal\s*[2345]\b|\bgolmaal\s+(returns|again)\b",title)
    tokens=[x for x in re.findall(r"[a-z0-9]+",expected) if len(x)>2]
    return bool(tokens) and all(re.search(r"\b"+re.escape(x)+r"\b",title) for x in tokens)

def select_candidates(discovery,max_per_movie=3,max_total=18):
    if max_per_movie<1 or max_total<1:
        raise ValueError("Candidate limits must be positive")
    selected=[]
    seen=set()
    counts=defaultdict(int)
    rows=sorted(discovery.get("rows",[]),
                key=lambda x:float(x.get("score") or 0),reverse=True)
    for item in rows:
        if item.get("channel")!="bollywood" or not item.get("video_id") or not correct_film_candidate(item):
            continue
        movie=str(item.get("movie") or "").strip()
        vid=str(item["video_id"])
        if not movie or vid in seen or counts[movie]>=max_per_movie:
            continue
        seen.add(vid)
        counts[movie]+=1
        selected.append({
            "priority":len(selected)+1,
            "movie":movie,
            "year":item.get("movie_year",""),
            "title":str(item.get("title") or ""),
            "video_url":"https://www.youtube.com/watch?v="+vid,
            "uploader":item.get("uploader",""),
            "views":int(item.get("views") or 0),
            "likes":int(item.get("likes") or 0),
            "score":float(item.get("score") or 0),
            "declared_license":item.get("youtube_declared_license","unknown"),
            "rights_owner_confirmed":False,
            "license_status":"not_verified",
            "automated_repost_eligible":False,
            "remix_eligibility":"unknown_check_in_youtube_app",
            "remix_action":"Open on mobile in YouTube, tap Share > Remix > Cut if available. In-app only.",
            "licensing_action":"Identify film rights holder; request permitted excerpts, written approval, and approved source file."
        })
        if len(selected)>=max_total:
            break
    return selected

def escape_table(text):
    return str(text).replace("|","/").replace("\n"," ").replace("\r"," ").replace("[","(").replace("]",")")

def build(discovery,output=DEFAULT_OUTPUT,contacts=PARTNERS,max_per_movie=3,max_total=18):
    out=Path(output)
    out.mkdir(parents=True,exist_ok=True)
    contacts=json.loads(Path(contacts).read_text(encoding="utf-8"))["partners"]
    candidates=select_candidates(discovery,max_per_movie,max_total)
    data={
        "date":discovery.get("date"),
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "input_mode":discovery.get("mode","unknown"),
        "note":"Candidate selection is research only. Film rights and in-app Remix eligibility are unverified.",
        "candidates":candidates,
        "licensing_leads_not_confirmed_rights_owners":contacts
    }
    (out/"bollywood_source_queue.json").write_text(
        json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"bollywood_source_queue.csv").open("w",newline="",encoding="utf-8-sig") as file:
        writer=csv.DictWriter(file,fieldnames=FIELDS,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(candidates)
    lines=[
        "# Bollywood comedy footage and Remix research",
        "",
        "Generated from the YouTube Data API's public metadata. No footage was downloaded.",
        "**None of these entries is approved for automated film-scene republishing.**",
        "",
        "## Priority research queue",
        "| # | Film | Candidate | Views | Rights | Remix |",
        "|---|---|---|---:|---|---|"
    ]
    for item in candidates:
        lines.append("| {priority} | {movie} | [{title}]({url}) | {views:,} | Not verified | Check in YouTube app |".format(
            priority=item["priority"],movie=escape_table(item["movie"]),
            title=escape_table(item["title"]),url=item["video_url"],views=item["views"]))
    lines.extend([
        "",
        "## Path A: YouTube Shorts Remix (manual in-app)",
        "1. Open a candidate video in the YouTube mobile app.",
        "2. Look for Share > Remix > Cut (some videos do not offer the option).",
        "3. Create the Short using YouTube's native feature with original-source attribution.",
        "4. Do not assume that a remixed Short can be downloaded and independently republished.",
        "",
        "YouTube Data API does not provide a reliable field for actual Cut/Remix availability.",
        "",
        "## Path B: Licensed footage (eligible for unattended production)",
        "1. Identify the genuine film/clip rights owner independently of the video uploader.",
        "2. Obtain written rights for editing, subtitles, 9:16 cropping, YouTube Shorts, regions, term, and monetization.",
        "3. Request the film clip through a separate rights-holder-approved media delivery route.",
        "4. Record explicit approval and the separate approved media URL in data/authorized_modern_sources.json.",
        "5. Only then run the existing authorized Shorts factory and review platform upload status.",
        "",
        "## Licensing enquiry contacts (specific film ownership unverified)"
    ])
    for partner in contacts:
        lines.append("- "+escape_table(partner["company"])+": "+partner["contact"]+" | "+partner["url"])
    lines.extend(["",
                  "No licensing messages have been sent, and no film rights have been assumed."])
    (out/"source_review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (out/"licensing_email_template.txt").write_text(
        "Subject: Licensing enquiry — short Hindi film-comedy excerpts for YouTube Shorts\n\n"
        "Hello [Licensing Team],\n\n"
        "I manage a new YouTube channel highlighting humorous Hindi film moments. "
        "Could you confirm whether you control digital clip rights for [Film, year]? "
        "We would like to license 15–40 second excerpts for edited vertical YouTube Shorts, "
        "with Hindi subtitles and appropriate attribution. Please share availability, "
        "cost, permitted regions, term, monetization conditions, and any Content ID "
        "clearance requirements. Could you provide authorized source video files "
        "through a licensed delivery link?\n\n"
        "Thank you,\n[Name]\n[YouTube channel]\n",
        encoding="utf-8")
    print("Bollywood source-screening:",len(candidates),
          "research candidates; 0 approved for reposting; output:",out)
    return data

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default=str(DEFAULT_INPUT))
    parser.add_argument("--output",default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-per-movie",type=int,default=3)
    parser.add_argument("--max-total",type=int,default=18)
    args=parser.parse_args()
    discovery=json.loads(Path(args.input).read_text(encoding="utf-8"))
    build(discovery,args.output,max_per_movie=args.max_per_movie,
          max_total=args.max_total)
if __name__=="__main__":
    main()
