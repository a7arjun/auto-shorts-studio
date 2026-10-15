"""Accurate, readable YouTube Shorts metadata for Hindi comedy scenes.

No video metadata proves clip rights. Film/actor tags do NOT imply permission.
Cast/character keywords require supplied, clip-specific verified annotations.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

FILM_INFO=Path("data/bollywood_seo_catalogue.json")
BASE_TAGS=("BollywoodComedy","HindiComedy","ComedyShorts","Shorts")

def hashtag(text):
    """Normalize actor, character, and film names into single-token hashtags."""
    normalized=unicodedata.normalize("NFKC",str(text or ""))
    # Most movie names are English/Hinglish; keep Devanagari characters when supplied.
    compact="".join(c for c in normalized if c.isalnum())
    return "#"+compact if compact else ""

def normalized(text):
    return re.sub(r"[^a-z0-9]+","",str(text).casefold())

def load_catalogue(path=FILM_INFO):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    return {normalized(key):value for key,value in data.items()}

def unique(values):
    found=set()
    out=[]
    for value in values:
        val=str(value).strip()
        key=val.casefold()
        if val and key not in found:
            found.add(key)
            out.append(val)
    return out

def build_metadata(film,year=None,scene_label=None,featured_characters=None,
                   source_credit=None,rights_text=None,catalogue=None,
                   episode_number=None):
    """Generate accurate SEO fields, no unverified actor or character inference.

    featured_characters must be confirmed by the source curator, not merely
    inferred from full-film casting or YouTube search metadata.
    """
    if not str(film or "").strip():
        raise ValueError("film is required")
    movie=str(film).strip()
    data=(catalogue if catalogue is not None else load_catalogue()).get(normalized(movie),{})
    movie=data.get("film",movie)
    movie_year=year if year is not None else data.get("year")
    confirmed=[]
    actor_names=[]
    characters=data.get("characters",{})
    for provided in featured_characters or []:
        key=normalized(provided)
        matched=next(((character,actor) for character,actor in characters.items()
                      if normalized(character)==key),None)
        if matched is None:
            raise ValueError("Unknown or unverified character for film: "+str(provided))
        confirmed.append(matched[0])
        actor_names.append(matched[1])
    confirmed=unique(confirmed)
    actor_names=unique(actor_names)

    hook=" ".join(str(scene_label or "").strip().split())
    if len(hook)>65:
        hook=hook[:62].rsplit(" ",1)[0]
    if not hook:
        hook=(confirmed[0]+"'s Funny Moment" if confirmed else "A Hilarious Comedy Moment")
    # Movie name first is useful for searches; numbering avoids 30 identical titles.
    if episode_number is not None:
        number=int(episode_number)
        if number<1 or number>999:
            raise ValueError("episode_number must be between 1 and 999")
        display_hook=(hook if hook!="A Hilarious Comedy Moment" else "Funny Scene")
        title=f"{movie} | {display_hook} #{number:02d} 😂 #Shorts"
    else:
        title=f"{hook} 😂 | {movie} #Shorts"
    if len(title)>100:
        title=f"{movie} Comedy #{int(episode_number):02d} 😂 #Shorts" if episode_number else f"{movie} Comedy Scene 😂 #Shorts"
        title=title[:100]

    hashes=[hashtag(movie),"#BollywoodComedy"]
    for character,actor in zip(confirmed,actor_names):
        hashes.extend([hashtag(character),hashtag(actor)])
    hashes+=["#HindiComedy","#ComedyShorts","#Shorts"]
    hashtags=unique(h for h in hashes if h)
    hashtags=hashtags[:6]  # Short, relevant hashtags rather than broad stuffing
    cast_line=(", ".join(confirmed)+" ("+", ".join(actor_names)+")") if confirmed else ""
    lead=f"Funny Hindi comedy moment from {movie}"
    if movie_year:
        lead+=f" ({movie_year})"
    if cast_line:
        lead+=f", featuring {cast_line}"
    lead+="."
    description=lead+"\n"
    if episode_number is not None:
        description+=f"Episode {int(episode_number):02d} in our {movie} comedy scene series.\n"
    if hook and hook not in ("A Hilarious Comedy Moment",):
        description+=f"\nScene: {hook}.\n"
    if source_credit:
        description+=f"\nFootage source: {str(source_credit).strip()[:400]}\n"
    if rights_text:
        description+=f"Reuse permission/reference: {str(rights_text).strip()[:350]}\n"
    description+="\n"+" ".join(hashtags)
    description=description[:5000]
    backend_tags=unique(
        [movie,f"{movie} comedy",f"{movie} funny scene",f"{movie} Hindi movie",
         f"{movie} {movie_year}" if movie_year else movie,
         "Bollywood comedy","Hindi comedy","funny movie scene","YouTube Shorts"]
        +confirmed+actor_names)
    # YouTube's separate tags field is minor metadata; keep it compact.
    backend_tags=backend_tags[:15]
    return {"title":title,"description":description,"tags":backend_tags,
            "hashtags":hashtags,"film":movie,"verified_characters":confirmed,
            "verified_actors":actor_names}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--film",required=True)
    parser.add_argument("--scene",default="")
    parser.add_argument("--characters",default="",help="Comma-separated, manually verified clip participants")
    parser.add_argument("--output",default="output/seo/metadata_preview.json")
    args=parser.parse_args()
    result=build_metadata(args.film,scene_label=args.scene,
                          featured_characters=[a.strip() for a in args.characters.split(",") if a.strip()])
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Title:",result["title"])
    print("Hashtags:"," ".join(result["hashtags"]))
    print("Preview:",dest)
if __name__=="__main__":
    main()
