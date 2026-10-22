import copy
import json
from pathlib import Path
import subprocess
import unittest
from shorts.pokemon_main import choose_pair
from shorts.pokemon_publish import can_start
from shorts.pokemon_story import hp_value, make_story, battle_events


class PokemonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(Path('data/pokemon_channel.json').read_text())
        cls.battle=json.loads(subprocess.check_output(['node','pokemon/simulate.cjs','Charizard','Blastoise','test-story','10']))

    def test_script_damage_matches_exact_hp(self):
        events=battle_events(self.battle)
        self.assertTrue(events)
        for event in events:
            self.assertTrue(all(0<=hp<=1 for hp in event['after']))
        story=make_story(self.battle,'Test Lab')
        for segment in story['segments']:
            if segment['kind']=='attack' and not segment['event']['miss']:
                e=segment['event'];target=1-e['actor']
                self.assertNotIn('percent',segment['text'])
                self.assertNotIn('maximum health',segment['text'])
        self.assertEqual([s['event']['sequence'] for s in story['segments'] if s.get('event')],list(range(len(events))))
        self.assertEqual(story['language'],'en')
        self.assertLessEqual(len(story['title']),100)
        self.assertIn('not a canonical anime result',story['description'])

    def test_hp_faint_and_status(self):
        self.assertEqual(hp_value('0 fnt'),0)
        self.assertAlmostEqual(hp_value('50/200 par'),.25)

    def test_no_repeat_or_same_species(self):
        state={'jobs':[]};date='2026-10-22'
        pair=choose_pair(state,date)
        self.assertNotEqual(*pair)
        state['jobs'].append({'pair':list(reversed(pair))})
        self.assertNotEqual(set(pair),set(choose_pair(state,date)))

    def test_public_requires_both_pilot_and_launch_config(self):
        state={'jobs':[],'pilot_verified':False}
        config={**self.config,'publication_enabled':False}
        self.assertFalse(can_start(state,config,'2026-10-22','daily'))
        state['pilot_verified']=True
        self.assertFalse(can_start(state,config,'2026-10-22','daily'))
        config['publication_enabled']=True
        self.assertTrue(can_start(state,config,'2026-10-22','daily'))

    def test_uncertain_upload_never_restarts(self):
        state={'jobs':[{'status':'uploading'}],'pilot_verified':True}
        with self.assertRaisesRegex(RuntimeError,'duplicate'):
            can_start(state,self.config,'2026-10-22','pilot')

    def test_daily_and_monthly_limits(self):
        config={**self.config,'publication_enabled':True}
        state={'pilot_verified':True,'jobs':[{'mode':'daily','status':'published','date':'2026-10-22'}]}
        self.assertTrue(can_start(state,config,'2026-10-22','daily'))
        state['jobs']*=2
        self.assertFalse(can_start(state,config,'2026-10-22','daily'))
        state['jobs']=[{'mode':'daily','status':'published','date':'2026-10-01'} for _ in range(62)]
        self.assertFalse(can_start(state,config,'2026-10-22','daily'))
        self.assertTrue(can_start(state,config,'2026-11-01','daily'))


if __name__=='__main__':
    unittest.main()
