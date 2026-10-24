import unittest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from shorts.channel_health import assess
from shorts.pokemon_main import run_daily_batch


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.config = {'publication_enabled': True, 'production_runner_ready': True,
                       'publish_times_ist': ['10:00', '22:00'], 'review_time_ist': '09:30'}
        self.state = {'jobs': []}

    def check(self, stamp='2026-10-24T09:30:00+05:30', **kwargs):
        return assess(self.config, self.state, datetime.fromisoformat(stamp), **kwargs)

    def cover(self, clock, status='scheduled'):
        self.state['jobs'].append({'date': '2026-10-24', 'video_id': clock,
                                  'publish_at': f'2026-10-24T{clock}:00+05:30', 'status': status})

    def test_missing_previews_at_review_fail(self):
        self.assertIn('daily_preview_coverage_incomplete', self.check()['blockers'])

    def test_early_preparation_not_false_alarm(self):
        self.assertTrue(self.check('2026-10-24T08:30:00+05:30')['healthy'])

    def test_post_batch_requires_coverage_even_early(self):
        self.assertFalse(self.check('2026-10-24T08:30:00+05:30', require_coverage=True)['healthy'])

    def test_0915_missing_previews_alert(self):
        self.assertFalse(self.check('2026-10-24T09:15:00+05:30')['healthy'])

    def test_both_schedules_cover_day(self):
        self.cover('10:00'); self.cover('22:00')
        self.assertTrue(self.check()['healthy'])

    def test_one_schedule_is_partial(self):
        self.cover('10:00')
        self.assertFalse(self.check()['today_fully_covered'])

    def test_host_off_does_not_hide_native_schedules(self):
        self.cover('10:00'); self.cover('22:00')
        self.config['production_runner_ready'] = False
        result = self.check()
        self.assertTrue(result['today_fully_covered'])
        self.assertEqual(result['blockers'], ['production_host_not_connected'])

    def test_browser_provider_does_not_require_legacy_host(self):
        self.cover('10:00'); self.cover('22:00')
        self.config.update(production_runner_ready=False, production_provider='chatgpt_browser',
                           chat_production={'enabled': True})
        self.assertTrue(self.check()['generation_ready'])
        self.assertTrue(self.check()['healthy'])

    def test_disabled_browser_provider_is_a_blocker(self):
        self.config.update(production_provider='chatgpt_browser', chat_production={'enabled': False})
        self.assertIn('chat_production_disabled', self.check()['blockers'])

    def test_cancelled_and_failed_are_not_coverage(self):
        self.cover('10:00', 'cancelled'); self.cover('22:00', 'missed_slot')
        self.assertFalse(any(s['covered'] for s in self.check()['slots']))

    def test_yesterday_not_today(self):
        self.cover('10:00'); self.state['jobs'][0]['date'] = '2026-10-23'
        self.assertFalse(self.check()['slots'][0]['covered'])

    def test_utc_date_boundary_uses_ist(self):
        self.assertEqual(self.check('2026-10-23T20:00:00+00:00')['date_ist'], '2026-10-24')

    def test_no_video_id_not_coverage(self):
        self.cover('10:00'); del self.state['jobs'][0]['video_id']
        self.assertFalse(self.check()['slots'][0]['covered'])

    def test_duplicate_schedules_fail(self):
        self.cover('10:00'); self.cover('10:00'); self.cover('22:00')
        self.assertEqual(self.check()['slots'][0]['reason'], 'duplicate_active_slot')
        self.assertFalse(self.check()['healthy'])

    def test_timezone_equivalent_schedule(self):
        self.cover('10:00'); self.cover('22:00')
        self.state['jobs'][0]['publish_at'] = '2026-10-24T04:30:00Z'
        self.assertTrue(self.check()['healthy'])

    def test_wrong_publish_time_rejected(self):
        self.cover('10:00'); self.state['jobs'][0]['publish_at'] = '2026-10-24T05:30:00Z'
        self.assertFalse(self.check()['slots'][0]['covered'])


class BatchHealthTests(unittest.TestCase):
    def setUp(self):
        self.config = {'publication_enabled': True, 'production_runner_ready': True}
        self.slots = [{'slot': 'morning'}, {'slot': 'evening'}]

    def test_missing_host_fails_without_upload(self):
        self.config['production_runner_ready'] = False
        with (patch('shorts.pokemon_main.Path.read_text', return_value=json.dumps(self.config)),
              patch('shorts.pokemon_main.run') as run):
            with self.assertRaisesRegex(RuntimeError, 'host not connected'):
                run_daily_batch()
            run.assert_not_called()

    def test_missed_window_fails_without_upload(self):
        with (patch('shorts.pokemon_main.Path.read_text', return_value=json.dumps(self.config)),
              patch('shorts.pokemon_main.daily_review_slots', return_value=[]),
              patch('shorts.pokemon_main.run') as run):
            with self.assertRaisesRegex(RuntimeError, 'window missed'):
                run_daily_batch()
            run.assert_not_called()

    def test_first_failure_still_attempts_other_slot(self):
        with (patch('shorts.pokemon_main.Path.read_text', return_value=json.dumps(self.config)),
              patch('shorts.pokemon_main.daily_review_slots', return_value=self.slots),
              patch('shorts.pokemon_main.run', side_effect=[RuntimeError('research failed'), None]) as run):
            with self.assertRaisesRegex(RuntimeError, 'Daily slot failures'):
                run_daily_batch()
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[1].kwargs['requested_slot'], self.slots[1])

    def test_silent_skip_cannot_pass_batch(self):
        self.finish_batch(False)

    def test_covered_batch_succeeds(self):
        self.finish_batch(True)

    def finish_batch(self, covered):
        with (patch('shorts.pokemon_main.Path.read_text', return_value=json.dumps(self.config)),
              patch('shorts.pokemon_main.daily_review_slots', return_value=self.slots),
              patch('shorts.pokemon_main.run'),
              patch('shorts.pokemon_main.Ledger', return_value=MagicMock(data={'jobs': []})),
              patch('shorts.channel_health.assess', return_value={'today_fully_covered': covered})):
            if covered:
                run_daily_batch()
            else:
                with self.assertRaisesRegex(RuntimeError, 'coverage incomplete'):
                    run_daily_batch()


if __name__ == '__main__':
    unittest.main()
