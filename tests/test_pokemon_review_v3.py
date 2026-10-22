import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from shorts.pokemon_story import make_story,battle_events
from shorts.pokemon_quality import require_story,BattleRejected
from shorts.pokemon_anime import assessment,add_assessment


class ReviewV3Tests(unittest.TestCase):
    def test_exact_skipped_garchomp_attack_is_now_shown_in_order(self):
        battle=json.loads(subprocess.check_output(['node','pokemon/simulate.cjs','Charizard','Garchomp',
                  '2026-10-23T22:00+05:30-r2','100','single-build-v1']))
        story=make_story(battle,'Test');require_story(story,battle)
        events=[s['event'] for s in story['segments'] if s.get('event')]
        self.assertEqual([e['move'] for e in events],['Stone Edge','Dragon Pulse','Dragon Claw','Dragon Pulse'])
        self.assertEqual(events,battle_events(battle))
        self.assertFalse(any('percent' in s['text'] or 'maximum health' in s['text'] for s in story['segments']))
        broken=copy.deepcopy(story);broken['segments'].pop(3)
        with self.assertRaises(BattleRejected):require_story(broken,battle)

    def test_named_anime_evidence_never_changes_measured_game_results(self):
        battle=json.loads(subprocess.check_output(['node','pokemon/simulate.cjs','Charizard','Tyranitar','review','100']))
        before=copy.deepcopy(battle);story=make_story(battle,'Test')
        result=add_assessment(story,battle)
        self.assertEqual(battle,before)
        self.assertEqual([p['trainer'] for p in result['profiles']],['Ash','Alain'])
        self.assertEqual(result['confidence'],'low')
        self.assertNotIn('probability',result)
        self.assertTrue(all(p['sources'] for p in result['profiles']))
        self.assertEqual(assessment(['Pikachu','Blastoise'])['status'],'unresolved')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_real_encoder_retimes_audio_and_video_together_at_1_5(self):
        from shorts.pokemon_render import render
        with tempfile.TemporaryDirectory() as folder:
            audio=Path(folder)/'voice.wav';output=Path(folder)/'short.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=24000:duration=30',str(audio)],check=True)
            story={'duration':30,'playback_speed':1.5,'segments':[{'start':0,'event':{'move':'Test'}}]}
            seen=[]
            def dummy(b,s,m):
                seen.append(m);return Image.new('RGB',(72,128),'black')
            with patch('shorts.pokemon_render.W',72),patch('shorts.pokemon_render.H',128),patch('shorts.pokemon_render.FPS',12),patch('shorts.pokemon_render.frame',dummy):
                quality=render({},story,audio,output)
            self.assertAlmostEqual(quality['duration'],20,delta=.2)
            self.assertGreater(max(seen),29)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))
            durations=[float(s['duration']) for s in probe['streams']]
            self.assertLess(max(durations)-min(durations),.15)
