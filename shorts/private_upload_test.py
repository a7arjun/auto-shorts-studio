"""Upload an original synthetic integration-test video as PRIVATE (never copyrighted clips)."""
import argparse
import os
from pathlib import Path
from shorts.movie_clips import make_demo_source, render_clip

def private_test(channel="hindi"):
    if channel!="hindi":
        raise ValueError("The first integration test is Bollywood/Hindi channel only.")
    if os.getenv("YT_PRIVACY_STATUS","private")!="private":
        raise RuntimeError("Integration test must stay private")
    if os.getenv("CONFIRM_PRIVATE_UPLOAD")!="true":
        raise RuntimeError("Confirm one-time private test upload in workflow_dispatch")
    root=Path("output/private-upload-test")
    demo=make_demo_source(root/"original-test-pattern.mp4")
    video=render_clip(demo,root/"test_bollywood_connection.mp4",0,8,keep_audio=False)
    meta={
      "title":"Auto Shorts Studio - Private Connection Test",
      "description":"Original synthetic test pattern. This is a private technical upload to verify OAuth from GitHub Actions, not a movie clip.",
    }
    from shorts.youtube import upload
    url=upload(channel,video,meta)
    print("PRIVATE INTEGRATION UPLOAD:",url)
    print("Please verify it appears in the intended channel at https://studio.youtube.com/")
    return url

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--channel",choices=["hindi"],default="hindi")
    args=parser.parse_args()
    private_test(args.channel)
