"""Finite root registration; never replay saved actual successes."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store

DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
BACKUP = ROOT / 'data/backups/3612-7388-native-before-20261016.sqlite3'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()

def save(p, obj):
    assert not p.exists(), 'Inspect existing successful receipt before proceeding'
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def run(path, folder, *, queue_after_registration):
    assert not folder.exists()
    folder.mkdir()
    with closing(Store(path)) as store:
        q = QualitativeResearch(store)
        ids = []
        for code in ['3612', '7388']:
            request = load(OUT / code / 'register-request.json')
            result = q.register_case(request, expected_version=0, research_root=ROOT)
            save(folder / (code + '-registration.json'), result)
            ids.append(request['case_id'])
        if queue_after_registration:
            queued = q.queue_cases(ids, now(), limit=2)
            save(folder / 'queue.json', queued)
            assert queued['jobs_created'] == 1
    save(folder / 'completed.json', {'recorded_at': now(), 'registered': 2, 'bootstrap_reads': 4, 'queue_called': queue_after_registration, 'financial_theses_or_questions': 0})

mode = sys.argv[1]
assert mode in ['preflight', 'actual']
if mode == 'preflight':
    m = load(OUT / 'manifest.json')
    for p, h in m['input_pins'].items():
        assert sha(ROOT / p) == h, p
    for p, h in m['files'].items():
        assert sha(OUT / p) == h, p
    before = sha(DB)
    assert not BACKUP.exists()
    with closing(sqlite3.connect(f'file:{DB}?mode=ro', uri=True)) as source:
        source.execute('pragma query_only=on')
        with closing(sqlite3.connect(BACKUP)) as destination:
            source.backup(destination)
    save(OUT / 'root-preparation.json', {'recorded_at': now(), 'source_DB_main_SHA256': before, 'backup_SHA256': sha(BACKUP), 'manifest_SHA256': sha(OUT / 'manifest.json'), 'semantic_scope_parent_accepted': 'Public comparison definitions; no future-earnings support, financial adoption or formal IR'})
    copy = OUT / 'native-preflight.sqlite3'
    assert not copy.exists()
    shutil.copyfile(BACKUP, copy)
    run(copy, OUT / 'copy-preflight', queue_after_registration=True)
    assert sha(DB) == before
else:
    p = load(OUT / 'root-preparation.json')
    assert sha(DB) == p['source_DB_main_SHA256'] and sha(OUT / 'manifest.json') == p['manifest_SHA256']
    assert (OUT / 'copy-preflight/completed.json').exists()
    run(DB, OUT / 'actual-registration', queue_after_registration=False)
