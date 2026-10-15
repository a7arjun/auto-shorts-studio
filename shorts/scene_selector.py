"""Automatic, *heuristic* dialogue-window ranking.

This is a testable foundation, NOT trained humor understanding. It accepts
timestamped dialogue from authorized source footage (e.g. local Whisper output).
YouTube Data API metadata alone cannot supply the transcript or footage.
"""
import argparse
import json
import re
from pathlib import Path

HUMOR_MARKERS=(
    "wait", "what", "seriously", "really", "no way", "are you joking",
    "why", "how", "but", "actually", "surprise", "idiot",
    "क्या", "क्यों", "अरे", "लेकिन", "पागल", "मज़ाक", "सच", "भाई",
    "[laugh", "(laugh", "[laughter", "हँस",
)

def validate_segments(segments):
    if not isinstance(segments,list) or not segments:
        raise ValueError("Expected nonempty segment list")
    previous=-1.0
    cleaned=[]
    for segment in segments:
        start=float(segment["start"])
        end=float(segment["end"])
        text=str(segment["text"]).strip()
        if start<0 or end<=start or start<previous:
            raise ValueError("Transcript times must be ordered and positive")
        if not text:
            raise ValueError("Transcript segment text must not be empty")
        previous=start
        cleaned.append({"start":start,"end":end,"text":text})
    return cleaned

def score_window(window, min_seconds=15, max_seconds=40):
    start=window[0]["start"]
    end=window[-1]["end"]
    duration=end-start
    if duration<min_seconds or duration>max_seconds:
        return None
    joined=" ".join(seg["text"] for seg in window)
    lines=[seg["text"].lower() for seg in window]
    humor=sum(any(marker in text for marker in HUMOR_MARKERS) for text in lines)
    question=sum("?" in text or "?" in line for text,line in zip((s["text"] for s in window),lines))
    surprise=sum("!" in text for text in lines)
    exchanges=min(len(lines),6)
    ending=window[-1]["text"]
    final_punch=1 if ("!" in ending or "?" in ending or any(x in ending.lower() for x in HUMOR_MARKERS)) else 0
    first_hook=1 if ("?" in window[0]["text"] or "!" in window[0]["text"]) else 0
    # Down-rank overly talkative or silent windows.
    spoken=sum(len(re.findall(r"\S+",s["text"])) for s in window)
    pace=spoken/max(duration,1)
    pace_penalty=max(0,pace-3.8)*4+max(0,0.35-pace)*7
    duration_penalty=abs(duration-27)*0.24
    score=(min(humor,4)*3.0 + min(question,3)*1.5 + min(surprise,3)*1.5
           + exchanges*1.8 + final_punch*4.5 + first_hook*2.5
           - pace_penalty - duration_penalty)
    return {"start":round(start,2),"end":round(end,2),"duration":round(duration,2),
            "score":round(score,2),"excerpt":joined[:500],"transcript_lines":len(window),
            "signals":{"humor_markers":humor,"questions":question,"surprises":surprise,
                       "final_punch":final_punch,"hook":first_hook}}

def overlap_fraction(a,b):
    shared=max(0,min(a["end"],b["end"])-max(a["start"],b["start"]))
    return shared/max(0.001,min(a["duration"],b["duration"]))

def select_scenes(segments, min_seconds=15, max_seconds=40, count=2):
    if min_seconds<=0 or max_seconds<min_seconds or count<1:
        raise ValueError("Invalid selection settings")
    segs=validate_segments(segments)
    ranked=[]
    for i in range(len(segs)):
        for j in range(i,len(segs)):
            window=segs[i:j+1]
            if window[-1]["end"]-window[0]["start"]>max_seconds:
                break
            if len(window)<2:
                continue
            candidate=score_window(window,min_seconds,max_seconds)
            if candidate is not None:
                ranked.append(candidate)
    ranked.sort(key=lambda x:(-x["score"],x["start"],x["duration"]))
    chosen=[]
    for candidate in ranked:
        if all(overlap_fraction(candidate,prior)<0.55 for prior in chosen):
            chosen.append(candidate)
            if len(chosen)>=count:
                break
    return chosen

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--transcript",required=True,help="JSON list of {start,end,text} or {segments:...}")
    parser.add_argument("--output",default="output/scenes/scene_candidates.json")
    parser.add_argument("--count",type=int,default=2)
    args=parser.parse_args()
    data=json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    segments=data["segments"] if isinstance(data,dict) else data
    results=select_scenes(segments,count=args.count)
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"type":"heuristic_dialogue_candidates",
          "note":"Candidate score is an approximation. Rights to footage are NOT implied.",
          "scenes":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Ranked {len(results)} potential clip(s): {out}")
    for candidate in results:
        print(candidate["start"],candidate["end"],candidate["score"])

if __name__=="__main__":
    main()
