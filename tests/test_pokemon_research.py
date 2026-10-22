from datetime import datetime, timezone
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import MagicMock
from shorts.pokemon_research import (cutoff_time,evidence,select_researched_pair,
                                     apply_metadata,ResearchUnavailable)
from shorts.pokemon_story import make_story

NOW=datetime(2026,10,22,4,tzinfo=timezone.utc)


def video(ident='abcdefghijk',date='2026-10-01T00:00:00Z',title='Charizard vs Blastoise: Who Wins?',channel='other',views='10000'):
    return {'id':ident,'snippet':{'title':title,'description':'#Charizard #Blastoise #Viral #Anime',
            'publishedAt':date,'channelId':channel,'defaultAudioLanguage':'en'},
            'statistics':{'viewCount':views,'likeCount':'100','commentCount':'10'}}


class ResearchTests(unittest.TestCase):
    def test_four_calendar_month_cutoff_and_end_of_month(self):
        self.assertEqual(cutoff_time(NOW).isoformat(),'2026-06-22T04:00:00+00:00')
        self.assertEqual(cutoff_time(datetime(2026,6,30,tzinfo=timezone.utc)).day,28)

    def test_reject_old_future_nonenglish_wrong_format_and_own_channel(self):
        items=[video(),video('oldoldold00','2026-06-21T00:00:00Z'),
               video('future00000','2026-10-23T00:00:00Z'),
               video('wrongform00',title='Mega Charizard vs Blastoise'),
               video('ownownown00',channel='mine'),video('unrelated00',title='Charizard card pack opening')]
        nonenglish=video('hindi000000');nonenglish['snippet']['defaultAudioLanguage']='hi';items.append(nonenglish)
        self.assertEqual([r['id'] for r in evidence(items,NOW,'mine')],['abcdefghijk'])

    def test_velocity_is_average_and_deduplicated(self):
        rows=evidence([video(),video()],NOW,'mine')
        self.assertEqual(len(rows),1)
        self.assertGreater(rows[0]['average_views_per_day'],450)
        self.assertIn('youtube.com/watch?v=',rows[0]['url'])

    def client(self,items):
        youtube=MagicMock()
        youtube.search().list().execute.return_value={'items':[{'id':{'videoId':i['id']}} for i in items]}
        youtube.videos().list().execute.return_value={'items':items}
        return youtube

    def test_selection_uses_recent_unused_matchup_and_exact_query(self):
        youtube=self.client([video()])
        builds=[{'species':n} for n in ('Charizard','Blastoise','Pikachu')]
        pair,research=select_researched_pair(youtube,builds,{'jobs':[]},'slot','mine',now=NOW)
        self.assertEqual(pair,('Charizard','Blastoise'))
        self.assertEqual(research['search_calls'],9)
        calls=youtube.search().list.call_args_list
        self.assertTrue(any(c.kwargs.get('q')=='Pokemon Charizard vs Blastoise battle' for c in calls))
        for call in calls:
            if call.kwargs:
                self.assertEqual(call.kwargs['publishedAfter'],'2026-06-22T04:00:00Z')
        pair2,_=select_researched_pair(youtube,builds,{'jobs':[]},'slot','mine',fixed_pair=pair,now=NOW)
        self.assertEqual(pair2,pair)
        with self.assertRaises(ResearchUnavailable):
            select_researched_pair(youtube,builds,{'jobs':[{'pair':list(pair)}]},'slot','mine',now=NOW)

    def test_empty_or_failed_research_never_fabricates_a_trend(self):
        builds=[{'species':'Charizard'},{'species':'Blastoise'}]
        with self.assertRaises(ResearchUnavailable):
            select_researched_pair(self.client([]),builds,{'jobs':[]},'slot',now=NOW)
        client=self.client([])
        client.search().list().execute.side_effect=RuntimeError('secret-url?key=hidden')
        with self.assertRaisesRegex(ResearchUnavailable,'research failed') as error:
            select_researched_pair(client,builds,{'jobs':[]},'slot',now=NOW)
        self.assertNotIn('hidden',str(error.exception))

    def test_metadata_remains_grounded_and_rejects_irrelevant_hashtags(self):
        battle=json.loads(subprocess.check_output(['node','pokemon/simulate.cjs','Charizard','Blastoise','research-test','10']))
        research={'status':'researched','checked_at':NOW.isoformat(),'pair':['Charizard','Blastoise'],
                  'references':evidence([video()],NOW,'mine')}
        story=make_story(battle,'Test');segments=copy.deepcopy(story['segments'][1:])
        apply_metadata(story,battle,research)
        self.assertIn('Who Wins',story['title'])
        self.assertLessEqual(len(story['title']),100)
        self.assertEqual(story['segments'][1:],segments)
        self.assertIn('Game battle, then anime verdict.',story['segments'][0]['text'])
        self.assertNotIn('#Viral',story['description'])
        self.assertNotIn('#Anime',story['description'])
        self.assertEqual(set(story['hashtags']),{'#Pokemon','#PokemonBattle','#Charizard','#Blastoise','#Shorts'})
        self.assertIn('not a canonical anime result',story['description'])
        self.assertNotEqual(story['title'],research['references'][0]['title'])
        with self.assertRaises(ResearchUnavailable):
            apply_metadata(story,battle,{**research,'pair':['Pikachu','Raichu']})


if __name__=='__main__':
    unittest.main()
