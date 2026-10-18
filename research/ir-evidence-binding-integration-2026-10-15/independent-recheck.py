"""Bounded offline prediction-binding recheck using fictional temporary DBs.

Fixture setup may configure intentionally bad snapshots/lineage. Each audited
report must preserve the configured DB dump/total_changes; the standalone
reader must also preserve the temporary database bytes. No actual DB is opened.
"""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.models import json_text
from ir_agent.observation_assessments import digest
from ir_agent.prediction_bindings import report_prediction_bindings
from test_prediction_bindings import PredictionBindingsTests, AS_OF, NOW

spec = importlib.util.spec_from_file_location('independent_prediction_binding_reader',
    REPO / 'scripts/report_prediction_bindings.py')
reader_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader_script)


def snapshot(db):
    return list(db.iterdump()), db.total_changes, db.in_transaction


def report(env, requests=None, *, as_of=AS_OF, now=NOW):
    requests = [env.binding] if requests is None else requests
    before = snapshot(env.db); original_requests = deepcopy(requests)
    result = report_prediction_bindings(env.db, requests, as_of=as_of, now=now)
    assert snapshot(env.db) == before
    assert requests == original_requests
    assert result['status'] == 'source_binding_report_only'
    for item in [result, *result['observations']]:
        for field in ('semantic_signal', 'state_independence', 'training', 'calibration'):
            assert item[field] == 'unknown'
        assert item['score'] is None and item['score_request'] is None
    assert all(item['selected_state'] is None for item in result['observations'])
    return result


def environment():
    env = PredictionBindingsTests('runTest')
    # These remain fictional fixtures; synthetic=False exercises the real-data
    # provenance gate without making the observations real or verified.
    env.environment(synthetic=False)
    return env


def base_and_mapping(directory):
    env = environment()
    try:
        baseline = report(env)
        assert baseline['observations'][0]['binding_status'] == 'matched'
        assert baseline['population'] == {'observation_count': 1, 'visible_prediction_count': 1,
                                          'no_prediction_count': 0, 'orphan_prediction_count': 0}
        assert baseline['sources_by_id'][env.state['id']]['record'] == env.state
        assert baseline['reply_snapshots'][env.reply['id']]['record'] == env.reply
        bad = deepcopy(env.binding)
        bad['source_links'][1]['source_snapshot_sha256'] = '0' * 64
        bad['reply_links'][0].update(raw_reply_sha256='0' * 64, basis_quote='A quote absent from the original reply')
        wrong = report(env, [bad])['observations'][0]
        assert wrong['binding_status'] == 'mismatch'
        assert 'source_snapshot_sha_mismatch' in wrong['reason_codes']
        assert 'raw_reply_sha_mismatch' in wrong['reason_codes']
        assert 'raw_reply_quote_mismatch' in wrong['reason_codes']
        unmapped = report(env, [])
        assert unmapped['population'] == baseline['population']
        assert unmapped['observations'][0]['binding_status'] == 'unknown'
        assert len(unmapped['observations'][0]['missing_bindings']) == 3
        # Own no Store constructor/migration: inspect a copied temporary file
        # with the production read-only report script and compare raw bytes.
        file_path = directory / 'synthetic-bindings.sqlite3'
        destination = sqlite3.connect(file_path)
        env.db.backup(destination); destination.close()
        before_bytes = file_path.read_bytes(); before_memory = snapshot(env.db)
        exported = reader_script.read_report(file_path, [env.binding], as_of=AS_OF, now=NOW)
        assert exported == baseline
        assert file_path.read_bytes() == before_bytes and snapshot(env.db) == before_memory
        # A caller-owned transaction remains owned by the caller.
        env.db.execute('BEGIN')
        report(env)
        assert env.db.in_transaction
        env.db.execute('ROLLBACK')
        # A no-prediction member remains in the report population.
        env.db.execute('DELETE FROM ir_predictions')
        no_prediction = report(env)
        assert no_prediction['population']['observation_count'] == 1
        assert no_prediction['population']['visible_prediction_count'] == 0
        assert no_prediction['population']['no_prediction_count'] == 1
        return {'baseline_binding_status': baseline['observations'][0]['binding_status'],
                'bad_sha_and_reply_quote_status': wrong['binding_status'],
                'unmapped_population_preserved': True, 'no_prediction_population_preserved': True,
                'raw_sources_and_reply_preserved': True, 'caller_transaction_preserved': True,
                'script_database_bytes_unchanged': True,
                'script_database_sha256': sha256(before_bytes).hexdigest(),
                'matched_does_not_approve_semantics_or_independence': True, 'score_and_score_request_null': True}
    finally:
        env.doCleanups()


