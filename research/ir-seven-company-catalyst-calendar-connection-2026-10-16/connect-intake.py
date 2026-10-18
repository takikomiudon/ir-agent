"""Root-only finite intake runner. Existing receipts prevent mutation replay."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store

OUT = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
BACKUP = ROOT / 'data/backups/seven-company-calendar-before-20261016.sqlite3'
CODES = ['2929', '4318', '3817', '6200', '6814']
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def save(path, value):
    assert not path.exists(), f'Receipt already exists; inspect before any retry: {path}'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def process(path, dest, worker):
    assert not dest.exists(), 'Run directory already exists; inspect saved successes'
    dest.mkdir()
    bundle = load(OUT / 'source-bundle.json')
    assert bundle['companies'] == [] and bundle['theses'] == [] and len(bundle['sources']) == 5
    store = Store(path)
    try:
        harness = Harness(store)
        result = harness.ingest(bundle)
        save(dest / 'ingest-result.json', result)
        assert result == {'companies': 0, 'sources_added': 5, 'theses_added': 0}
        for code in CODES:
            result = Intake(store).queue(datetime.now(timezone.utc).isoformat(), company_id='jp:' + code, new_only=True)
            save(dest / f'queue-{code}.json', result)
            assert result['jobs_created'] == 1 and result['selected'][0]['source_count'] == 1
        for n in range(1, 6):
            claim = harness.claim(worker, lease_seconds=900, measurement_synthetic=False,
                                  request_id=f'claim-calendar-intake-{n:02d}',
                                  caller_namespace='root:ir-research:20261016')
            save(dest / f'claim-{n}.json', claim)
            assert claim['current_lease']['valid_now'] and not claim['replayed']
            jid = claim['original_response']['job_id']
            job = store.job(jid)
            save(dest / f'job-at-claim-{n}.json', job)
            packet = job['packet']
            assert packet['kind'] == 'intake' and len(packet['sources']) == 1
            s = packet['sources'][0]
            code = s['company_id'].split(':')[1]
            assert code in CODES and s == next(x for x in bundle['sources'] if x['company_id'] == s['company_id'])
            q = load(ROOT / f'research/ir-case-studies-2026-10-15/{code}/public-catalyst-calendar-discovery-2026-10-16/source-quotes.json')
            quotes = q['quotes'] if isinstance(q, dict) else q
            quote = quotes[0]['quote']
            assert quote and quote in s['content']
            result = {'classifications': [{'source_id': s['id'], 'expected_version': 0,
                      'kind': 'schedule', 'financial_content': False, 'basis_quote': quote,
                      'rationale': '公式IRカレンダーの保存本文。日程・発表/説明会等の掲載であり、財務実績本文や実施確認ではない。原典の日付精度・未掲載・対象外総会を保持し、金融入力は採用しない。'}]}
            save(dest / f'result-{n}.json', result)
            completed = harness.complete(jid, worker, result, expected_attempt=job['attempts'])
            save(dest / f'completion-{n}.json', completed)
            assert completed['status'] == 'completed'
    finally:
        store.close()


def main():
    mode = argparse.ArgumentParser()
    mode.add_argument('mode', choices=['preflight', 'actual'])
    args = mode.parse_args()
    if args.mode == 'preflight':
        assert not BACKUP.exists() and not (OUT / 'preflight').exists()
        before = sha(DB)
        with closing(sqlite3.connect(f'file:{DB}?mode=ro', uri=True)) as source:
            source.execute('PRAGMA query_only=ON')
            assert source.execute("SELECT COUNT(*) FROM jobs WHERE status!='completed'").fetchone()[0] == 0
            with closing(sqlite3.connect(BACKUP)) as target:
                source.backup(target)
        copy = OUT / 'intake-preflight.sqlite3'
        assert not copy.exists()
        shutil.copyfile(BACKUP, copy)
        process(copy, OUT / 'preflight', 'preflight-calendar-intake')
        assert sha(DB) == before
        save(OUT / 'backup-and-preflight.json', {'recorded_at': datetime.now(timezone.utc).isoformat(),
             'backup': str(BACKUP.relative_to(ROOT)), 'backup_SHA256': sha(BACKUP),
             'before_DB_main_SHA256': before, 'source_bundle_SHA256': sha(OUT / 'source-bundle.json'),
             'copy_ingest_5_and_intake_5_completed': True, 'actual_DB_writes': 0})
    else:
        proof = load(OUT / 'backup-and-preflight.json')
        assert proof['copy_ingest_5_and_intake_5_completed']
        assert sha(DB) == proof['before_DB_main_SHA256']
        assert sha(OUT / 'source-bundle.json') == proof['source_bundle_SHA256']
        process(DB, OUT / 'actual-intake', 'root-seven-company-calendar-intake')
        save(OUT / 'actual-intake-completed.json', {'recorded_at': datetime.now(timezone.utc).isoformat(),
             'new_sources': 5, 'intake_jobs_completed': 5, 'DB_main_SHA256': sha(DB),
             'financial_adoption_or_IR_or_trade_changes': 0})


if __name__ == '__main__':
    main()
