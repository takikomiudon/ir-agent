"""Finite synthetic saved-source follow-up tests; no live case/database access."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ir_agent.availability import RecordAvailability, SCHEMA as AVAILABILITY_SCHEMA
from ir_agent.intake import SCHEMA as CLASSIFICATION_SCHEMA
from ir_agent.models import json_text
from ir_agent.research_monitoring import report_research_monitoring
from test_catalyst_schedule import digest, source

SAVED = '2026-10-15T10:00:00+00:00'
REVIEWED = '2026-10-15T10:30:00+00:00'
RECORDED = '2026-10-15T10:31:00+00:00'
AS_OF = '2026-10-15T11:00:00+00:00'
NOW = '2026-10-16T11:00:00+00:00'


class ResearchMonitoringTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.case_file = self.root / 'case.json'
        self.case_file.write_text('{"management_date":"2027-01-15","research_only":true}\n', encoding='utf-8')
        self.ref = {'path': 'case.json', 'sha256': sha256(self.case_file.read_bytes()).hexdigest()}
        self.db = sqlite3.connect(':memory:', isolation_level=None); self.addCleanup(self.db.close)
        self.db.executescript('CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT);' +
                             AVAILABILITY_SCHEMA + CLASSIFICATION_SCHEMA)
        self.saved_source = source('old')
        self.save(self.saved_source)
        self.case = {'id': 'synthetic-case', 'company_id': 'jp:TEST', 'issue_id': 'author-condition',
            'synthetic': True, 'recorded_at': RECORDED, 'last_review_at': REVIEWED,
            'case_ref': deepcopy(self.ref), 'source_inventory': [
                {'source_id': self.saved_source['id'], 'source_snapshot_sha256': digest(self.saved_source),
                 'issue_review_status': 'reviewed'}],
            'management_review': {'date': '2027-01-15', 'timezone': 'Asia/Tokyo',
                                 'basis_ref': deepcopy(self.ref), 'basis_quote': '2027-01-15'}}

    def save(self, value, *, saved_at=SAVED, classify=True):
        self.db.execute('BEGIN')
        self.db.execute('INSERT INTO sources VALUES (?,?)', (value['id'], json_text(value)))
        RecordAvailability(self.db).record_first_save('source', value['id'], value, now=saved_at)
        self.db.execute('COMMIT')
        if classify:
            self.classify(value, saved_at)

    def classify(self, value, at, *, kind='financial_statement', version=1):
        record = {'source_id': value['id'], 'version': version, 'kind': kind, 'basis_quote': value['content'],
                  'source_snapshot_sha256': digest(value), 'source_sha256': sha256(value['content'].encode()).hexdigest(),
                  'recorded_at': at}
        self.db.execute('INSERT INTO source_classifications VALUES (?,?,?,?,?)',
                        (value['id'], version, json_text(record), at, 'synthetic-classification'))

    def report(self, cases=None, *, as_of=AS_OF, now=NOW, db=None):
        return report_research_monitoring(db or self.db, [self.case] if cases is None else cases,
                                         as_of=as_of, now=now, research_root=self.root)

    def test_watch_style_case_without_numeric_thesis_repeats_without_writes_or_new_trigger(self):
        before, changes, request = list(self.db.iterdump()), self.db.total_changes, deepcopy(self.case)
        result = self.report(); case = result['cases'][0]
        self.assertEqual(case['status'], 'no_new_trigger_in_checked_scope')
        self.assertFalse(case['management_review_check']['due'])
        self.assertEqual(case['source_changes']['new_saved_sources'], [])
        self.assertEqual(case['pending_issue_review_sources'], [])
        self.assertIsNone(case['pillar_impact']); self.assertIsNone(case['investment_action'])
        self.assertEqual(result['jobs_created'], 0)
        self.assertEqual(result, self.report())
        self.assertEqual(self.case, request)
        self.assertEqual(list(self.db.iterdump()), before)
        self.assertEqual(self.db.total_changes, changes)
        self.assertFalse(self.db.in_transaction)

    def test_late_old_publication_old_unlisted_and_review_pending_are_separate(self):
        self.case['source_inventory'][0]['issue_review_status'] = 'not_reviewed'
        self.save(source('old-unlisted'))
        self.save(source('new-late-document'), saved_at='2026-10-15T10:40:00Z')
        result = self.report()['cases'][0]
        self.assertEqual(result['status'], 'needs_manual_review')
        self.assertEqual(result['source_changes'], {'new_saved_sources': ['new-late-document'],
                                                    'previously_unlisted_sources': ['old-unlisted']})
        self.assertEqual(set(result['pending_issue_review_sources']), {'old', 'old-unlisted', 'new-late-document'})
        self.assertEqual(next(s for s in result['sources'] if s['source_id'] == 'old')['issue_review_status'], 'not_reviewed')

    def test_manifest_after_past_cutoff_is_held_and_cannot_make_due_true(self):
        self.case['recorded_at'] = '2026-10-15T12:00:00Z'
        result = self.report()['cases'][0]
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertIn('manifest_recorded_after_as_of', result['reason_codes'])
        self.assertEqual(result['manifest_check']['status'], 'held')
        self.assertIsNone(result['management_review_check']['due'])
        self.assertEqual(result['manifest_prospectiveness'], 'unverified')

    def test_management_date_cannot_be_created_from_an_unrelated_quote(self):
        self.case['management_review']['date'] = '2026-10-01'
        value = self.report()['cases'][0]
        self.assertIsNone(value['management_review_check']['due'])
        self.assertIn('management_date_not_bound_to_quote', value['reason_codes'])

    def test_calendar_due_uses_declared_timezone_and_unknown_remains_unknown(self):
        self.case['management_review']['date'] = '2026-10-16'
        for cutoff, due in [('2026-10-15T14:59:59.999999Z', False), ('2026-10-15T15:00:00Z', True)]:
            # Preserve an actual supporting date in the synthetic file.
            self.case_file.write_text('2026-10-16', encoding='utf-8')
            ref = {'path': 'case.json', 'sha256': sha256(self.case_file.read_bytes()).hexdigest()}
            self.case['case_ref'] = deepcopy(ref); self.case['management_review']['basis_ref'] = ref
            self.case['management_review']['basis_quote'] = '2026-10-16'
            with self.subTest(cutoff=cutoff):
                check = self.report(as_of=cutoff)['cases'][0]['management_review_check']
                self.assertEqual(check['due'], due)
                self.assertTrue(check['date_is_project_management_only'])
        self.case['management_review']['timezone'] = None
        self.assertIsNone(self.report()['cases'][0]['management_review_check']['due'])

    def test_missing_tables_known_empty_and_missing_inventory_are_not_zero_evidence(self):
        other = sqlite3.connect(':memory:', isolation_level=None); self.addCleanup(other.close)
        result = self.report(db=other)
        self.assertEqual(result['coverage']['case_count'], 1)
        self.assertIsNone(result['sections']['sources']['row_count'])
        self.assertIsNone(result['cases'][0]['source_count'])
        self.assertEqual(result['cases'][0]['status'], 'insufficient_evidence')
        self.case['source_inventory'] = None
        result = self.report()['cases'][0]
        self.assertIn('previous_source_inventory_unknown', result['reason_codes'])
        self.case['source_inventory'] = []
        result = self.report()['cases'][0]
        self.assertEqual(result['source_changes']['previously_unlisted_sources'], ['old'])
        self.assertNotIn('previous_source_inventory_unknown', result['reason_codes'])
        empty = sqlite3.connect(':memory:', isolation_level=None); self.addCleanup(empty.close)
        empty.executescript('CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT);' + AVAILABILITY_SCHEMA + CLASSIFICATION_SCHEMA)
        result = self.report(db=empty)['cases'][0]
        self.assertEqual(result['source_count'], 0)

    def test_future_save_and_legacy_receipt_cannot_be_fresh_arrival(self):
        self.save(source('future-save'), saved_at='2026-10-15T12:00:00Z')
        result = self.report()['cases'][0]
        future = next(s for s in result['sources'] if s['source_id'] == 'future-save')
        self.assertEqual(future['arrival'], 'unknown')
        self.assertIn('first_saved_after_knowledge_at', future['reason_codes'])
        self.db.execute("DELETE FROM record_availability WHERE entity_id='old'")
        self.db.execute('BEGIN')
        RecordAvailability(self.db).observe_existing('source', 'old', self.saved_source, now='2026-10-15T12:01:00Z')
        self.db.execute('COMMIT')
        result = self.report(as_of='2026-10-15T13:00:00Z')['cases'][0]
        old = next(s for s in result['sources'] if s['source_id'] == 'old')
        self.assertFalse(old['first_save_known']); self.assertIsNone(old['first_saved_at'])
        self.assertIn('source_first_save_unknown', old['reason_codes'])

    def test_parent_missing_private_parent_and_real_synthetic_mix_stay_held(self):
        self.save(source('reply-parent', source_type='ir_reply', metadata={'synthetic': True, 'information_status': 'public_clarification'}))
        self.save(source('derived-private', metadata={'synthetic': True, 'original_source_id': 'reply-parent'}))
        self.save(source('derived-missing', metadata={'synthetic': True, 'original_source_id': 'missing-parent'}))
        result = self.report()['cases'][0]
        by_id = {s['source_id']: s for s in result['sources']}
        self.assertIn('source_type_outside_schedule_scope', by_id['derived-private']['reason_codes'])
        self.assertIn('source_snapshot_missing', by_id['derived-missing']['reason_codes'])
        self.assertEqual(result['outside_scope_source_count'], 1)
        self.case['synthetic'] = False
        result = self.report()['cases'][0]
        self.assertIn('synthetic_source_in_real_observation', result['reason_codes'])

    def test_missing_classification_and_current_hold_do_not_erase_historical_view(self):
        self.classify(self.saved_source, '2026-10-15T12:00:00Z', kind='unresolved', version=2)
        value = self.report()['cases'][0]['sources'][0]
        self.assertEqual(value['historical_usability']['status'], 'matched')
        self.assertEqual(value['current_use']['status'], 'held')
        self.assertIn('classification_unresolved', value['reason_codes'])
        self.db.execute('DELETE FROM source_classifications')
        value = self.report()['cases'][0]['sources'][0]
        self.assertIn('classification_not_available', value['reason_codes'])

    def test_new_unclassified_source_arrival_does_not_imply_usable_evidence(self):
        self.save(source('new-unclassified'), saved_at='2026-10-15T10:40:00Z', classify=False)
        result = self.report()['cases'][0]
        self.assertEqual(result['source_changes']['new_saved_sources'], ['new-unclassified'])
        item = next(item for item in result['sources'] if item['source_id'] == 'new-unclassified')
        self.assertEqual(item['status'], 'unknown')
        self.assertIn('classification_not_available', item['reason_codes'])
        self.assertEqual(result['status'], 'insufficient_evidence')

    def test_hash_mismatch_and_file_missing_are_results_paths_escaping_are_errors(self):
        self.case['source_inventory'][0]['source_snapshot_sha256'] = '0' * 64
        self.assertIn('inventory_source_sha_mismatch', self.report()['cases'][0]['reason_codes'])
        self.case['case_ref']['sha256'] = '0' * 64
        self.assertIn('research_file_sha_mismatch', self.report()['cases'][0]['reason_codes'])
        self.case['case_ref']['path'] = 'missing.json'
        self.assertIn('research_file_missing_or_unreadable', self.report()['cases'][0]['reason_codes'])
        outside = self.root.parent / 'not-inside-research-root.json'
        for path in ('../not-inside-research-root.json', str(outside)):
            self.case['case_ref']['path'] = path
            with self.subTest(path=path), self.assertRaises(ValueError): self.report()
        link = self.root / 'escape'; link.symlink_to(self.root.parent, target_is_directory=True)
        self.case['case_ref']['path'] = 'escape/outside.json'
        with self.assertRaises(ValueError): self.report()

    def test_input_boundaries_and_outer_transaction_survive(self):
        for mutate in (lambda c: c.update(approved=True), lambda c: c.update(recorded_at=None),
                       lambda c: c.update(synthetic=1), lambda c: c['source_inventory'][0].update(issue_review_status=[]),
                       lambda c: c['management_review'].update(timezone='Not/A_Zone')):
            bad = deepcopy(self.case); mutate(bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError): self.report([bad])
        with self.assertRaises(ValueError): self.report([self.case, self.case])
        with self.assertRaises(ValueError): self.report(as_of='2026-10-17T00:00:00Z')
        before = self.db.total_changes
        self.db.execute('BEGIN')
        self.report()
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.total_changes, before)
        self.db.execute('ROLLBACK')
        self.assertEqual(self.report([])['coverage']['case_count'], 0)


if __name__ == '__main__':
    unittest.main()
