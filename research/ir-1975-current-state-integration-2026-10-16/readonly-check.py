"""Finite current-state verification; actual SQLite read-only, no Store/network."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = '28185d10772c7e29c57bfb93b967c5e4d94739f6d6b8fd66ce86faa2365dbb64'
digest = lambda path: sha256(path.read_bytes()).hexdigest()
assert digest(DB) == EXPECTED
codefile = ROOT / 'research/ir-public-information-review-binding-integration-2026-10-16/fixed-code-under-test-pins.json'
codepins = json.loads(codefile.read_bytes())
assert len(codepins) == 44 and all(digest(ROOT / path) == pin for path, pin in codepins.items())
with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
    connection.execute('PRAGMA query_only=ON')
    assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
    connection.execute('BEGIN')
    tables = ['companies','sources','record_availability','source_classifications','jobs','job_attempts',
        'job_attempt_events','job_request_receipts','qualitative_case_versions','theses','decision_policies',
        'position_declarations','questions','replies','research_decision_reviews']
    counts = {t: connection.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
    types = connection.execute("SELECT json_extract(data,'$.source_type'),count(*),count(DISTINCT company_id) FROM sources GROUP BY json_extract(data,'$.source_type')").fetchall()
    financial = connection.execute("SELECT count(DISTINCT s.company_id) FROM sources s JOIN source_classifications a ON a.source_id=s.id JOIN (SELECT source_id,max(version) version FROM source_classifications GROUP BY source_id)b ON a.source_id=b.source_id AND a.version=b.version WHERE json_extract(a.data,'$.financial_content')=1").fetchone()[0]
    jobs = connection.execute("SELECT json_extract(packet,'$.kind'),status,count(*) FROM jobs GROUP BY json_extract(packet,'$.kind'),status").fetchall()
    bases = connection.execute("SELECT basis,count(*) FROM record_availability WHERE entity_type='source' GROUP BY basis").fetchall()
    heads = [json.loads(r[0]) for r in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
        (SELECT case_id,max(version) version FROM qualitative_case_versions GROUP BY case_id)b
        ON a.case_id=b.case_id AND a.version=b.version''')]
    dates = {}
    for row in heads:
        review = row['management_review']; key = review['date'] + ' ' + review['timezone']
        dates[key] = dates.get(key, 0) + 1
    actual_file = ROOT / 'research/ir-case-studies-2026-10-15/1975/native-case-setup-2026-10-16/actual-inputs/actual-case.json'
    native = json.loads(actual_file.read_bytes())['record']
    assert next(row for row in heads if row['company_id']=='jp:1975') == native
    assert connection.execute("SELECT count(*) FROM sources WHERE company_id='jp:2163'").fetchone()[0] == 0
    pending = connection.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0]
    connection.rollback()
assert counts == dict(companies=1819,sources=190,record_availability=190,source_classifications=189,jobs=107,
    job_attempts=104,job_attempt_events=208,job_request_receipts=104,qualitative_case_versions=43,
    theses=0,decision_policies=0,position_declarations=0,questions=0,replies=0,research_decision_reviews=0)
assert types == [('market_data',1,1),('public_disclosure',189,32)] and financial == 27
assert jobs == [('intake','completed',87),('qualitative_review','completed',20)]
assert bases == [('legacy_presence',28),('trusted_insert',162)]
assert len(heads) == 22 and sum(len(row['reviewed_sources']) for row in heads) == 129
assert dates == {'2027-01-15 Asia/Tokyo':12,'2027-01-16 Asia/Tokyo':10} and pending == 0
assert digest(DB) == EXPECTED
result = {'recorded_at':datetime.now(timezone.utc).isoformat(),
    'connection':'sqlite mode=ro/query_only/contextlib.closing; no Store',
    'actual_DB_SHA_before':EXPECTED,'actual_DB_SHA_after':digest(DB),'counts':counts,'source_types':types,
    'financial_content_companies':financial,'job_kind_status_counts':jobs,'availability_bases':bases,
    'case_heads':len(heads),'reviewed_sources':sum(len(row['reviewed_sources']) for row in heads),
    'management_date_counts':dates,'native1975v1_whole_record_equal_saved_actual':True,
    'native1975_reviewed_source_count':len(native['reviewed_sources']),'2163_actual_sources':0,
    'fixed_code_under_test_pin_count':44,'all44_current_code_SHA_match':True,
    'code_pins_file_sha256':digest(codefile),'pending_leased':pending,'DB_writes':0,
    'earlier_readonly_diagnostic_errors':[
        'First aggregation used nonexistent jobs.kind; stopped before mutation (RO only).',
        'Schema diagnostic showed packet column but then attempted nonexistent jobs.data; corrected to packet JSON kind. No mutations.']}
with (HERE/'readonly-verification.json').open('x') as output:
    output.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
