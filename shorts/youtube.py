"""YouTube upload using one-time OAuth setup and stored GitHub Actions secrets."""
import os
import time

def upload(channel,video,metadata):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    prefix="YT_HI" if channel=="hindi" else "YT_EN"
    values=[os.getenv(prefix+"_"+x) for x in ("CLIENT_ID","CLIENT_SECRET","REFRESH_TOKEN")]
    if not all(values):raise RuntimeError("Missing YouTube OAuth configuration for "+channel)
    credentials=Credentials(None,refresh_token=values[2],token_uri="https://oauth2.googleapis.com/token",
       client_id=values[0],client_secret=values[1],scopes=["https://www.googleapis.com/auth/youtube.upload"])
    credentials.refresh(Request())
    youtube=build("youtube","v3",credentials=credentials,cache_discovery=False)
    body={"snippet":{"title":metadata["title"],"description":metadata["description"],
          "categoryId":"23"},"status":{"privacyStatus":os.getenv("YT_PRIVACY_STATUS","private"),
          "selfDeclaredMadeForKids":False}}
    request=youtube.videos().insert(part="snippet,status",body=body,
       media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True,chunksize=4*1024*1024))
    for attempt in range(8):
        try:
            result=None
            while result is None:_,result=request.next_chunk()
            if not result.get("id"):raise RuntimeError("Missing YouTube video id")
            return "https://www.youtube.com/watch?v="+result["id"]
        except (HttpError,OSError) as exc:
            status=getattr(getattr(exc,"resp",None),"status",None)
            if status is not None and int(status) not in (429,500,502,503,504):raise
            if attempt==7:raise
            time.sleep(min(2**attempt,45))
