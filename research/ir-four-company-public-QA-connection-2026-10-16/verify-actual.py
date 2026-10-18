"""Finite read-only final DB comparison; no Store, API mutations or new retrieval."""
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
BACKUP = ROOT / 'data/backups/four-company-QA-before-20261016.sqlite3'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
native = lambda s: hashlib.sha256(json.dumps(s, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
before_main = sha(DB)
backup_sha = sha(BACKUP)
with closing(sqlite3.connect(f'file:{DB}?mode=ro', uri=True)) as c, closing(sqlite3.connect(f'file:{BACKUP}?mode=ro', uri=True)) as old:
    c.execute('pragma query_only=on')
    old.execute('pragma query_only=on')
    assert c.execute('pragma query_only').fetchone()[0] == old.execute('pragma query_only').fetchone()[0] == 1
    schema = lambda db: db.execute('select type,name,sql from sqlite_master order by type,name').fetchall()
    assert schema(c) == schema(old)
    tables = [r[0] for r in c.execute("select name from sqlite_master where type='table' order by name")]
    assert len(tables) == 27
    counts, old_counts, delta, old_row_checks = {}, {}, {}, {}
    for table in tables:
        ident = '"' + table.replace('"', '""') + '"'
        rows = c.execute('select * from ' + ident).fetchall()
        prior = old.execute('select * from ' + ident).fetchall()
        assert not (Counter(prior) - Counter(rows)), table
        counts[table], old_counts[table] = len(rows), len(prior)
        delta[table] = len(rows) - len(prior)
        old_row_checks[table] = {'old_rows': len(prior), 'current_rows': len(rows), 'all_old_whole_rows_preserved': True}
    assert {t: n for t, n in delta.items() if n} == {'sources': 4, 'source_classifications': 4, 'record_availability': 4, 'jobs': 7, 'job_attempts': 7, 'job_attempt_events': 14, 'job_request_receipts': 7, 'qualitative_case_versions': 3}
    expected = {'sources': 261, 'source_classifications': 260, 'record_availability': 261, 'jobs': 179, 'job_attempts': 176, 'job_attempt_events': 352, 'job_request_receipts': 176, 'qualitative_case_versions': 79}
    assert all(counts[k] == v for k, v in expected.items())
    states = dict(c.execute('select status,count(*) from jobs group by status'))
    assert states == {'completed': 179}
    kinds = dict(Counter(json.loads(p)['kind'] for (p,) in c.execute('select packet from jobs')))
    assert kinds == {'intake': 135, 'qualitative_review': 44}
    heads, old_heads = {}, {}
    for db, result in [(c, heads), (old, old_heads)]:
        for cid, version, config, data in db.execute('select case_id,version,config_revision,data from qualitative_case_versions order by case_id,version'):
            result[cid] = {'version': version, 'config_revision': config, 'record': json.loads(data)}
    reads = sum(len(x['record']['reviewed_sources']) for x in heads.values())
    old_reads = sum(len(x['record']['reviewed_sources']) for x in old_heads.values())
    assert (len(heads), counts['qualitative_case_versions'], reads) == (34, 79, 197)
    assert (len(old_heads), old_counts['qualitative_case_versions'], old_reads) == (34, 76, 194)
    dates = dict(Counter(x['record']['management_review']['date'] for x in heads.values()))
    assert dates == {'2027-01-15': 12, '2027-01-16': 22}
    current = {}
    for code, version, num_reads in [('4318', 4, 4), ('6200', 5, 6), ('6814', 5, 6)]:
        folder = OUT / 'actual-qualitative' / code
        after = load(folder / 'case-after.json')
        cid = after['case_id']
        head = heads[cid]
        assert head['version'] == version and head['config_revision'] == 1
        assert head['record'] == after['record'] and len(head['record']['reviewed_sources']) == num_reads
        assert head['record']['management_review'] == old_heads[cid]['record']['management_review']
        assert head['record']['case_ref'] == old_heads[cid]['record']['case_ref']
        job = load(folder / 'job-at-claim.json')
        stored = c.execute('select status,result,packet from jobs where id=?', (job['id'],)).fetchone()
        completion = load(folder / 'completion.json')
        request = load(folder / 'worker-result.json')
        assert stored[0] == completion['status'] == 'completed'
        result = json.loads(stored[1]); assert result == completion['result'] and result['request'] == request
        assert request['case_observation']['outcome'] == 'unresolved'
        assert request['management_review_update']['mode'] == 'retain'
        assert all(x['outcome'] == 'unchanged' for x in request['source_reviews']) and len(request['source_reviews']) == 1
        current[code] = {'case_id': cid, 'version': version, 'config_revision': 1, 'reviewed_sources': num_reads, 'outcome': 'unresolved', 'source_outcome': 'unchanged', 'worker_request_whole_exact': True, 'case_after_whole_record_exact': True, 'old_management_and_case_ref_unchanged': True, 'management_review': head['record']['management_review']}
    changed_case_ids = {x['case_id'] for x in current.values()}
    assert all(heads[k] == old_heads[k] for k in heads if k not in changed_case_ids)
    sources = {sid: json.loads(data) for sid, data in c.execute('select id,data from sources')}
    source_checks = []
    for source in load(OUT / 'source-bundle.json')['sources']:
        sid = source['id']; assert sources[sid] == source
        receipt = c.execute('select snapshot_sha256,first_saved_at,basis from record_availability where entity_type=? and entity_id=?', ('source', sid)).fetchall()
        assert len(receipt) == 1 and receipt[0][0] == native(source) and receipt[0][1] and receipt[0][2] == 'trusted_insert'
        cl = json.loads(c.execute('select data from source_classifications where source_id=? order by version desc limit 1', (sid,)).fetchone()[0])
        assert cl['source_snapshot_sha256'] == native(source) and cl['kind'] == 'qa' and cl['inputs_verified'] is False
        source_checks.append({'source_id': sid, 'native_SHA256': native(source), 'whole_object_matched': True, 'classification_snapshot_matched': True, 'first_saved_at': receipt[0][1]})
    assert len(source_checks) == 4
    types = dict(Counter(s['source_type'] for s in sources.values())); assert types == {'public_disclosure': 260, 'market_data': 1}
    public_companies = {s['company_id'] for s in sources.values() if s['source_type'] == 'public_disclosure'}; assert len(public_companies) == 55
    latest_classes = {}
    for sid, data in c.execute('select source_id,data from source_classifications order by source_id,version'): latest_classes[sid] = json.loads(data)
    financial_companies = {sources[sid]['company_id'] for sid, cl in latest_classes.items() if cl['financial_content'] is True}; assert len(financial_companies) == 41
    basis = dict(c.execute('select basis,count(*) from record_availability group by basis')); assert basis == {'legacy_presence': 28, 'trusted_insert': 233}
    zero_tables = ['theses', 'decision_policies', 'questions', 'replies', 'position_declarations', 'research_decision_reviews', 'decision_reviews', 'evaluations']
    assert all(counts[t] == 0 for t in zero_tables)
requeue = load(OUT / 'actual-qualitative/requeue-after-completion.json'); assert requeue['jobs_created'] == 0 and requeue['selected'] == []
index = ROOT / 'research/ir-case-studies-2026-10-15/disclosed-fact-index-v42.json'
assert sha(index) == 'a1f0345a1bfaad52aa3e491885c8364303b0e0558e27b2d737b562a6449160b4'
assert sha(DB) == before_main and sha(BACKUP) == backup_sha
receipt = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'status': 'actual_four_QA_intake_and_three_condition_reviews_verified', 'old_schema_and_all_old_27table_rows_preserved': True, 'old_row_checks': old_row_checks, 'counts': counts, 'old_counts': old_counts, 'delta': delta, 'job_states': states, 'job_kinds': kinds, 'source_types': types, 'availability_basis': basis, 'public_source_companies': len(public_companies), 'financial_content_companies': len(financial_companies), 'native_heads': len(heads), 'native_versions': counts['qualitative_case_versions'], 'native_reads': reads, 'read_count_explanation': '旧34case/76版/194既読＋既存3case各1source読解＝34case/79版/197既読', 'management_dates': dates, 'case_states': current, 'new_source_checks': source_checks, 'requeue_after_completion': requeue, 'zero_tables': zero_tables, 'formal_IR_external_send_order_or_financial_adoption': 0, 'external_actions_limit': 'DB zero tables and bounded phase artifacts verified; no external transport/order operation is performed by this script.', 'index_v42_unchanged_SHA256': sha(index), 'actual_DB_main_SHA256': before_main, 'backup_SHA256': backup_sha, 'before_after_DB_and_backup_bytes_unchanged': True, 'query_only_mode_ro_closing': True, 'Store_mutations_GET_code_tests': 0, 'verification_script_SHA256': sha(Path(__file__))}
target = OUT / 'actual-verification.json'; assert not target.exists(); target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'sources': counts['sources'], 'jobs': counts['jobs'], 'native': [len(heads), counts['qualitative_case_versions'], reads], 'DB_main_SHA256': before_main, 'receipt_SHA256': sha(target)}))
