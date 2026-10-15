import json
import tempfile
import unittest
from pathlib import Path
from shorts.modern_factory import validate_source, write_srt, eligible_source

class ModernFactoryTest(unittest.TestCase):
    def test_blank_catalogue_never_publishes(self):
        item,state=eligible_source()
        self.assertIsNone(item)
    def test_reject_unlicensed_youtube_file(self):
        entry={"channel":"hindi","enabled":True,"license_type":"licensed",
               "usage_authorized":True,"rights_reference":"agreement",
               "title":"Test","source_id":"a","media_url":"https://www.youtube.com/watch?v=a"}
        with self.assertRaises(ValueError):validate_source(entry)
    def test_requires_usage_auth(self):
        entry={"channel":"hindi","enabled":True,"license_type":"licensed",
               "usage_authorized":False,"rights_reference":"agreement",
               "title":"Test","source_id":"a","media_url":"https://example.com/video.mp4"}
        with self.assertRaises(ValueError):validate_source(entry)
    def test_caption_timing(self):
        with tempfile.TemporaryDirectory() as d:
            path=write_srt([{"start":10,"end":13,"text":"क्या हाल है?"},
                            {"start":13,"end":18,"text":"अरे वाह!"}],10,18,Path(d)/"caption.srt")
            value=path.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:03,000",value)
            self.assertIn("क्या हाल है?",value)
if __name__=="__main__":
    unittest.main()
