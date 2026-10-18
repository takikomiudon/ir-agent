"""One official-source intake, then a real opt-in qualitative review claim."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text, validate_source
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store
from ir_agent.qualitative_research import QualitativeResearch

HERE = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
CASE = '1980-source-applicability-monitor'
def now(): return datetime.now(timezone.utc)
def save(name, value):
    with (HERE / name).open('x') as f: f.write(json_text(value) + '\n')

assert not (HERE / 'execution-start.json').exists()
capture = json.loads((HERE / 'capture.json').read_text())
assert capture['new_GETs'] == 2
item = capture['GETs'][1]
assert item['HTTP_status'] == 200 and item['complete_body'] and item['error'] is None
raw = HERE / item['raw_file']; extracted = HERE / item['text_file']
assert sha256(raw.read_bytes()).hexdigest() == item['raw_sha256']
assert sha256(extracted.read_bytes()).hexdigest() == item['text_sha256']
content = extracted.read_text()
source = {'id': 'case-public:' + item['raw_sha256'], 'company_id': 'jp:1980',
    'title': '2027年３月期 第１四半期決算短信〔日本基準〕（連結）',
    'url': item['url'], 'source_type': 'public_disclosure',
    'document_kind': 'issuer_earnings_statement', 'published_at': None,
    'retrieved_at': item['http_get_completed_at'], 'source_first_saved_at': None,
    'requires_research': True, 'content': content,
    'metadata': {'document_date_as_printed': '2026-08-05',
        'publication_precision': 'date_only; exact time unknown',
        'raw_file': str(raw.relative_to(ROOT)), 'raw_sha256': item['raw_sha256'],
        'text_file': str(extracted.relative_to(ROOT)), 'content_sha256': item['text_sha256'],
        'physical_page_count': len(content.split('\f')) - 1,
        'current_raw_saved_at': item['raw_saved_at'], 'historical_first_save_unknown': True,
        'semantic_review_scope_recorded_separately': True,
        'source_id_is_local_capture_identifier_not_system_derivation': True}}
assert validate_source(source) == source
save('source-only-bundle.json', {'schema_version': 1, 'sources': [source]})
before_hash = sha256(DB.read_bytes()).hexdigest()
ro = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
assert ro.execute('SELECT count(*) FROM sources').fetchone()[0] == 116
assert ro.execute("SELECT count(*) FROM jobs WHERE status<>'completed'").fetchone()[0] == 0
tables = [r[0] for r in ro.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
before = {t: [list(r) for r in ro.execute('SELECT * FROM ' + t)] for t in tables}
backup = ROOT / ('data/ir-research-before-1980-issuer-' + now().strftime('%Y%m%dT%H%M%S%fZ') + '.sqlite3')
dest = sqlite3.connect(backup); ro.backup(dest); dest.close(); ro.close()
save('execution-start.json', {'recorded_at': now().isoformat(), 'database_main_sha256_before': before_hash,
    'backup_path': str(backup.relative_to(ROOT)), 'backup_sha256': sha256(backup.read_bytes()).hexdigest(),
    'before_table_rows': before})
store = Store(str(DB)); h = Harness(store); q = QualitativeResearch(store)
save('case-before.json', q.show_case(CASE))
ingest = h.ingest({'schema_version': 1, 'sources': [source]})
save('ingest-result.json', ingest); assert ingest == {'companies': 0, 'sources_added': 1, 'theses_added': 0}
queue = Intake(store).queue(now().isoformat(), company_id='jp:1980', limit=1)
save('intake-queue.json', queue); assert len(queue['selected']) == 1
worker = 'parent-1980-issuer-classification'
claim = h.claim(worker, measurement_synthetic=False, caller_namespace='research-session-2026-10-15',
                request_id='daidan-issuer-quarter-intake-20261015')
save('intake-claim.json', claim); jid = claim['original_response']['job_id']
assert claim['current_lease']['valid_now'] and jid == queue['selected'][0]['job_id']
job = store.job(jid); save('intake-packet.json', job['packet'])
assert [s['id'] for s in job['packet']['sources']] == [source['id']]
classification = {'classifications': [{'source_id': source['id'], 'expected_version': 0,
    'kind': 'financial_statement', 'financial_content': True,
    'basis_quote': '2027年３月期          第１四半期決算短信〔日本基準〕（連結）',
    'rationale': '会社公式の四半期決算短信。表紙と資料種別を確認して分類し、詳細比較は別の定性レビューで行う。'}]}
save('classification-input.json', classification)
save('intake-completed.json', h.complete(jid, worker, classification, expected_attempt=1))
current = now(); queue = q.queue_cases([CASE], current.isoformat(), now=current)
save('qualitative-queue.json', queue); assert queue['jobs_created'] == 1
claim = h.claim('parent-1980-issuer-review', lease_seconds=1800, measurement_synthetic=False,
    caller_namespace='research-session-2026-10-15', request_id='daidan-issuer-quarter-review-20261015')
save('qualitative-claim.json', claim)
assert claim['current_lease']['valid_now']
job = store.job(claim['original_response']['job_id']); save('qualitative-job.json', job)
assert job['packet']['kind'] == 'qualitative_review'
assert job['packet']['pending_source_ids'] == [source['id']]
store.close()
print(json_text({'ingest': ingest, 'qualitative_job_id': job['id'], 'lease_seconds': 1800,
                 'pending_source_ids': job['packet']['pending_source_ids']}))
