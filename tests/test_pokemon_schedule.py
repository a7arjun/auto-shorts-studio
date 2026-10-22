from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from shorts.pokemon_publish import (publication_slot, require_future_slot, can_start,
                                    schedule_existing)
from shorts.pokemon_main import run


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads(Path('data/pokemon_channel.json').read_text())
        self.config['publication_enabled']=True

    def test_requested_ist_slots_have_correct_utc_times(self):
        for hour,target in ((4,'04:30'),(16,'16:30')):
            slot=publication_slot(self.config,datetime(2026,10,22,hour,tzinfo=timezone.utc))
            self.assertEqual(slot['publish_at'],f'2026-10-22T{target}:00Z')
            self.assertTrue(slot['slot'].endswith(('10:00+05:30','22:00+05:30')))

    def test_early_late_and_between_slots_do_not_catch_up(self):
        for clock in ('03:58','04:26','04:30','05:00','16:26','23:59'):
            self.assertIsNone(publication_slot(self.config,datetime.fromisoformat(f'2026-10-22T{clock}:00+00:00')))
        with self.assertRaisesRegex(RuntimeError,'deadline'):
            require_future_slot('2026-10-22T04:30:00Z',datetime(2026,10,22,4,26,tzinfo=timezone.utc))

    def test_scheduled_video_reserves_slot_but_allows_second_slot(self):
        state={'pilot_verified':True,'jobs':[{'mode':'daily','date':'2026-10-22',
                    'status':'scheduled','slot':'morning'}]}
        self.assertFalse(can_start(state,self.config,'2026-10-22','daily','morning'))
        self.assertTrue(can_start(state,self.config,'2026-10-22','daily','evening'))
        state['jobs'].append({**state['jobs'][0],'slot':'evening'})
        self.assertFalse(can_start(state,self.config,'2026-10-22','daily','third'))

    @patch('shorts.pokemon_publish.require_future_slot')
    @patch('shorts.pokemon_publish.check_processed')
    def test_schedule_sets_private_future_release_and_verifies_it(self,processed,deadline):
        youtube=MagicMock(); stamp='2026-10-22T04:30:00Z'
        processed.return_value={'status':{'privacyStatus':'private'}}
        youtube.videos().list().execute.return_value={'items':[{'snippet':{'channelId':'target'},
                   'status':{'privacyStatus':'private','publishAt':stamp}}]}
        schedule_existing(youtube,'video',self.config,'target',stamp)
        body=youtube.videos().update.call_args.kwargs['body']
        self.assertEqual(body['status']['privacyStatus'],'private')
        self.assertEqual(body['status']['publishAt'],stamp)
        deadline.assert_called_once_with(stamp)

    @patch('shorts.pokemon_publish.require_future_slot',side_effect=RuntimeError('deadline'))
    @patch('shorts.pokemon_publish.check_processed',return_value={'status':{'privacyStatus':'private'}})
    def test_missed_slot_never_calls_public_update(self,processed,deadline):
        youtube=MagicMock()
        with self.assertRaisesRegex(RuntimeError,'deadline'):
            schedule_existing(youtube,'video',self.config,'target','2026-10-22T04:30:00Z')
        youtube.videos().update.assert_not_called()

    @patch('shorts.pokemon_publish.check_processed')
    def test_reconcile_existing_schedule_does_not_update_or_upload(self,processed):
        youtube=MagicMock(); stamp='2026-10-22T04:30:00Z'
        processed.return_value={'status':{'privacyStatus':'private','publishAt':stamp}}
        schedule_existing(youtube,'video',self.config,'target',stamp)
        youtube.videos().update.assert_not_called()
        youtube.videos().insert.assert_not_called()

    def test_two_runs_and_retries_upload_once_per_slot(self):
        state={'pilot_verified':True,'jobs':[]};ledger=MagicMock();ledger.data=state
        slots=[{'slot':f'2026-10-22T{clock}+05:30','date':'2026-10-22',
                'publish_at':f'2099-10-22T{utc}:00Z'} for clock,utc in [('10:00','04:30'),('22:00','16:30')]]
        with (patch('shorts.pokemon_main.Ledger',return_value=ledger),
              patch('shorts.pokemon_main.Path.read_text',return_value=json.dumps(self.config)),
              patch('shorts.pokemon_main.services',return_value=(MagicMock(),MagicMock(),{'can_manage':True,'channel_id':'target'})),
              patch('shorts.pokemon_main.choose_pair',return_value=('Charizard','Blastoise')),
              patch('shorts.pokemon_main.prepare',return_value={}),
              patch('shorts.pokemon_main.require_future_slot'),
              patch('shorts.pokemon_main.upload_private',side_effect=['video1','video2']) as upload,
              patch('shorts.pokemon_main.check_processed'),
              patch('shorts.pokemon_main.schedule_existing'),
              patch('shorts.pokemon_main.Path.write_text'),
              patch('shorts.pokemon_main.publication_slot',side_effect=[slots[0],slots[0],slots[1],slots[1]])):
            for _ in range(4):
                run('daily')
        self.assertEqual(upload.call_count,2)
        self.assertEqual(len(state['jobs']),2)
        self.assertTrue(all(j['status']=='scheduled' for j in state['jobs']))


if __name__=='__main__':
    unittest.main()
