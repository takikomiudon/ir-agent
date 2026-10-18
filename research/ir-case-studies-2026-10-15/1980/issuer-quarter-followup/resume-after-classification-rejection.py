"""Correct one rejected result on the already-owned intake attempt."""
from datetime import datetime, timezone
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text
from ir_agent.harness import Harness
from ir_agent.store import Store
from ir_agent.qualitative_research import QualitativeResearch
HERE = Path(__file__).resolve().parent
def load(n): return json.loads((HERE / n).read_text())
def save(n,v):
    with (HERE / n).open('x') as f: f.write(json_text(v)+'\n')
store = Store(str(ROOT / 'data/ir-research-2026-10-15.sqlite3')); h = Harness(store)
claim = load('intake-claim.json'); jid = claim['original_response']['job_id']
job = store.job(jid)
assert job['status'] == 'leased' and job['attempts'] == 1
result = load('classification-input.json'); result['classifications'][0]['kind'] = 'financial_statement'
save('classification-input-v2.json', result)
save('classification-rejection.json', {'recorded_at': datetime.now(timezone.utc).isoformat(),
    'rejected_kind': 'earnings_release', 'error': 'Invalid source classification kind',
    'corrected_kind': 'financial_statement', 'same_attempt': 1,
    'new_GETs_new_sources_new_intake_jobs': 0})
save('intake-completed.json', h.complete(jid, 'parent-1980-issuer-classification', result, expected_attempt=1))
q = QualitativeResearch(store); now = datetime.now(timezone.utc)
queue = q.queue_cases(['1980-source-applicability-monitor'], now.isoformat(), now=now)
save('qualitative-queue.json', queue); assert queue['jobs_created'] == 1
claim = h.claim('parent-1980-issuer-review', lease_seconds=1800, measurement_synthetic=False,
    caller_namespace='research-session-2026-10-15', request_id='daidan-issuer-quarter-review-20261015')
save('qualitative-claim.json', claim); assert claim['current_lease']['valid_now']
job = store.job(claim['original_response']['job_id']); save('qualitative-job.json', job)
source = load('source-only-bundle.json')['sources'][0]
assert job['packet']['kind'] == 'qualitative_review'
assert job['packet']['pending_source_ids'] == [source['id']]
store.close(); print(json_text({'qualitative_job_id': job['id'], 'pending_source_ids': job['packet']['pending_source_ids']}))
