"""Root-only finite batch; each saved success is retained before checking it."""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store

OUT = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()
CASES = ['5480-cyclical-normalization-monitor',
         '6200-reported-annual-per-share-basis-monitor',
         '6814-reported-annual-per-share-basis-monitor']


def save(path, value):
    assert not path.exists(), f'Existing receipt requires inspection: {path}'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def process(path, dest, *, actual):
    assert not dest.exists(), 'Do not replay a run; inspect saved successes'
    dest.mkdir()
    bundle = load(OUT / 'source-bundle.json')
    plan = load(OUT / 'intake-classification-plan.json')['classifications']
    sources = {s['id']: s for s in bundle['sources']}
    classes = {r['source_id']: r for r in plan}
    assert bundle['companies'] == bundle['theses'] == []
    assert len(sources) == len(plan) == len(classes) == 21 and set(sources) == set(classes)
    for sid, r in classes.items():
        assert set(r) == {'source_id', 'expected_version', 'kind', 'financial_content', 'basis_quote', 'rationale'}
        assert r['expected_version'] == 0 and r['basis_quote'] in sources[sid]['content']
    expected = Counter(s['company_id'] for s in sources.values())
    assert len(expected) == 17
    worker = 'root-guidance-business-intake' if actual else 'copy-guidance-business-intake'
    with closing(Store(path)) as store:
        h = Harness(store)
        result = h.ingest(bundle)
        save(dest / 'ingest-result.json', result)
        assert result == {'companies': 0, 'sources_added': 21, 'theses_added': 0}
        for cid, count in sorted(expected.items()):
            queued = Intake(store).queue(now(), company_id=cid, new_only=True)
            save(dest / ('queue-' + cid.split(':')[1] + '.json'), queued)
            assert queued['jobs_created'] == 1 and queued['selected'][0]['source_count'] == count
        for n in range(1, len(expected) + 1):
            claim = h.claim(worker, lease_seconds=900, measurement_synthetic=not actual,
                            caller_namespace='root:ir-research:20261016',
                            request_id=f'claim-guidance-business-intake-{n:02d}')
            save(dest / f'claim-{n:02d}.json', claim)
            assert not claim['replayed'] and claim['current_lease']['valid_now']
            job = store.job(claim['original_response']['job_id'])
            save(dest / f'job-at-claim-{n:02d}.json', job)
            assert job['packet']['kind'] == 'intake'
            assert all(sources[s['id']] == s for s in job['packet']['sources'])
            result = {'classifications': [classes[s['id']] for s in job['packet']['sources']]}
            save(dest / f'result-{n:02d}.json', result)
            completed = h.complete(job['id'], worker, result, expected_attempt=job['attempts'])
            save(dest / f'completion-{n:02d}.json', completed)
            assert completed['status'] == 'completed'
        q = QualitativeResearch(store)
        queued = q.queue_cases(CASES, now(), limit=3)
        save(dest / 'qualitative-queue.json', queued)
        assert queued['jobs_created'] == 3 and not queued['skipped']
        assert all(len(store.job(x['job_id'])['packet']['sources']) == 2 and
                   q.claimable(store.job(x['job_id'])['packet']) for x in queued['selected'])
        if actual:
            reviews = OUT / 'actual-qualitative'
            assert not reviews.exists()
            reviews.mkdir()
            for n in range(1, 4):
                claim = h.claim('root-guidance-business-condition-review', lease_seconds=1200,
                                measurement_synthetic=False, caller_namespace='root:ir-research:20261016',
                                request_id=f'claim-guidance-business-condition-{n:02d}')
                save(reviews / f'claim-{n}.json', claim)
                assert claim['current_lease']['valid_now'] and not claim['replayed']
                job = store.job(claim['original_response']['job_id'])
                folder = reviews / job['company_id'].split(':')[1]
                assert not folder.exists()
                folder.mkdir()
                save(folder / 'claim.json', claim)
                save(folder / 'job-at-claim.json', job)
                save(folder / 'full-packet.json', job['packet'])
                save(folder / 'worker-packet.json', q.worker_packet(job['id']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'actual'])
    args = parser.parse_args()
    baseline = load(OUT / 'root-preparation/before-backup.json')
    assert sha(DB) == baseline['actual_DB_main_SHA256_before_after']
    if args.mode == 'preflight':
        backup = ROOT / baseline['backup']
        assert sha(backup) == baseline['backup_SHA256']
        copy = OUT / 'intake-native-preflight.sqlite3'
        assert not copy.exists()
        shutil.copyfile(backup, copy)
        process(copy, OUT / 'copy-preflight', actual=False)
        assert sha(DB) == baseline['actual_DB_main_SHA256_before_after']
        save(OUT / 'copy-preflight-accepted.json', {
            'recorded_at': now(), 'sources_added': 21, 'intake_completed': 17,
            'qualitative_queued_and_claimable': 3, 'actual_DB_writes': 0,
            'source_bundle_SHA256': sha(OUT / 'source-bundle.json'),
            'classification_plan_SHA256': sha(OUT / 'intake-classification-plan.json')})
    else:
        proof = load(OUT / 'copy-preflight-accepted.json')
        assert sha(OUT / 'source-bundle.json') == proof['source_bundle_SHA256']
        assert sha(OUT / 'intake-classification-plan.json') == proof['classification_plan_SHA256']
        assert (OUT / 'preparation-parent-acceptance.json').exists()
        process(DB, OUT / 'actual-intake', actual=True)
        save(OUT / 'actual-intake-and-claims-completed.json', {
            'recorded_at': now(), 'sources_added': 21, 'intake_completed': 17,
            'qualitative_jobs_leased': 3, 'financial_adoption_formalIR_or_trade_changes': 0})


if __name__ == '__main__':
    main()
