"""Three disposable synthetic position-declaration rechecks; no actual DB access."""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import csv
import json
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from ir_agent.decision import evaluate_decision
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.harness import Harness
from ir_agent.store import Store
from test_contacts import IMPORTED, row
from test_decision import plan

T0 = '2026-10-15T01:30:00+00:00'
T1 = '2026-10-15T01:31:00+00:00'
T2 = '2026-10-15T01:32:00+00:00'
T3 = '2026-10-15T01:33:00+00:00'
T4 = '2026-10-15T01:34:00+00:00'
T5 = '2026-10-15T01:35:00+00:00'
clock = datetime.fromisoformat


def dump(store):
    return '\n'.join(store.connection.iterdump())


def rows(store, table):
    return [tuple(r) for r in store.connection.execute('SELECT * FROM ' + table + ' ORDER BY 1')]


def counts(store):
    return [len(rows(store, name)) for name in ('position_observations', 'position_declarations')]


def financial_digest(value):
    return sha256(json.dumps({'valuation': value['thesis']['valuation'], 'policy': value['policy'],
                              'price': value['quote']['price_jpy']}, sort_keys=True).encode()).hexdigest()


def original_gap_and_reopen():
    company_id = 'jp:130A'
    with tempfile.TemporaryDirectory(prefix='ir_position_independent_', dir='/tmp') as temporary:
        path = Path(temporary) / 'synthetic.sqlite3'
        catalog = Path(temporary) / 'contacts.csv'
        item = row()
        assert 'held' not in item
        with catalog.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(item))
            writer.writeheader()
            writer.writerow(item)
        with patch('ir_agent.store.now_iso', return_value=T0):
            store = Store(path)
            harness = Harness(store)
            harness.import_contacts(str(catalog), IMPORTED)
            harness.set_company_status(company_id, 'active', 'Synthetic status only')
        try:
            value = plan()
            original_financial = financial_digest(value)
            value['as_of'] = T1
            value['thesis']['company_id'] = company_id
            for source in value['sources']:
                source['company_id'] = company_id
            value['quote'].update(company_id=company_id, observed_at=IMPORTED, retrieved_at=IMPORTED)
            value['sources'][1]['retrieved_at'] = IMPORTED
            value['sources'][1]['metadata']['observed_at'] = IMPORTED
            saved = clock('2026-10-15T01:30:30+00:00')
            harness.ingest({'schema_version': 1, 'sources': value['sources'], 'theses': [value['thesis']]}, now=saved)
            harness.register_decision_policy(value['policy'], now=saved)
            lifecycle = DecisionLifecycle(store)
            assert store.company(company_id)['held'] is False
            assert lifecycle.position_for(company_id, T1, {}) is None
            value['context']['held'] = None
            held_result = evaluate_decision(value)
            assert held_result['proposed_action'] == 'unresolved'
            assert held_result['reason_codes'] == ['position_not_verified']
            question = deepcopy(value['question'])
            question.update(company_id=company_id, created_at=T1)
            question['decision_contract'] = {
                'policy_id': value['policy']['id'], 'policy_version': 1,
                'quote': value['quote'], 'synthetic': True,
            }
            frozen = harness.add_question(question, now=clock(T1))
            assert frozen['decision_contract']['held'] is None
            assert frozen['decision_contract']['position_snapshot'] is None
            assert frozen['decision_contract']['synthetic_position'] is None
            question_before = store.connection.execute('SELECT data FROM questions').fetchone()[0]
            metadata_rows_before = rows(store, 'position_observations')
            declaration = store.declare_position(company_id, False, now=T2)
            assert declaration['kind'] == 'user_declaration' and declaration['broker_verified'] is False
            assert lifecycle.position_for(company_id, T1, {}) is None
            value['as_of'] = T2
            value['context']['held'] = lifecycle.position_for(company_id, T2, {})['held']
            eligible_result = evaluate_decision(value)
            assert eligible_result['proposed_action'] == 'buy_review'
            assert financial_digest(value) == original_financial
            assert rows(store, 'position_observations')[:len(metadata_rows_before)] == metadata_rows_before
            assert store.connection.execute('SELECT data FROM questions').fetchone()[0] == question_before
            before_refresh = counts(store)
            with patch('ir_agent.store.now_iso', return_value=T3):
                harness.ingest({'schema_version': 1, 'companies': [
                    {'id': company_id, 'name': 'Synthetic provider refresh', 'held': True}]})
            assert counts(store) == before_refresh
            assert store.company(company_id)['held'] is False
            assert store.declared_position_at(company_id, T3) == declaration
            before_reopen = dump(store)
        finally:
            store.close()
        with patch('ir_agent.store.now_iso', return_value=T4):
            reopened = Store(path)
        try:
            assert dump(reopened) == before_reopen
            assert reopened.declared_position_at(company_id, T4) == declaration
            assert reopened.company(company_id)['held'] is False
            assert reopened.connection.execute('SELECT data FROM questions').fetchone()[0] == question_before
        finally:
            reopened.close()
    return {'case': 'catalog_original_gap_explicit_declaration_provider_reopen',
            'catalog_action': held_result['proposed_action'], 'catalog_reason_codes': held_result['reason_codes'],
            'frozen_contract_held': None, 'explicit_false_action': eligible_result['proposed_action'],
            'financial_values_and_policy_unchanged': True, 'old_history_and_question_unchanged': True,
            'provider_did_not_redeclare': True, 'reopen_dump_unchanged': True}