def graph_case(damage=None):
    env = environment()
    try:
        def derived(identity, parents=()):
            value = deepcopy(env.state); value['id'] = identity
            value['metadata'] = {'original_source_ids': list(parents)}
            return value
        common = derived('shared-origin')
        first = derived('first-parent', ['shared-origin'])
        second = derived('second-parent', ['shared-origin'])
        root = derived('derived-state', ['first-parent', 'second-parent'])
        if damage == 'synthetic': second['metadata']['synthetic'] = True
        if damage == 'held': second['metadata']['information_status'] = 'potential_nonpublic'
        if damage == 'future':
            second.update(published_at='2026-11-03T10:00:00+09:00', retrieved_at='2026-11-03T10:01:00+09:00')
        # Root exists before the future second parent, so only that parent is
        # later evidence; the root's own historical receipt remains adequate.
        for item in (common, first, root, second):
            env.save_raw('sources', item, item['retrieved_at'])
        env.binding['source_links'][1].update(source_id=root['id'], source_snapshot_sha256=digest(root))
        result = report(env)
        binding = result['observations'][0]['resolved_bindings'][1]
        parent = next(item for item in binding['lineage_checks'] if item['source_id'] == second['id'])
        root_check = next(item for item in binding['lineage_checks'] if item['source_id'] == root['id'])
        assert root_check['historical_availability']['status'] == 'matched'
        assert sum(item['source_id'] == common['id'] for item in binding['lineage_checks']) == 1
        if damage is None:
            assert binding['status'] == 'matched'
            # Configure a finite cycle with matching fixture receipts; the
            # following audit still must be strictly read-only.
            common['metadata'] = {'original_source_id': root['id']}
            env.db.execute('UPDATE sources SET data=? WHERE id=?', (json_text(common), common['id']))
            env.db.execute('UPDATE record_availability SET snapshot_sha256=? WHERE entity_id=?', (digest(common), common['id']))
            cycle = report(env)['observations'][0]['resolved_bindings'][1]
            assert cycle['status'] == 'mismatch' and 'source_provenance_cycle' in cycle['reason_codes']
            return {'shared_dag': 'matched', 'shared_parent_visits': 1, 'configured_cycle': 'mismatch'}
        if damage == 'held':
            assert binding['status'] == parent['status'] == 'held'
        elif damage == 'synthetic':
            assert binding['status'] == 'mismatch'
            assert 'synthetic_source_in_real_observation' in parent['reason_codes']
        else:
            assert binding['status'] == 'mismatch'
            assert parent['historical_availability']['status'] == 'mismatch'
        return {'binding_status': binding['status'], 'second_parent_status': parent['status'],
                'second_parent_reasons': parent['reason_codes'], 'root_historical_receipt_matched': True}
    finally:
        env.doCleanups()


def legacy_and_current_hold():
    env = environment()
    try:
        exact = report(env)['observations'][0]['resolved_bindings'][0]['lineage_checks'][0]
        assert exact['usage_availability']['availability']['first_save_known'] is True
        env.db.execute("UPDATE record_availability SET basis='legacy_presence',first_saved_at=NULL,presence_observed_at=? "
            "WHERE entity_type='source' AND entity_id=?", ('2026-11-01T00:00:00+09:00', env.premise['id']))
        legacy = report(env)['observations'][0]['resolved_bindings'][0]['lineage_checks'][0]
        assert legacy['usage_availability']['status'] == 'unknown'
        assert legacy['historical_availability']['status'] == 'matched'
        assert legacy['historical_availability']['availability']['first_save_known'] is False
        assert legacy['historical_availability']['availability']['receipt']['first_saved_at'] is None
        review = {'reply_id': env.reply['id'], 'version': 1, 'information_status': 'potential_nonpublic',
                  'recorded_at': '2026-11-03T17:00:00+09:00'}
        env.db.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)',
                       (env.reply['id'], 1, json_text(review), review['recorded_at']))
        current = report(env)['observations'][0]['resolved_bindings'][-1]
        assert current['historical_publicity']['status'] == 'matched'
        assert current['current_publicity']['status'] == current['status'] == 'held'
        return {'trusted_first_save_known': True, 'legacy_usage_before_presence': 'unknown',
                'legacy_historical_after_presence': 'matched', 'legacy_first_save_still_null': True,
                'reply_historical_publicity': 'matched', 'reply_current_publicity': 'held'}
    finally:
        env.doCleanups()


def unknown_tables():
    db = sqlite3.connect(':memory:', isolation_level=None)
    try:
        before = snapshot(db)
        result = report_prediction_bindings(db, [], as_of=AS_OF, now=NOW)
        assert snapshot(db) == before
        assert all(value == 'unknown' for value in result['table_status'].values())
        assert result['population']['observation_count'] == 0
        assert result['score'] is None and result['score_request'] is None
        return {'all_tables_explicit_unknown': True, 'observation_count': 0, 'unscored': True}
    finally:
        db.close()


def main():
    with patch('ir_agent.probability_scoring.score_categorical_forecast', side_effect=AssertionError('Scorer must not be called')) as scorer:
        with tempfile.TemporaryDirectory(prefix='ir-prediction-binding-recheck-') as folder:
            result = {'all_inputs_fictional': True, 'database_scope': 'memory plus one disposable SQLite copy',
                'base_mapping_population_readonly': base_and_mapping(Path(folder)),
                'lineage': {'shared_and_cycle': graph_case(), **{damage: graph_case(damage) for damage in ('future', 'held', 'synthetic')}},
                'receipt_and_publicity_clocks': legacy_and_current_hold(), 'missing_tables': unknown_tables(),
                'score_function_called': scorer.called,
                'limits': ['Mechanical binding agreement does not validate state truth, signal meaning, independence, training or calibration.',
                           'No scorer input or score is generated, including for fully matched bindings.',
                           'Finite synthetic configurations only; not a broad malformed-input or performance audit.',
                           'No production source/tests/docs, actual DB, network, financial hypothesis or threshold changed.']}
        assert not scorer.called
    Path('/tmp/ir_prediction_bindings_recheck.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
