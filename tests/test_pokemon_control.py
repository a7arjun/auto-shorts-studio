import unittest
from unittest.mock import MagicMock, patch
from shorts.pokemon_control import short_eligibility,operate
from shorts.pokemon_publish import daily_review_slots,require_review_deadline,can_start,MissedPublicationSlot
from datetime import datetime,timezone

class ControlTests(unittest.TestCase):
    def test_uploaded_file_short_eligibility(self):
        item={'fileDetails':{'durationMs':'54600','videoStreams':[{'widthPixels':720,'heightPixels':1280,'rotation':'none'}]}}
        self.assertEqual(short_eligibility(item)['duration'],54.6)
        item['fileDetails']['videoStreams'][0]['widthPixels']=1920
        with self.assertRaises(RuntimeError):short_eligibility(item)
        with self.assertRaises(RuntimeError):short_eligibility({})

    def test_morning_batch_prepares_both_slots_and_late_run_skips(self):
        c={'review_time_ist':'09:30','review_preparation_minutes':60,'publish_times_ist':['10:00','22:00'],'review_before_publish':True}
        slots=daily_review_slots(c,datetime(2026,10,23,3,tzinfo=timezone.utc))
        self.assertEqual([s['publish_at'] for s in slots],['2026-10-23T04:30:00Z','2026-10-23T16:30:00Z'])
        self.assertEqual(daily_review_slots(c,datetime(2026,10,23,4,tzinfo=timezone.utc)),[])
        with self.assertRaises(MissedPublicationSlot):
            require_review_deadline(c,slots[1]['publish_at'],datetime(2026,10,23,4,tzinfo=timezone.utc))
        require_review_deadline(c,slots[1]['publish_at'],datetime(2026,10,23,3,59,tzinfo=timezone.utc))

    def test_public_pilot_cannot_be_uploaded_again(self):
        self.assertFalse(can_start({'pilot_verified':True,'jobs':[{'mode':'pilot','status':'published'}]}, {},'2026-10-23','pilot'))

    @patch('shorts.pokemon_control.verify_public')
    @patch('shorts.pokemon_control.check_processed',return_value={'status':{'privacyStatus':'private'}})
    def test_publish_reuses_recorded_id_without_insert(self,processed,verify):
        youtube=MagicMock();ledger=MagicMock()
        ledger.data={'jobs':[{'video_id':'video','channel_id':'target','mode':'pilot','status':'private_verified'}]}
        youtube.videos().list().execute.return_value={'items':[{'snippet':{'channelId':'target'},'fileDetails':{
            'durationMs':'54600','videoStreams':[{'widthPixels':720,'heightPixels':1280}]}}]}
        operate({'action':'publish','video_id':'video','request_id':'one'},ledger,{'made_for_kids':False},youtube,MagicMock(),{'can_manage':True,'channel_id':'target'})
        youtube.videos().insert.assert_not_called()
        self.assertEqual(ledger.data['jobs'][0]['status'],'published')
        verify.assert_called_once()

    @patch('shorts.pokemon_control.check_processed',return_value={'status':{'privacyStatus':'private'}})
    def test_cancel_removes_schedule_and_verifies_private(self,processed):
        youtube=MagicMock();ledger=MagicMock()
        ledger.data={'jobs':[{'video_id':'video','channel_id':'target','mode':'daily','status':'scheduled'}]}
        youtube.videos().list().execute.return_value={'items':[{'snippet':{'channelId':'target'},'status':{'privacyStatus':'private'}}]}
        operate({'action':'cancel','video_id':'video','request_id':'stop'},ledger,{'made_for_kids':False},youtube,MagicMock(),{'can_manage':True,'channel_id':'target'})
        self.assertNotIn('publishAt',youtube.videos().update.call_args.kwargs['body']['status'])
        self.assertEqual(ledger.data['jobs'][0]['status'],'cancelled')
        youtube.videos().insert.assert_not_called()

class ScheduleConsistencyTests(unittest.TestCase):
    @patch('shorts.pokemon_control.time.sleep')
    @patch('shorts.pokemon_control.check_processed',return_value={'status':{'privacyStatus':'private'}})
    def test_cancel_waits_for_schedule_removal_without_another_update(self,processed,sleep):
        youtube=MagicMock();ledger=MagicMock()
        ledger.data={'jobs':[{'video_id':'video','channel_id':'target','mode':'daily','status':'scheduled'}]}
        youtube.videos().list().execute.side_effect=[
            {'items':[{'snippet':{'channelId':'target'},'status':{'privacyStatus':'private','publishAt':'future'}}]},
            {'items':[{'snippet':{'channelId':'target'},'status':{'privacyStatus':'private'}}]}]
        operate({'action':'cancel','video_id':'video','request_id':'stop'},ledger,{'made_for_kids':False},youtube,MagicMock(),{'can_manage':True,'channel_id':'target'})
        self.assertEqual(ledger.data['jobs'][0]['status'],'cancelled')
        self.assertEqual(youtube.videos().update.call_count,1)
        sleep.assert_called_once_with(5)

    @patch('shorts.pokemon_publish.time.sleep')
    @patch('shorts.pokemon_publish.require_review_deadline')
    @patch('shorts.pokemon_publish.require_future_slot')
    @patch('shorts.pokemon_publish.check_processed',return_value={'status':{'privacyStatus':'private'}})
    def test_status_read_can_lag_without_duplicate_update(self,processed,future,review,sleep):
        from shorts.pokemon_publish import schedule_existing
        client=MagicMock();stamp='2026-10-23T04:30:00Z'
        client.videos().list().execute.side_effect=[
            {'items':[{'snippet':{'channelId':'target'},'status':{'privacyStatus':'private'}}]},
            {'items':[{'snippet':{'channelId':'target'},'status':{'privacyStatus':'private','publishAt':stamp}}]}]
        schedule_existing(client,'video',{'made_for_kids':False},'target',stamp)
        self.assertEqual(client.videos().update.call_count,1)
        client.videos().insert.assert_not_called()
        sleep.assert_called_once_with(5)
