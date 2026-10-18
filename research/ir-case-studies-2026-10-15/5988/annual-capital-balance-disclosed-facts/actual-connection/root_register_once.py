"""Root's single registration, separate from the accepted shadow-only runner."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3

from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.models import json_text
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('accepted_shadow_helpers', HERE / 'shadow_preflight.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)  # Definitions only; never executes shadow main().


def main():
    assert not any((HERE / n).exists() for n in ('actual-stage.jsonl', 'actual-completion.json', 'actual-error.json'))
    acceptance = json.loads((HERE / 'root-connection-acceptance.json').read_bytes())
    assert acceptance['status'] == 'accepted_for_root_single_actual_registration'
    assert all(s.digest(s.ROOT / p) == h for p, h in acceptance['files'].items())
    assert s.digest(s.DB) == s.EXPECTED
    bundle = json.loads((HERE / 'derived-only-bundle.json').read_bytes())
    request = json.loads((HERE / 'classification-request.json').read_bytes())
    original, derived = json.loads((HERE.parent / 'normalized-bundle.json').read_bytes())['sources']
    assert bundle == {'schema_version': 1, 'companies': [], 'sources': [derived], 'theses': []}
    assert request['classifications'][0]['basis_quote'] in derived['content']
    backup = s.ROOT / 'data/backups/ir-research-before-5988-capital-balance-2026-10-16.sqlite3'
    assert not backup.exists()
    with s.readonly() as ro:
        before, schema, cases = s.snapshot(ro), s.schema(ro), s.state(ro)
        assert sum(before['jobs'].values()) == 86 and sum(before['sources'].values()) == 152
        assert ro.execute("SELECT COUNT(*) FROM jobs WHERE status!='completed'").fetchone()[0] == 0
        assert ro.execute('SELECT COUNT(*) FROM sources WHERE id=?', (s.SOURCE,)).fetchone()[0] == 0
        assert json.loads(ro.execute('SELECT data FROM sources WHERE id=?', (original['id'],)).fetchone()[0]) == original
        with sqlite3.connect(backup) as copy:
            ro.backup(copy)
            assert s.snapshot(copy) == before and s.schema(copy) == schema
    assert s.digest(s.DB) == s.EXPECTED
    stage = 'before_store'
    store = None
    with (HERE / 'actual-stage.jsonl').open('x', encoding='utf8') as journal:
        def log(phase, result):
            journal.write(json.dumps({'recorded_at': s.now().isoformat(), 'stage': stage,
                                      'phase': phase, 'result': result}, ensure_ascii=False) + '\n')
            journal.flush(); os.fsync(journal.fileno())

        def mutate(name, operation):
            nonlocal stage
            stage = name; log('begin', {})
            result = operation(); log('succeeded', result)
            return result

        try:
            store = Store(s.DB)
            assert s.snapshot(store.connection) == before and s.schema(store.connection) == schema
            h = Harness(store)
            assert mutate('ingest', lambda: h.ingest(bundle, now=s.now())) == {
                'companies': 0, 'sources_added': 1, 'theses_added': 0}
            at = s.now()
            q = mutate('queue', lambda: Intake(store).queue(at.isoformat(), company_id=s.COMPANY, new_only=True, now=at))
            assert q['jobs_created'] == len(q['selected']) == 1 and not q['skipped'] and q['deferred_count'] == 0
            selected = q['selected'][0]
            assert selected['company_id'] == s.COMPANY and selected['source_count'] == 1
            job_id = selected['job_id']; packet = store.job(job_id)['packet']
            assert packet['kind'] == 'intake' and packet['stage'] == 'source_classification'
            assert packet['sources'] == [derived] and packet['company'] == store.company(s.COMPANY)
            envelope = mutate('claim', lambda: h.claim(s.WORKER, now=s.now(), measurement_synthetic=False,
                caller_namespace=s.WORKER, request_id='5988-balance-actual-20261016-1'))
            claim, lease = envelope['original_response'], envelope['current_lease']
            assert not envelope['replayed'] and lease['valid_now']
            assert claim['job_id'] == lease['job_id'] == job_id and claim['company_id'] == s.COMPANY
            assert claim['worker'] == lease['worker'] == s.WORKER and claim['generation'] == lease['generation'] == 1
            assert claim['packet_sha256'] == lease['packet_sha256'] == s.sha256(json_text(packet).encode()).hexdigest()
            done = mutate('complete', lambda: h.complete(job_id, s.WORKER, request, expected_attempt=1, now=s.now()))
            assert done['status'] == 'completed' and done['id'] == job_id
            after = s.snapshot(store.connection); comparisons = {}
            assert set(after) == set(before) and s.schema(store.connection) == schema
            for name in before:
                delta = sum(after[name].values()) - sum(before[name].values())
                assert not (before[name] - after[name]) and delta == s.DELTAS.get(name, 0), name
                comparisons[name] = {'before_count': sum(before[name].values()), 'after_count': sum(after[name].values()),
                                     'old_rows_preserved': True, 'delta': delta}
            assert s.state(store.connection) == cases and store.source(original['id']) == original
            assert store.source(s.SOURCE) == derived
            classification = json.loads(store.connection.execute(
                'SELECT data FROM source_classifications WHERE source_id=?', (s.SOURCE,)).fetchone()[0])
            assert all(classification[k] == v for k, v in request['classifications'][0].items() if k != 'expected_version')
            assert classification['inputs_verified'] is False and classification['job_id'] == job_id
            receipt = dict(store.connection.execute('SELECT * FROM record_availability WHERE entity_id=?', (s.SOURCE,)).fetchone())
            assert receipt['basis'] == 'trusted_insert' and receipt['first_saved_at'] == receipt['presence_observed_at']
            assert receipt['snapshot_sha256'] == s.sha256(json_text(derived).encode()).hexdigest()
            store.close(); store = None
            stage = 'verified'
            s.save('actual-completion.json', {'recorded_at': s.now().isoformat(), 'status': 'actual_saved_classified',
                'source_id': s.SOURCE, 'fact_count': 8, 'job_id': job_id, 'availability': receipt,
                'classification': classification, 'before_main_sha256': s.EXPECTED, 'after_main_sha256': s.digest(s.DB),
                'backup': str(backup), 'backup_sha256': s.digest(backup), 'table_comparisons': comparisons,
                'case_state_unchanged': cases, 'financial_inputs_adopted': False})
            log('succeeded', {'job_id': job_id, 'source_id': s.SOURCE})
            print(json.dumps({'status': 'actual_saved_classified', 'job_id': job_id,
                              'first_saved_at': receipt['first_saved_at'], 'main_sha256': s.digest(s.DB)}))
        except BaseException as error:
            if store is not None: store.close()
            failure = {'stage': stage, 'error_type': type(error).__name__, 'error': str(error),
                       'instruction': 'Stop and inspect journal. Do not resend successful or uncertain mutations.'}
            s.save('actual-error.json', failure); log('failed', failure)
            raise


if __name__ == '__main__':
    main()
