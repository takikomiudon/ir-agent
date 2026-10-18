"""Bounded record-only protocol registry recheck in one fictional temp DB.

Uses fixture request builders without executing unit-test methods. Financial,
observation and prediction rows are seeded only into a disposable database.
No production source/tests/docs, actual DB or network is changed.
"""
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.cli import run
from ir_agent.evaluation_protocols import EvaluationProtocols
from ir_agent.harness import Harness
from ir_agent.models import json_text
from ir_agent.observation_store import ObservationStore
from ir_agent.prediction_store import PredictionStore
from ir_agent.store import Store
from test_evaluation_protocols import declared, draft
from test_observation_store import design, fixture
from test_prediction_store import candidate, DESIGN_SAVED, SAVED as PREDICTION_SAVED

TABLE = 'ir_evaluation_protocol_versions'
SAVE = '2026-11-04T03:00:00.123456+00:00'
LATER = '2026-11-04T03:01:00.654321+00:00'


def other_tables(db):
    tables = sorted(row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
    return {table: [tuple(row) for row in db.execute('SELECT * FROM "' + table + '" ORDER BY rowid')]
            for table in tables if table != TABLE}


def snapshot(db):
    return list(db.iterdump()), db.total_changes


def unverified(record):
    assert record['status'] == 'protocol_commitment_only'
    for field in ('cohort_reference', 'model_references', 'source_references', 'source_quotes',
                  'author_principle_adoption', 'rule_correctness', 'prospectiveness', 'blindness', 'independence'):
        assert record['verification'][field] == 'unverified'
    assert record['verification']['execution'] == 'not_performed'
    assert record['verification']['score_eligibility'] == 'not_assessed'
    assert all(field not in record for field in ('score', 'score_request', 'state', 'signal', 'packet'))


def main():
    with tempfile.TemporaryDirectory(prefix='ir-protocol-recheck-') as folder, \
         patch('ir_agent.probability_scoring.score_categorical_forecast', side_effect=AssertionError('Scorer must not run')) as scorer:
        directory = Path(folder); path = directory / 'synthetic-ledger.sqlite3'
        store = Store(path)
        try:
            harness = Harness(store)
            # Existing fixture values are not a new investment hypothesis.
            harness.ingest(json.loads((REPO / 'examples/demo.json').read_text()),
                           now=__import__('datetime').datetime.fromisoformat('2026-10-15T00:00:00+00:00'))
            observations = ObservationStore(store.connection)
            initial = observations.register(design(synthetic=True), DESIGN_SAVED)
            PredictionStore(store.connection).register(candidate(initial), PREDICTION_SAVED)
            observations.append(fixture(), 1, '2026-11-02T16:00:00+09:00')
            untouched = other_tables(store.connection)
            registry = EvaluationProtocols(store.connection)
            request = declared('synthetic-independent-registry')
            request['recorded_at'] = '2020-01-01T00:00:00Z'
            original_request = deepcopy(request)
            first = registry.register(request, 0, now=SAVE)
            assert first['added'] is True and first['draft'] is False and first['unset_fields'] == []
            assert first['first_saved_at'] == SAVE
            assert first['request_sha256'] == sha256(json_text(request).encode()).hexdigest()
            assert request == original_request
            unverified(first)
            before_retry = snapshot(store.connection)
            exact = registry.register(deepcopy(request), 0, now=LATER)
            assert exact == first | {'added': False}
            assert snapshot(store.connection) == before_retry

            second_request = declared(request['id'], version=2)
            second_request['rules']['state'] = 'Synthetic revised procedural prose; not a verified rule.'
            second = registry.register(second_request, 1, now=LATER)
            before_old_retry = snapshot(store.connection)
            old_retry = registry.register(request, 0, now='2026-11-04T03:02:00+00:00')
            assert old_retry == first | {'added': False}
            assert registry.show(request['id'], 1) == old_retry
            assert registry.show(request['id']) == second | {'added': False}
            assert snapshot(store.connection) == before_old_retry

            # Separate SQLite connections compete for the same next version.
            barrier = threading.Barrier(2)
            def contender(recorder):
                db = sqlite3.connect(path, isolation_level=None, timeout=10)
                try:
                    competing = declared(request['id'], version=3)
                    competing['recorded_by'] = recorder
                    barrier.wait(timeout=10)
                    try:
                        saved = EvaluationProtocols(db).register(competing, 2, now='2026-11-04T03:03:00+00:00')
                    except ValueError as error:
                        return {'outcome': 'rejected', 'error': str(error)}
                    return {'outcome': 'added', 'record': saved}
                finally:
                    db.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                a = pool.submit(contender, 'Synthetic contender A')
                b = pool.submit(contender, 'Synthetic contender B')
                competition = [a.result(timeout=15), b.result(timeout=15)]
            assert sorted(item['outcome'] for item in competition) == ['added', 'rejected']
            winner = next(item['record'] for item in competition if item['outcome'] == 'added')
            assert 'immutable' in next(item['error'] for item in competition if item['outcome'] == 'rejected')
            assert registry.show(request['id']) == winner | {'added': False}
            assert [item['version'] for item in registry.history(request['id'])] == [1, 2, 3]
            unverified(winner)
            changed = deepcopy(request); changed['recorded_by'] = 'Different caller content'
            skipped = declared(request['id'], version=5)
            forged = draft('synthetic-forged'); forged['independent'] = True
            forged_clock = draft('synthetic-forged-clock'); forged_clock['first_saved_at'] = '2020-01-01T00:00:00Z'
            for value, previous in ((changed, 0), (skipped, 4), (forged, 0), (forged_clock, 0)):
                before = snapshot(store.connection)
                try:
                    registry.register(value, previous, now='2026-11-04T03:04:00+00:00')
                except ValueError:
                    pass
                else:
                    raise AssertionError('Changed content, skipped CAS or forged verification/clock must fail')
                assert snapshot(store.connection) == before

            before_rollback = list(store.connection.iterdump())
            try:
                with store.transaction():
                    rolled_back = registry.register(draft('synthetic-outer-rollback'), 0,
                                                    now='2026-11-04T03:05:00+00:00')
                    assert rolled_back['added'] and store.connection.in_transaction
                    assert registry.show('synthetic-outer-rollback')['id'] == 'synthetic-outer-rollback'
                    raise RuntimeError('Fictional later failure in owning transaction')
            except RuntimeError:
                pass
            assert list(store.connection.iterdump()) == before_rollback
            try:
                registry.show('synthetic-outer-rollback')
            except ValueError:
                pass
            else:
                raise AssertionError('Outer rollback must remove protocol version')

            cli_request = declared('synthetic-cli-record-only')
            input_file = directory / 'protocol.json'; input_file.write_text(json.dumps(cli_request))
            with patch('ir_agent.cli.now_iso', return_value='2026-11-04T03:06:00.123456+00:00'):
                cli = run(Namespace(command='evaluation-protocol', operation='register', file=str(input_file),
                                    expected_previous_version=0), store)
            unverified(cli)
            before_read = snapshot(store.connection)
            show = run(Namespace(command='evaluation-protocol', operation='show', protocol_id=request['id'], version=1), store)
            history = run(Namespace(command='evaluation-protocol', operation='history', protocol_id=request['id']), store)
            status = run(Namespace(command='status'), store)
            assert show == first | {'added': False}
            assert len(history) == 3 and status['evaluation_protocol_versions'] == 4
            assert snapshot(store.connection) == before_read
            assert other_tables(store.connection) == untouched
            assert not scorer.called
            report = {'all_inputs_fictional': True, 'database_scope': 'one disposable TemporaryDirectory SQLite database',
                'exact_retry_and_old_retry_no_writes': True, 'old_version_retry_preserves_original_first_save': first['first_saved_at'],
                'late_claimed_recorded_at': first['request']['recorded_at'],
                'fully_filled_draft': first['draft'], 'status': first['status'], 'verification': first['verification'],
                'cas_competition': [item['outcome'] for item in competition], 'history_versions': [item['version'] for item in history],
                'changed_content_skipped_cas_and_self_approval_rejected': True,
                'outer_rollback_removed_protocol': True, 'cli_register_show_history_status_connected': True,
                'protocol_version_count': status['evaluation_protocol_versions'],
                'all_other_tables_exactly_unchanged': True, 'existing_thesis_count': status['theses'],
                'existing_prediction_count': status['signal_predictions'], 'scorer_called': scorer.called,
                'limits': ['Record-only registration does not resolve references, execute rules or establish prospective/blind/independent evaluation.',
                           'No packets, state/signal labels, score input or score generated.',
                           'SQLite total_changes counts a rolled-back INSERT; rollback is checked by full logical DB dump, not a false zero-counter claim.',
                           'Finite synthetic cases only; no restore-loss protocol, malformed-table sweep, production edit or network access.']}
        finally:
            store.close()
    Path('/tmp/ir_evaluation_protocol_recheck.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
