"""Synthetic holdings declarations; catalog metadata is not a declaration."""
from copy import deepcopy
from contextlib import redirect_stdout
import csv
from datetime import datetime
import json
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.decision import evaluate_decision
from ir_agent.cli import main
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.harness import Harness
from ir_agent.store import Store
from test_contacts import row, IMPORTED
from test_decision import plan

T0 = '2026-10-09T00:30:00+00:00'
T1 = '2026-10-09T00:59:00+00:00'
T2 = '2026-10-09T01:00:00+00:00'
T3 = '2026-10-09T01:01:00+00:00'
COMPANY = 'demo-services'


class PositionDeclarationTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:')
        self.addCleanup(self.store.close)
        self.harness = Harness(self.store)

    def seed(self, **extra):
        with patch('ir_agent.store.now_iso', return_value=T0):
            self.harness.ingest({'schema_version': 1, 'companies': [
                {'id': COMPANY, 'name': 'Synthetic company', **extra}]})

    def counts(self):
        return tuple(self.store.connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                     for table in ('position_observations', 'position_declarations'))

    def snapshot(self):
        return '\n'.join(self.store.connection.iterdump())

    def test_ingest_omitted_false_and_true_are_metadata_only_and_decision_is_held(self):
        for held in (None, False, True):
            with self.subTest(held=held):
                self.seed(**({} if held is None else {'held': held}))
                metadata = self.store.position_at(COMPANY, T2)
                self.assertEqual(metadata['kind'], 'observed')
                self.assertIsNone(self.store.declared_position_at(COMPANY, T2))
                position = DecisionLifecycle(self.store).position_for(COMPANY, T2, {})
                self.assertIsNone(position)
                value = plan()
                value['context']['held'] = None if position is None else position['held']
                result = evaluate_decision(value)
                self.assertEqual(result['proposed_action'], 'unresolved')
                self.assertEqual(result['reason_codes'], ['position_not_verified'])
                self.assertEqual(self.counts()[1], 0)

    def test_catalog_import_and_status_omission_never_confirm_a_position(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'contacts.csv'
            item = row()
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(item))
                writer.writeheader(); writer.writerow(item)
            with patch('ir_agent.store.now_iso', return_value=T0):
                self.harness.import_contacts(str(path), IMPORTED)
                self.harness.set_company_status('jp:130A', 'active', 'Synthetic research status only')
            self.assertFalse(self.store.company('jp:130A')['held'])
            self.assertIsNotNone(self.store.position_at('jp:130A', T2))
            self.assertIsNone(self.store.declared_position_at('jp:130A', T2))
            self.assertEqual(self.counts()[1], 0)

    def test_same_value_explicit_true_and_false_append_new_receipts_without_relabelling_old_rows(self):
        for index, held in enumerate((False, True)):
            company = f'synthetic-{index}'
            with patch('ir_agent.store.now_iso', return_value=T0):
                self.harness.ingest({'schema_version': 1, 'companies': [
                    {'id': company, 'name': 'Synthetic', 'held': held}]})
            old = dict(self.store.connection.execute(
                'SELECT * FROM position_observations WHERE company_id=?', (company,)).fetchone())
            self.assertIsNone(self.store.declared_position_at(company, T2))
            with patch('ir_agent.store.now_iso', return_value=T1):
                self.harness.set_company_status(company, 'active', 'Explicit caller holding declaration', held=held)
            declared = self.store.declared_position_at(company, T2)
            self.assertEqual(declared['held'], held)
            self.assertEqual(declared['origin'], 'explicit_user_declaration')
            self.assertEqual(declared['kind'], 'user_declaration')
            self.assertFalse(declared['broker_verified'])
            self.assertNotEqual(declared['observation_id'], old['id'])
            self.assertEqual(dict(self.store.connection.execute(
                'SELECT * FROM position_observations WHERE id=?', (old['id'],)).fetchone()), old)
            self.assertIsNone(self.store.connection.execute(
                'SELECT * FROM position_declarations WHERE observation_id=?', (old['id'],)).fetchone())
            self.assertIsNone(self.store.declared_position_at(company, T0))

    def test_declared_false_releases_only_the_position_gate_without_changing_financial_inputs(self):
        self.seed(held=False)
        value = plan(); original = deepcopy(value)
        self.store.declare_position(COMPANY, False, now=T1)
        position = DecisionLifecycle(self.store).position_for(COMPANY, value['as_of'], {})
        value['context']['held'] = position['held']
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'buy_review')
        original['context']['held'] = False
        self.assertEqual(value, original)

    def test_declaration_clock_is_sampled_after_lock_and_receipt_has_its_own_as_of_boundary(self):
        self.seed()
        original_clock = self.store._clock
        def clock(now):
            self.assertTrue(self.store.connection.in_transaction)
            return original_clock(now)
        with patch.object(self.store, '_clock', side_effect=clock):
            declared = self.store.declare_position(COMPANY, False, now=T1)
        self.assertEqual(declared['observed_at'], T1)
        self.assertEqual(declared['declared_at'], T1)
        self.assertIsNone(self.store.declared_position_at(COMPANY, '2026-10-09T00:58:59.999999+00:00'))
        self.assertIsNotNone(self.store.declared_position_at(COMPANY, T1))
        # A deliberately isolated future receipt cannot authenticate an earlier
        # observation. Production only writes equal trusted receipt/observation times.
        self.store.connection.execute('UPDATE position_declarations SET declared_at=?', (T3,))
        self.assertIsNone(self.store.declared_position_at(COMPANY, T2))
        self.assertIsNotNone(self.store.declared_position_at(COMPANY, T3))

    def test_latest_unqualified_observation_blocks_instead_of_falling_back(self):
        self.seed()
        declared = self.store.declare_position(COMPANY, False, now=T1)
        with patch('ir_agent.store.now_iso', return_value=T2):
            self.store.observe_position(COMPANY, True)
        self.assertEqual(self.store.declared_position_at(COMPANY, T1), declared)
        self.assertTrue(self.store.position_at(COMPANY, T2)['held'])
        self.assertIsNone(self.store.declared_position_at(COMPANY, T2))
        self.assertIsNone(DecisionLifecycle(self.store).position_for(COMPANY, T2, {}))
        newer = self.store.declare_position(COMPANY, True, now=T3)
        self.assertTrue(newer['held'])
        self.assertEqual(newer['declared_at'], T3)

    def test_provider_refresh_preserves_declared_metadata_and_receipt_without_confirming_anything(self):
        self.seed()
        declared = self.store.declare_position(COMPANY, True, now=T1)
        counts = self.counts()
        with patch('ir_agent.store.now_iso', return_value=T2):
            self.harness.ingest({'schema_version': 1, 'companies': [
                {'id': COMPANY, 'name': 'Provider label', 'held': False}]})
        self.assertEqual(self.counts(), counts)
        self.assertTrue(self.store.company(COMPANY)['held'])
        self.assertEqual(self.store.declared_position_at(COMPANY, T2), declared)

    def test_receipt_failure_rolls_back_observation_company_and_outer_status(self):
        self.seed(held=False)
        self.store.connection.execute('''CREATE TRIGGER reject_position_receipt
            BEFORE INSERT ON position_declarations BEGIN SELECT RAISE(ABORT,'receipt failed'); END''')
        before = self.snapshot()
        with patch('ir_agent.store.now_iso', return_value=T1):
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'receipt failed'):
                self.harness.set_company_status(COMPANY, 'active', 'Synthetic failed declaration', held=True)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.store.connection.in_transaction)
        self.assertIsNone(self.store.declared_position_at(COMPANY, T2))

    def test_direct_api_rollback_and_malformed_boolean_preserve_input_and_database(self):
        self.seed()
        before = self.snapshot()
        for invalid in (None, 0, 1, 'false', [], {}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.store.declare_position(COMPANY, invalid, now=T1)
        self.assertEqual(self.snapshot(), before)
        with self.assertRaisesRegex(ValueError, 'rollback synthetic declaration'):
            with self.store.transaction():
                self.store.declare_position(COMPANY, True, now=T1)
                raise ValueError('rollback synthetic declaration')
        self.assertEqual(self.snapshot(), before)

    def test_legacy_reopen_preserves_metadata_and_history_without_minting_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'legacy.sqlite3'
            with patch('ir_agent.store.now_iso', return_value=T0):
                old = Store(path)
                Harness(old).ingest({'schema_version': 1, 'companies': [
                    {'id': COMPANY, 'name': 'Synthetic legacy', 'held': True}]})
            company_before = old.connection.execute('SELECT data FROM companies').fetchone()[0]
            history_before = [tuple(r) for r in old.connection.execute('SELECT * FROM position_observations')]
            old.connection.execute('DROP TABLE position_declarations')
            old.close()
            with patch('ir_agent.store.now_iso', return_value=T2):
                reopened = Store(path)
            try:
                self.assertEqual(reopened.connection.execute('SELECT data FROM companies').fetchone()[0], company_before)
                self.assertEqual([tuple(r) for r in reopened.connection.execute('SELECT * FROM position_observations')], history_before)
                self.assertEqual(reopened.connection.execute('SELECT COUNT(*) FROM position_declarations').fetchone()[0], 0)
                self.assertTrue(reopened.position_at(COMPANY, T2)['held'])
                self.assertIsNone(reopened.declared_position_at(COMPANY, T2))
                self.assertIsNone(reopened.declared_position_at(COMPANY, T0))
            finally:
                reopened.close()

    def test_new_declaration_does_not_rewrite_frozen_question_or_past_decision(self):
        self.seed(held=False)
        value = plan()
        saved_at = datetime.fromisoformat(T2)
        self.harness.ingest({'schema_version': 1, 'sources': value['sources'], 'theses': [value['thesis']]}, now=saved_at)
        self.harness.register_decision_policy(value['policy'], now=saved_at)
        question = deepcopy(value['question'])
        question['decision_contract'] = {'policy_id': value['policy']['id'], 'policy_version': 1,
                                         'quote': value['quote'], 'synthetic': True}
        frozen = self.harness.add_question(question, now=saved_at)
        raw_before = self.store.connection.execute('SELECT data FROM questions').fetchone()[0]
        self.assertIsNone(frozen['decision_contract']['held'])
        self.assertIsNone(frozen['decision_contract']['position_snapshot'])
        self.store.declare_position(COMPANY, False, now=T3)
        self.assertEqual(self.store.connection.execute('SELECT data FROM questions').fetchone()[0], raw_before)
        self.assertIsNone(DecisionLifecycle(self.store).position_for(COMPANY, T2, {}))
        self.assertFalse(DecisionLifecycle(self.store).position_for(COMPANY, T3, {})['held'])
        self.assertEqual(self.store.question(question['id'])['decision_contract']['preflight'],
                         frozen['decision_contract']['preflight'])

    def test_cli_status_omitted_then_explicit_no_held_uses_distinct_confirmation_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'synthetic.sqlite3'
            with patch('ir_agent.store.now_iso', return_value=T0):
                seeded = Store(path)
                Harness(seeded).ingest({'schema_version': 1, 'companies': [
                    {'id': COMPANY, 'name': 'Synthetic CLI company', 'held': False}]})
                seeded.close()
            argv = ['--db', str(path), 'company', 'set-status', COMPANY,
                    '--status', 'active', '--reason', 'Synthetic caller declaration test']
            for flags, stamp, expected_count in (([], T1, 0), (['--no-held'], T2, 1), (['--held'], T3, 2)):
                with patch('ir_agent.store.now_iso', return_value=stamp), redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(main(argv + flags), 0)
                self.assertEqual(json.loads(output.getvalue())['held'], flags == ['--held'])
                connection = sqlite3.connect(path)
                try:
                    self.assertEqual(connection.execute('SELECT COUNT(*) FROM position_declarations').fetchone()[0],
                                     expected_count)
                finally:
                    connection.close()


if __name__ == '__main__':
    unittest.main()
