import unittest
from shorts.seo import build_metadata,hashtag

class SEOTests(unittest.TestCase):
    def test_baburao_and_actor(self):
        m=build_metadata("Hera Pheri",scene_label="Baburao's Funniest Moment",
            featured_characters=["Baburao"])
        self.assertIn("#HeraPheri",m["description"])
        self.assertIn("#PareshRawal",m["description"])
        self.assertNotIn("#AkshayKumar",m["description"])
        self.assertIn("Paresh Rawal",m["tags"])
    def test_unknown_actor_not_inferred(self):
        m=build_metadata("Hera Pheri")
        self.assertNotIn("#AkshayKumar",m["description"])
        self.assertNotIn("#PareshRawal",m["description"])
    def test_reject_unverified_character(self):
        with self.assertRaises(ValueError):
            build_metadata("Welcome",featured_characters=["Baburao"])
    def test_title_length_and_tag_limits(self):
        m=build_metadata("Golmaal: Fun Unlimited",scene_label="Very funny "*20)
        self.assertLessEqual(len(m["title"]),100)
        self.assertLessEqual(len(m["hashtags"]),9)
    def test_episode_series_metadata(self):
        a=build_metadata("Hera Pheri",year=2000,scene_label="Funny Scene",episode_number=2)
        b=build_metadata("Hera Pheri",year=2000,scene_label="Funny Scene",episode_number=3)
        self.assertIn("Hera Pheri | Funny Scene #02",a["title"])
        self.assertNotEqual(a["title"],b["title"])
        self.assertIn("Episode 02",a["description"])
        self.assertLessEqual(len(a["hashtags"]),6)
        self.assertNotIn("#PareshRawal",a["description"])

    def test_hashtag(self):
        self.assertEqual(hashtag("Akshay Kumar"),"#AkshayKumar")
        self.assertEqual(hashtag("Bollywood Comedy"),"#BollywoodComedy")

if __name__=="__main__":
    unittest.main()
