"""Root finite four-company QA intake and existing-case queue. Do not replay saved successes."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store

DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()
CASES = ['4318-reported-annual-per-share-basis-monitor', '6200-reported-annual-per-share-basis-monitor', '6814-reported-annual-per-share-basis-monitor']

def save(p, obj):
    assert not p.exists(), 'Inspect existing successes, never replay actual operations'
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def run(path, dest, actual):
    assert not dest.exists()
    dest.mkdir()
    bundle = load(OUT / 'source-bundle.json')
    sources = {s['id']: s for s in bundle['sources']}
    plan = {r['source_id']: r for r in load(OUT / 'intake-classification-plan.json')['classifications']}
    worker = ('root' if actual else 'copy') + '-four-company-QA-intake'
    with closing(Store(path)) as store:
        h = Harness(store)
        result = h.ingest(bundle)
        save(dest / 'ingest.json', result)
        assert result == {'companies': 0, 'sources_added': 4, 'theses_added': 0}
        for code in ['4318', '6200', '6814', '7187']:
            queued = Intake(store).queue(now(), company_id='jp:' + code, new_only=True)
            save(dest / ('queue-' + code + '.json'), queued)
            assert queued['jobs_created'] == 1 and queued['selected'][0]['source_count'] == 1
        for n in [1, 2, 3, 4]:
            claim = h.claim(worker, lease_seconds=600, measurement_synthetic=not actual, caller_namespace='root:ir-research:20261016', request_id=f'claim-four-company-QA-intake-{n:02d}')
            save(dest / f'claim-{n}.json', claim)
            assert not claim['replayed'] and claim['current_lease']['valid_now']
            job = store.job(claim['original_response']['job_id'])
            save(dest / f'job-{n}.json', job)
            assert job['packet']['kind'] == 'intake' and all(sources[s['id']] == s for s in job['packet']['sources'])
            response = {'classifications': [plan[s['id']] for s in job['packet']['sources']]}
            save(dest / f'result-{n}.json', response)
            complete = h.complete(job['id'], worker, response, expected_attempt=job['attempts'])
            save(dest / f'completion-{n}.json', complete)
            assert complete['status'] == 'completed'
        q = QualitativeResearch(store)
        queued = q.queue_cases(CASES, now(), limit=3)
        save(dest / 'qualitative-queue.json', queued)
        assert queued['jobs_created'] == 3
        for row in queued['selected']:
            job = store.job(row['job_id'])
            assert len(job['packet']['sources']) == 1
            assert q.claimable(job['packet'])
        if actual:
            reviews = OUT / 'actual-qualitative'
            assert not reviews.exists()
            reviews.mkdir()
            for n in [1, 2, 3]:
                claim = h.claim('root-four-company-QA-condition-review', lease_seconds=1200, measurement_synthetic=False, caller_namespace='root:ir-research:20261016', request_id=f'claim-four-company-QA-condition-{n:02d}')
                save(reviews / f'claim-{n}.json', claim)
                assert not claim['replayed'] and claim['current_lease']['valid_now']
                job = store.job(claim['original_response']['job_id'])
                folder = reviews / job['company_id'].split(':')[1]
                folder.mkdir()
                save(folder / 'job-at-claim.json', job)
                save(folder / 'full-packet.json', job['packet'])
                save(folder / 'worker-packet.json', q.worker_packet(job['id']))
    save(dest / 'completed.json', {'recorded_at': now(), 'sources_added': 4, 'intake_completed': 4, 'qualitative_queued': 3, 'qualitative_leased': 3 if actual else 0, 'financial_adoption': False})

mode = sys.argv[1]
assert mode in ['preflight', 'actual']
p = load(OUT / 'root-preparation.json')
assert sha(DB) == p['source_DB_main_SHA256']
assert sha(OUT / 'source-bundle.json') == p['source_bundle_SHA256']
assert sha(OUT / 'intake-classification-plan.json') == p['classification_plan_SHA256']
if mode == 'preflight':
    backup = ROOT / p['backup']
    assert sha(backup) == p['backup_SHA256']
    copy = OUT / 'preflight.sqlite3'
    assert not copy.exists()
    shutil.copyfile(backup, copy)
    run(copy, OUT / 'copy-preflight', False)
    assert sha(DB) == p['source_DB_main_SHA256']
else:
    assert (OUT / 'copy-preflight/completed.json').exists()
    run(DB, OUT / 'actual-intake', True)
