"""Rights-tag-checked Wikimedia Commons video downloader."""
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse
import requests

API="https://commons.wikimedia.org/w/api.php"
HEADERS={"User-Agent":"AutoShortsStudio/0.3 (personal creative project; https://github.com/a7arjun/auto-shorts-studio)"}
MAX_BYTES=int(os.getenv("CLIP_SOURCE_MAX_MB","300"))*1024*1024

class MediaSourceError(RuntimeError): pass

def valid_url(url):
    p=urlparse(url)
    return p.scheme=="https" and p.hostname in {"upload.wikimedia.org","commons.wikimedia.org"}

def candidate_transcodes(info):
    options=[]
    for item in info.get("derivatives",[]):
        url=item.get("src") or item.get("url","")
        width=int(item.get("width") or 0)
        size=int(item.get("size") or 0)
        if valid_url(url) and 200<=width<=700 and (not size or size<=MAX_BYTES):
            options.append((abs(width-480),size,url))
    options.sort()
    if options: return [t[2] for t in options]
    original=info.get("url","")
    if valid_url(original) and 0<int(info.get("size") or 0)<=MAX_BYTES: return [original]
    return []

def resolve_commons(source):
    if not source.get("enabled") or not source.get("required_categories"):
        raise MediaSourceError("Source not approved in local catalogue")
    params={"action":"query","format":"json","formatversion":2,"prop":"videoinfo|categories",
            "titles":"File:"+source["file"],"viprop":"url|size|derivatives|extmetadata","cllimit":"max"}
    response=requests.get(API,headers=HEADERS,params=params,timeout=40)
    response.raise_for_status()
    pages=response.json().get("query",{}).get("pages",[])
    if not pages or pages[0].get("missing") or not pages[0].get("videoinfo"):
        raise MediaSourceError("Video unavailable on Wikimedia Commons")
    page=pages[0]
    categories={c["title"].removeprefix("Category:") for c in page.get("categories",[])}
    if any("copyrighted in the u.s." in x.lower() for x in categories):
        raise MediaSourceError("Copyright warning found")
    required=set(source["required_categories"])
    if not required.issubset(categories):
        raise MediaSourceError("Required rights categories missing: "+", ".join(sorted(required-categories)))
    info=page["videoinfo"][0]
    meta=info.get("extmetadata",{})
    if str(meta.get("Copyrighted",{}).get("value","")).lower()=="true":
        raise MediaSourceError("Copyright flag present")
    urls=candidate_transcodes(info)
    if not urls: raise MediaSourceError("No suitably sized Commons transcode")
    return {"urls":urls,"page":source["source_page"],"categories":sorted(categories)}

def download_commons(source,dest_root):
    resolved=resolve_commons(source)
    folder=Path(dest_root);folder.mkdir(parents=True,exist_ok=True)
    url=resolved["urls"][0]
    ext=".mp4" if ".mp4" in urlparse(url).path.lower() else ".webm" if ".webm" in urlparse(url).path.lower() else ".ogv"
    output=folder/(source["id"]+"-"+hashlib.sha256(url.encode()).hexdigest()[:12]+ext)
    if output.exists() and output.stat().st_size>10000:return output,resolved
    part=Path(str(output)+".partial")
    try:
        count=0
        with requests.get(url,headers=HEADERS,stream=True,timeout=(20,120)) as response:
            response.raise_for_status()
            if int(response.headers.get("content-length") or 0)>MAX_BYTES:
                raise MediaSourceError("Remote file too large")
            with part.open("wb") as f:
                for chunk in response.iter_content(524288):
                    if chunk:
                        count+=len(chunk)
                        if count>MAX_BYTES:raise MediaSourceError("Exceeded download cap")
                        f.write(chunk)
        if count<10000:raise MediaSourceError("Downloaded file too small")
        part.replace(output)
        return output,resolved
    except Exception:
        part.unlink(missing_ok=True)
        raise
