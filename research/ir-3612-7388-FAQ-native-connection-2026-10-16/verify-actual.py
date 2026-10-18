"""Read-only final receipt. No Store and no successful mutation is replayed."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
BACKUP = ROOT / 'data/backups/3612-7388-FAQ-before-20261016.sqlite3'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
with closing(sqlite3.connect(f'file:{DB}?mode=ro', uri=True)) as c, closing(sqlite3.connect(f'file:{BACKUP}?mode=ro', uri=True)) as old:
    c.execute('pragma query_only=on')
    old.execute('pragma query_only=on')
    schema = lambda db: db.execute('select type,name,sql from sqlite_master order by type,name').fetchall()
    assert schema(c) == schema(old)
    counts, delta = {}, {}
    for (table,) in c.execute("select name from sqlite_master where type='table' order by name"):
        rows = c.execute('select * from "' + table + '"').fetchall()
        prior = old.execute('select * from "' + table + '"').fetchall()
        assert set(prior) <= set(rows), table
        counts[table] = len(rows)
        delta[table] = len(rows) - len(prior)
    assert {t: n for t, n in delta.items() if n} == {'sources': 2, 'source_classifications': 2, 'record_availability': 2, 'jobs': 4, 'job_attempts': 4, 'job_attempt_events': 8, 'job_request_receipts': 4, 'qualitative_case_versions': 2}
    states = dict(c.execute('select status,count(*) from jobs group by status'))
    assert states == {'completed': 172}
    heads = {}
    for cid, version, data in c.execute('select case_id,version,data from qualitative_case_versions order by case_id,version'):
        heads[cid] = {'version': version, 'record': json.loads(data)}
    reads = sum(len(x['record']['reviewed_sources']) for x in heads.values())
    assert (len(heads), counts['qualitative_case_versions'], reads) == (34, 76, 194)
    current = {}
    for code, expected in [('3612', 4), ('7388', 3)]:
        cid = code + '-public-earnings-driver-comparability-monitor'
        head = heads[cid]
        assert head['version'] == 2 and len(head['record']['reviewed_sources']) == expected
        assert head['record']['management_review']['date'] == '2027-01-16'
        job = load(OUT / 'actual-qualitative' / code / 'job-at-claim.json')
        stored = json.loads(c.execute('select result from jobs where id=?', (job['id'],)).fetchone()[0])
        assert stored['request'] == load(OUT / 'actual-qualitative' / code / 'worker-result.json')
        assert stored['request']['case_observation']['outcome'] == 'unresolved'
        current[code] = {'case_id': cid, 'version': 2, 'reviewed_sources': expected, 'outcome': 'unresolved', 'management_review': head['record']['management_review']}
    for source in load(OUT / 'source-bundle.json')['sources']:
        assert json.loads(c.execute('select data from sources where id=?', (source['id'],)).fetchone()[0]) == source
    types, public_companies = {}, set()
    for (data,) in c.execute('select data from sources'):
        source = json.loads(data)
        types[source['source_type']] = types.get(source['source_type'], 0) + 1
        if source['source_type'] == 'public_disclosure':
            public_companies.add(source['company_id'])
    assert types == {'public_disclosure': 256, 'market_data': 1}
    assert all(counts[t] == 0 for t in ['theses', 'decision_policies', 'questions', 'replies', 'position_declarations', 'research_decision_reviews'])
receipt = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'status': 'actual_FAQ_intake_and_condition_review_verified', 'old_schema_and_all_old_27table_rows_preserved': True, 'counts': counts, 'delta': delta, 'job_states': states, 'native_heads': 34, 'native_versions': 76, 'native_reads': 194, 'new_case_states': current, 'source_types': types, 'public_source_companies': len(public_companies), 'new_sources': 2, 'intake_completed': 2, 'qualitative_completed': 2, 'source_reviews_added': 3, 'read_count_explanation': '旧32case187既読＋新2case bootstrap4＋3612既存HTML入口/新FAQと7388新Q&A入口の3レビュー＝194', 'requeue_after_completion': load(OUT / 'actual-qualitative/requeue-after-completion.json'), 'financial_adoption_or_theses_or_IR_questions_or_sends_or_orders': 0, 'index_v42_unchanged_SHA256': sha(ROOT / 'research/ir-case-studies-2026-10-15/disclosed-fact-index-v42.json'), 'actual_DB_main_SHA256': sha(DB)}
target = OUT / 'actual-verification.json'
assert not target.exists()
target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'sources': counts['sources'], 'classifications': counts['source_classifications'], 'completed_jobs': 172, 'native_heads': 34, 'native_versions': 76, 'native_reads': 194, 'DB_main_SHA256': receipt['actual_DB_main_SHA256']}))