def temporal_and_latest_observation():
    with patch('ir_agent.store.now_iso', return_value=T0):
        store = Store(':memory:')
        Harness(store).ingest({'schema_version': 1, 'companies': [{'id': 'synthetic', 'name': 'Synthetic'}]})
    try:
        old = rows(store, 'position_observations')
        one = store.declare_position('synthetic', False, now=T1)
        two = store.declare_position('synthetic', False, now=T2)
        three = store.declare_position('synthetic', True, now=T3)
        assert one['observation_id'] != two['observation_id'] != three['observation_id']
        assert counts(store) == [4, 3]
        assert rows(store, 'position_observations')[:1] == old
        assert store.declared_position_at('synthetic', '2026-10-15T10:30:59.999999+09:00') is None
        assert store.declared_position_at('synthetic', '2026-10-15T10:31:00+09:00') == one
        assert store.declared_position_at('synthetic', T2) == two
        assert store.declared_position_at('synthetic', T3) == three
        assert store.company('synthetic')['held'] is True
        with patch('ir_agent.store.now_iso', return_value=T4):
            store.observe_position('synthetic', False)
        assert store.declared_position_at('synthetic', T3) == three
        assert store.declared_position_at('synthetic', T4) is None
        assert DecisionLifecycle(store).position_for('synthetic', T4, {}) is None
        assumed = {'synthetic': True, 'synthetic_position': {'held': True, 'observed_at': T3}}
        assert DecisionLifecycle(store).position_for('synthetic', T3, assumed) == three
        try:
            DecisionLifecycle(store).position_for('synthetic', T4, {**assumed, 'synthetic': False})
        except ValueError as error:
            assert 'synthetic position assumption' in str(error)
        else:
            raise AssertionError('Real route accepted a synthetic assumption')
        four = store.declare_position('synthetic', False, now=T5)
        assert four['held'] is False and store.company('synthetic')['held'] is False
        assert store.declared_position_at('synthetic', T4) is None
        assert store.declared_position_at('synthetic', T5) == four
        read_before = dump(store)
        changes_before = store.connection.total_changes
        assert store.declared_position_at('synthetic', T5) == four
        assert dump(store) == read_before and store.connection.total_changes == changes_before
    finally:
        store.close()
    return {'case': 'same_value_temporal_latest_unqualified_and_synthetic_boundary',
            'same_value_false_appended_new_receipt': True, 'true_and_false_company_metadata_consistent': True,
            'equivalent_JST_UTC_and_microsecond_boundary_checked': True,
            'latest_unqualified_blocks_old_receipt': True, 'explicit_redeclaration_restores_current_eligibility': True,
            'synthetic_exception_requires_synthetic_true': True, 'reads_did_not_mutate': True}


def atomic_failure_and_outer_rollback():
    with patch('ir_agent.store.now_iso', return_value=T0):
        store = Store(':memory:')
        harness = Harness(store)
        harness.ingest({'schema_version': 1, 'companies': [{'id': 'synthetic', 'name': 'Synthetic'}]})
    try:
        store.connection.execute("CREATE TRIGGER synthetic_receipt_abort BEFORE INSERT ON position_declarations "
                                 "BEGIN SELECT RAISE(ABORT,'synthetic receipt failure'); END")
        before = dump(store)
        with patch('ir_agent.store.now_iso', return_value=T1):
            try:
                harness.set_company_status('synthetic', 'active', 'Synthetic explicit declaration', held=True)
            except sqlite3.IntegrityError as error:
                assert 'synthetic receipt failure' in str(error)
            else:
                raise AssertionError('Receipt failure did not abort')
        assert dump(store) == before and not store.connection.in_transaction
        store.connection.execute('DROP TRIGGER synthetic_receipt_abort')
        before_outer = dump(store)
        sampled_inside = []
        old_clock = store._clock
        def acquired_clock(now):
            sampled_inside.append(store.connection.in_transaction)
            return old_clock(now)
        try:
            with store.transaction(), patch.object(store, '_clock', side_effect=acquired_clock):
                declaration = store.declare_position('synthetic', True, now=T2)
                assert declaration['held'] is True and store.company('synthetic')['held'] is True
                raise RuntimeError('synthetic outer rollback')
        except RuntimeError as error:
            assert str(error) == 'synthetic outer rollback'
        assert sampled_inside == [True]
        assert dump(store) == before_outer and not store.connection.in_transaction
        assert store.declared_position_at('synthetic', T3) is None
    finally:
        store.close()
    return {'case': 'receipt_failure_outer_rollback_and_runtime_sampling',
            'receipt_failure_rolls_back_company_status_history_receipt': True,
            'direct_nested_declaration_rolls_back_with_outer_transaction': True,
            'runtime_sampled_inside_writer': True}


def run():
    return {'schema_version': 1, 'status': 'three_bounded_synthetic_probes_passed',
            'cases': [original_gap_and_reopen(), temporal_and_latest_observation(), atomic_failure_and_outer_rollback()],
            'execution': {'synthetic_databases': 3, 'actual_DB_accesses': 0, 'GETs': 0, 'full_suite_runs': 0,
                          'production_test_or_old_artifact_edits': 0},
            'limits': ['Existing synthetic plan fixture only; no new model, policy or investment numbers.',
                       'A declaration is a caller assertion, not a broker account verification.',
                       'Current display reassessment of old saved position origins is outside this bounded review.',
                       'Source code and test assertions were read; no producer test method or full suite was rerun.']}


if __name__ == '__main__':
    result = run()
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('independent-probe-result.json')
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'cases': [r['case'] for r in result['cases']]}))
