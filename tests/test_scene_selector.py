import unittest
from shorts.scene_selector import select_scenes, validate_segments, overlap_fraction

class SceneSelectorTests(unittest.TestCase):
    def setUp(self):
        self.transcript=[
            {"start":0,"end":6,"text":"I bought blue curtains."},
            {"start":6,"end":12,"text":"The office is too quiet."},
            {"start":12,"end":18,"text":"Why is the printer on your head?"},
            {"start":18,"end":23,"text":"Wait! The boss said make an impression!"},
            {"start":23,"end":29,"text":"Are you joking?"},
            {"start":29,"end":35,"text":"I thought it was a new hat!"}
        ]
    def test_returns_ranked_windows(self):
        rows=select_scenes(self.transcript,count=2)
        self.assertTrue(rows)
        self.assertGreaterEqual(rows[0]["duration"],15)
        self.assertLessEqual(rows[0]["duration"],40)
        self.assertTrue(all(rows[i]["score"]>=rows[i+1]["score"] for i in range(len(rows)-1)))
    def test_dedupe(self):
        rows=select_scenes(self.transcript,count=5)
        for i in range(len(rows)):
            for j in range(i):
                self.assertLess(overlap_fraction(rows[i],rows[j]),0.55)
    def test_invalid_transcript(self):
        with self.assertRaises(ValueError):
            validate_segments([{"start":5,"end":4,"text":"oops"}])
    def test_too_short(self):
        self.assertEqual(select_scenes([{"start":0,"end":1,"text":"A"},{"start":1,"end":2,"text":"B"}]),[])
    def test_hindi_text(self):
        dialogue=[
            {"start":0,"end":8,"text":"भाई, ये क्या कर रहे हो?"},
            {"start":8,"end":17,"text":"अरे! मैं कुछ नहीं कर रहा!"},
            {"start":17,"end":26,"text":"लेकिन कुर्सी पर बैग क्यों है?"}
        ]
        self.assertTrue(select_scenes(dialogue))
if __name__=="__main__":
    unittest.main()
