import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from shorts import discovery

class TestModernDiscovery(unittest.TestCase):
    def test_all_movies_2000_plus(self):
        self.assertTrue(all(m['year']>=2000 for group in discovery.load_movies().values() for m in group))
    def test_rotating_is_deterministic(self):
        items=discovery.load_movies()['bollywood']
        a=discovery.daily_picks(items,'bollywood','2026-10-15')
        b=discovery.daily_picks(items,'bollywood','2026-10-15')
        self.assertEqual(a,b)
        self.assertEqual(len(a),2)
    def test_query_film_release_year_not_upload_date(self):
        item=discovery.load_movies()['bollywood'][0]
        self.assertIn('2000',discovery.movie_query(item))
        self.assertIn('search_query=',discovery.search_link(discovery.movie_query(item)))
    def test_without_key_does_not_claim_rights_or_views(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ',{'YOUTUBE_DATA_API_KEY':''}):
            result=discovery.run(date='2026-10-15',out=Path(folder))
            self.assertEqual(result['mode'],'offline_search_queries')
            self.assertEqual(len(result['rows']),4)
            self.assertTrue(all(r['upload_eligible'] is False for r in result['rows']))
            self.assertTrue(all('views' not in r for r in result['rows']))
            self.assertTrue((Path(folder)/'modern_movies.csv').exists())
    def test_api_results_not_assumed_licensed(self):
        sample={'movie':'Welcome','year':2007,'language':'hi','region':'IN'}
        search={'items':[{'id':{'videoId':'example-id'},'snippet':{}}]}
        details={'items':[{'id':'example-id','snippet':{'title':'Test','publishedAt':'2026-10-01T00:00:00Z'},'statistics':{'viewCount':'1000'},'status':{'license':'creativeCommon'}}]}
        with patch.object(discovery,'request_json',side_effect=[search,details]):
            items=discovery.get_candidates(sample,'bollywood','fakekey')
        self.assertEqual(len(items),1)
        self.assertFalse(items[0]['upload_eligible'])
        self.assertFalse(items[0]['rights_verified'])
        self.assertEqual(items[0]['youtube_declared_license'],'creativeCommon')
if __name__=='__main__':unittest.main()
