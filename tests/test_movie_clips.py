import json
import unittest
from pathlib import Path
from shorts.movie_clips import select_item,make_metadata
from shorts.commons_media import candidate_transcodes

class TestMovieClips(unittest.TestCase):
    def test_catalogue(self):
        data=json.loads(Path("data/movie_sources.json").read_text(encoding="utf-8"))
        self.assertTrue(data["hindi"] and data["english"])
        for items in data.values():
            self.assertTrue(all(x["source_page"].startswith("https://commons.wikimedia.org/wiki/File:") for x in items))
    def test_rotating_clips(self):
        item,start,duration=select_item("hindi",[],today="2026-10-15")
        other,next_start,_=select_item("hindi",[{"source_id":item["id"],"start_second":start}],today="2026-10-15")
        self.assertNotEqual((item["id"],start),(other["id"],next_start))
        self.assertGreaterEqual(duration,12)
    def test_credits(self):
        item,start,_=select_item("english",[],today="2026-10-15")
        self.assertIn(item["source_page"],make_metadata(item,"english",start)["description"])
    def test_transcode_filter(self):
        payload={"derivatives":[{"src":"https://upload.wikimedia.org/good.webm","width":480,"size":4000000},{"src":"https://evil.org/evil.webm","width":480,"size":1000}]}
        self.assertEqual(candidate_transcodes(payload),["https://upload.wikimedia.org/good.webm"])
if __name__=="__main__":unittest.main()
