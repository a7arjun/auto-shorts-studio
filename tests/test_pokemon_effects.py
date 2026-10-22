import copy
import json
from pathlib import Path
import subprocess
import unittest
from PIL import Image
from shorts.pokemon_effects import TYPE_COLORS,paint_attack,timing
from shorts.pokemon_quality import assess_battle,require_battle,require_story,BattleRejected
from shorts.pokemon_story import make_story

class EffectsTests(unittest.TestCase):
    def test_all_types_draw_distinct_effects_and_both_directions(self):
        base=Image.new('RGB',(720,1280),'#0a101e');seen=set()
        for kind in TYPE_COLORS:
            event={'move_type':kind,'move':'Test','miss':False,'immune':False}
            result=paint_attack(base,event,.5,(213,755),(507,755))
            self.assertNotEqual(result.tobytes(),base.tobytes())
            seen.add(result.tobytes())
            paint_attack(base,event,.5,(507,755),(213,755))
        self.assertEqual(len(seen),18)

    def test_damage_follows_effect_timing_and_miss_has_no_impact(self):
        seg={'duration':8,'event':{'move':'Thunderbolt'},'speech_parts':[{'start':1.0,'text':'Thunderbolt'}]}
        phase,mix=timing(seg,1.0)
        self.assertEqual((phase,mix),(0,0))
        self.assertEqual(timing(seg,3)[1],1)
        base=Image.new('RGB',(720,1280),'#0a101e')
        event={'move_type':'Electric','move':'Thunderbolt','miss':True,'immune':False}
        image=paint_attack(base,event,.9,(213,755),(507,755))
        self.assertEqual(image.tobytes(),base.tobytes())

    def test_unanimous_and_one_hit_examples_are_rejected_without_altering_results(self):
        battle=json.loads(subprocess.check_output(['node','pokemon/simulate.cjs','Charizard','Pikachu','quality-check','100']))
        before=copy.deepcopy(battle['wins'])
        self.assertFalse(assess_battle(battle)['eligible'])
        with self.assertRaises(BattleRejected):require_battle(battle)
        self.assertEqual(battle['wins'],before)

    def test_accepted_story_shows_two_successful_moves_from_the_winner(self):
        battle=json.loads(subprocess.check_output(['node','pokemon/simulate.cjs','Charizard','Sylveon','quality-v2-screen','100','single-build-v1']))
        require_battle(battle)
        story=make_story(battle,'Test')
        require_story(story,battle)
        self.assertTrue(any('Life Orb recoil' in s['text'] for s in story['segments']))
        self.assertIn('Sylveon wins this example.',story['segments'][-1]['text'])
        for segment in story['segments']:
            if segment.get('event'):
                self.assertIn(segment['event']['move_type'],TYPE_COLORS)
