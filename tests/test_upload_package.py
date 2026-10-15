import json
import tempfile
import unittest
from pathlib import Path
from shorts.modern_factory import prepare_upload_metadata,write_upload_package,eligible_source

class UploadPackageTests(unittest.TestCase):
    def test_empty_approved_source_catalogue(self):
        source,_=eligible_source()
        self.assertIsNone(source)
    def test_unapproved_source_cannot_generate_metadata(self):
        item={"channel":"hindi","enabled":True,"license_type":"licensed",
              "usage_authorized":False,"rights_reference":"ref",
              "source_id":"example","title":"Hera Pheri","film":"Hera Pheri",
              "media_url":"https://cdn.example.org/film.mp4"}
        with self.assertRaises(ValueError):
            prepare_upload_metadata(item)
    def test_verified_character_keywords(self):
        entry={"channel":"hindi","enabled":True,"license_type":"licensed",
               "usage_authorized":True,"rights_reference":"license-document-1",
               "source_id":"example","title":"Hera Pheri","film":"Hera Pheri",
               "verified_featured_characters":["Baburao"],
               "media_url":"https://cdn.example.org/film.mp4"}
        metadata=prepare_upload_metadata(entry)
        self.assertIn("#PareshRawal",metadata["description"])
        self.assertNotIn("#AkshayKumar",metadata["description"])
        self.assertIn("Hera Pheri",metadata["title"])
    def test_no_unverified_actor(self):
        entry={"channel":"hindi","enabled":True,"license_type":"owned",
               "usage_authorized":True,"rights_reference":"reference",
               "source_id":"other","title":"Dhamaal","film":"Dhamaal",
               "media_url":"https://cdn.example.org/film.mp4"}
        self.assertNotIn("#SanjayDutt",prepare_upload_metadata(entry)["description"])
if __name__=="__main__":
    unittest.main()
