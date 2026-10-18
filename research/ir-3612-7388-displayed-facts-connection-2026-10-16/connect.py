"""Root-only, finite derived-source intake; saved successes must not be replayed."""
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
OUT = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
BACKUP = ROOT / 'data/backups/displayed-facts-before-20261016.sqlite3'
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store
from ir_agent.models import json_text
from ir_agent.disclosed_facts import normalize_disclosed_facts

load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()

def save(p, value):
    assert not p.exists(), f'Inspect existing receipt before any replay: {p}'
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def prepare():
    assert not BACKUP.exists() and not (OUT / 'root-preparation.json').exists()
    before = sha(DB)
    sources, classes, pins = [], [], {}
    with closing(sqlite3.connect(f'file:{DB}?mode=ro', uri=True)) as c:
        c.execute('pragma query_only=on')
        for code, count in [('3612', 1), ('7388', 2)]:
            folder = ROOT / 'research/ir-case-studies-2026-10-15' / code / 'saved-report-per-share-disclosed-facts-2026-10-16'
            for name in ['annual-per-share-saved-report-review-2026-10-16', 'saved-report-per-share-disclosed-facts-2026-10-16']:
                mpath = folder.parent / name / 'manifest.json'
                manifest = load(mpath)
                for domain in ['input_pins', 'files']:
                    for path, digest in manifest[domain].items():
                        resolved = mpath.parent / path if domain == 'files' and not path.startswith('research/') else ROOT / path
                        assert sha(resolved) == digest, path
                        pins[str(resolved.relative_to(ROOT))] = digest
                pins[str(mpath.relative_to(ROOT))] = sha(mpath)
            bundle = load(folder / 'normalized-bundle.json')
            audit = load(folder / 'audit.json')
            original, derived = bundle['sources']
            moment = audit['derived_retrieved_at_execution_time'] if code == '3612' else audit['normalization_now']
            assert normalize_disclosed_facts(load(folder / 'normalization-input.json'), now=moment) == bundle
            row = c.execute('select data,content_hash from sources where id=?', (original['id'],)).fetchone()
            assert row and json.loads(row[0]) == original
            assert row[1] == hashlib.sha256(original['content'].encode()).hexdigest()
            assert c.execute('select 1 from sources where id=?', (derived['id'],)).fetchone() is None
            facts = json.loads(derived['content'])['facts']
            assert len(facts) == count and all(f['kind'] == 'reported_fact' for f in facts)
            sources.append(derived)
            quote = '"concept":"reported_annual_earnings_per_share"'
            assert quote in derived['content']
            classes.append({'source_id': derived['id'], 'expected_version': 0, 'kind': 'other', 'financial_content': True, 'basis_quote': quote,
                            'rationale': code + ' 保存統合報告書の表示値を再表現した派生資料。年度列と分割調整、未確認の基準・分母・日付精度を保持する。原典の再公表や独立証拠ではない。Graham入力認定・金融採用・参考計算・IR判断は行わない。'})
        with closing(sqlite3.connect(BACKUP)) as dest:
            c.backup(dest)
    assert sha(DB) == before
    save(OUT / 'source-bundle.json', {'schema_version': 1, 'companies': [], 'sources': sources, 'theses': []})
    save(OUT / 'intake-classification-plan.json', {'classifications': classes})
    save(OUT / 'root-preparation.json', {'recorded_at': now(), 'actual_DB_main_SHA256': before, 'backup': str(BACKUP.relative_to(ROOT)), 'backup_SHA256': sha(BACKUP), 'source_bundle_SHA256': sha(OUT / 'source-bundle.json'), 'classification_plan_SHA256': sha(OUT / 'intake-classification-plan.json'), 'input_pins': pins, 'parent_image_views': ['3612 physical63/66', '7388 physical42'], 'whole_bundle_replays': 2, 'derived_sources': 2, 'displayed_facts': 3, 'new_native_cases': 0, 'financial_adoption': False, 'reference_calculations': 0})

def run(actual):
    receipt = load(OUT / 'root-preparation.json')
    assert sha(DB) == receipt['actual_DB_main_SHA256']
    for name, key in [('source-bundle.json', 'source_bundle_SHA256'), ('intake-classification-plan.json', 'classification_plan_SHA256')]:
        assert sha(OUT / name) == receipt[key]
    dest = OUT / ('actual-intake' if actual else 'copy-preflight')
    assert not dest.exists(), 'Inspect saved successful steps; never replay actual writes'
    dest.mkdir()
    path = DB if actual else OUT / 'preflight.sqlite3'
    if not actual:
        assert not path.exists() and sha(BACKUP) == receipt['backup_SHA256']
        shutil.copyfile(BACKUP, path)
    else:
        assert (OUT / 'copy-preflight/completed.json').exists()
    bundle = load(OUT / 'source-bundle.json')
    source_map = {s['id']: s for s in bundle['sources']}
    plan = {r['source_id']: r for r in load(OUT / 'intake-classification-plan.json')['classifications']}
    worker = ('root' if actual else 'copy') + '-displayed-facts-intake'
    with closing(Store(path)) as store:
        harness = Harness(store)
        result = harness.ingest(bundle)
        save(dest / 'ingest.json', result)
        assert result == {'companies': 0, 'sources_added': 2, 'theses_added': 0}
        for code in ['3612', '7388']:
            queued = Intake(store).queue(now(), company_id='jp:' + code, new_only=True)
            save(dest / ('queue-' + code + '.json'), queued)
            assert queued['jobs_created'] == 1 and queued['selected'][0]['source_count'] == 1
        for n in [1, 2]:
            claim = harness.claim(worker, lease_seconds=600, measurement_synthetic=not actual, caller_namespace='root:ir-research:20261016', request_id=f'claim-displayed-facts-intake-{n:02d}')
            save(dest / f'claim-{n}.json', claim)
            assert not claim['replayed'] and claim['current_lease']['valid_now']
            job = store.job(claim['original_response']['job_id'])
            save(dest / f'job-{n}.json', job)
            assert job['packet']['kind'] == 'intake' and len(job['packet']['sources']) == 1
            assert all(source_map[s['id']] == s for s in job['packet']['sources'])
            response = {'classifications': [plan[s['id']] for s in job['packet']['sources']]}
            save(dest / f'result-{n}.json', response)
            completed = harness.complete(job['id'], worker, response, expected_attempt=job['attempts'])
            save(dest / f'completion-{n}.json', completed)
            assert completed['status'] == 'completed'
    save(dest / 'completed.json', {'recorded_at': now(), 'sources_added': 2, 'intake_completed': 2, 'native_case_changes': 0, 'financial_adoption_or_calculations': 0})

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['prepare', 'preflight', 'actual'])
    args = p.parse_args()
    prepare() if args.mode == 'prepare' else run(args.mode == 'actual')
