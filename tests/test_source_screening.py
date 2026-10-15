import json
import tempfile
import unittest
from pathlib import Path
from shorts.source_screening import select_candidates, build

class ScreenMovieSourcesTests(unittest.TestCase):
    def setUp(self):
        self.discovery={"date":"2026-10-15","mode":"live_youtube_metadata","rows":[
            {"channel":"bollywood","movie":"Hera Pheri","movie_year":2000,"video_id":"abc1234xyZA",
             "title":"Hera Pheri (2000) funny scene","uploader":"Uploader unknown","views":1234,"likes":12,
             "score":100,"youtube_declared_license":"creativeCommon"},
            {"channel":"bollywood","movie":"Hera Pheri","movie_year":2000,"video_id":"abc1234xyZA","score":10},
            {"channel":"hollywood","movie":"The Hangover","video_id":"def5678xyZA","score":2000},
            {"channel":"bollywood","movie":"Welcome","movie_year":2007,"video_id":"xyz0123xyZA","title":"Welcome (2007) funny scene","score":55}
        ]}
    def test_only_bollywood_and_deduplicated(self):
        rows=select_candidates(self.discovery)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["movie"],"Hera Pheri")
    def test_license_never_inferred_from_youtube_license(self):
        item=select_candidates(self.discovery)[0]
        self.assertEqual(item["declared_license"],"creativeCommon")
        self.assertFalse(item["rights_owner_confirmed"])
        self.assertEqual(item["license_status"],"not_verified")
        self.assertFalse(item["automated_repost_eligible"])
    def test_remix_never_claimed_available(self):
        rows=select_candidates(self.discovery)
        self.assertTrue(all(r["remix_eligibility"]=="unknown_check_in_youtube_app" for r in rows))
    def test_limits(self):
        self.assertEqual(len(select_candidates(self.discovery,max_total=1)),1)
        with self.assertRaises(ValueError):
            select_candidates(self.discovery,max_total=0)
    def test_exports(self):
        with tempfile.TemporaryDirectory() as d:
            report=build(self.discovery,Path(d)/"out")
            self.assertEqual(len(report["candidates"]),2)
            for path in ["source_review.md","bollywood_source_queue.csv",
                         "bollywood_source_queue.json","licensing_email_template.txt"]:
                self.assertTrue((Path(d)/"out"/path).exists())
            self.assertIn("None of these entries is approved",
                          (Path(d)/"out"/"source_review.md").read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
