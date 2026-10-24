"""Read-only production readiness and per-slot coverage checks; never uploads."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo


def assess(config, state, now=None, require_coverage=False):
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo('Asia/Kolkata'))
    date = local.date().isoformat()
    slots = []
    for clock in config['publish_times_ist']:
        expected = datetime.fromisoformat(f'{date}T{clock}:00').replace(tzinfo=local.tzinfo)
        matches = []
        for job in state['jobs']:
            if job.get('date') != date or not job.get('video_id'):
                continue
            try:
                actual = datetime.fromisoformat(job.get('publish_at', '').replace('Z', '+00:00'))
            except ValueError:
                continue
            if actual == expected and job.get('status') in ('scheduled', 'published'):
                matches.append(job)
        slots.append({'time_ist': clock, 'covered': len(matches) == 1,
                      'video_ids': [j['video_id'] for j in matches],
                      'reason': 'duplicate_active_slot' if len(matches) > 1 else
                                ('verified_record_present' if matches else 'no_verified_schedule_record')})
    blockers = []
    if not config.get('publication_enabled'):
        blockers.append('publication_disabled')
    browser_provider = config.get('production_provider') == 'chatgpt_browser'
    provider_ready = (config.get('chat_production', {}).get('enabled', False) if browser_provider
                      else config.get('production_runner_ready', False))
    if not provider_ready:
        blockers.append('chat_production_disabled' if browser_provider else 'production_host_not_connected')
    # Missing previews are actionable before the review, but not during early preparation.
    review_hour, review_minute = map(int, config['review_time_ist'].split(':'))
    review_minutes = review_hour * 60 + review_minute
    coverage_due = require_coverage or local.hour * 60 + local.minute >= review_minutes - 15
    if coverage_due and any(not s['covered'] for s in slots):
        blockers.append('daily_preview_coverage_incomplete')
    return {'checked_at': local.isoformat(), 'date_ist': date, 'slots': slots,
            'generation_ready': bool(config.get('publication_enabled') and provider_ready),
            'today_fully_covered': all(s['covered'] for s in slots),
            'blockers': blockers, 'healthy': not blockers,
            'evidence': 'repository records; not a fresh YouTube API verification'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-coverage', action='store_true')
    args = parser.parse_args()
    result = assess(json.loads(Path('data/pokemon_channel.json').read_text()),
                    json.loads(Path('data/pokemon_state.json').read_text()),
                    require_coverage=args.require_coverage)
    output = json.dumps(result, indent=2)
    Path('output/pokemon').mkdir(parents=True, exist_ok=True)
    Path('output/pokemon/health.json').write_text(output + '\n')
    print(output)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write('## Pokemon production health\n\n```json\n' + output + '\n```\n')
    if not result['healthy']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
