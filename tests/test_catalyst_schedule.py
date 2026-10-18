"""Finite schedule-only fixtures; no actual DB, network or event completion."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ir_agent.availability import RecordAvailability, SCHEMA as AVAILABILITY_SCHEMA
from ir_agent.catalyst_schedule import report_catalyst_schedule
from ir_agent.intake import SCHEMA as CLASSIFICATION_SCHEMA
from ir_agent.models import json_text, parse_json, validate_source

SAVED = '2026-10-15T10:00:00+00:00'
CLASSIFIED = '2026-10-15T10:01:00+00:00'
AS_OF = '2026-10-15T11:00:00+00:00'
NOW = '2026-11-12T11:00:00+00:00'
ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return sha256(json_text(value).encode()).hexdigest()


def source(identifier='calendar', **updates):
    result = {'id': identifier, 'company_id': 'jp:TEST', 'title': 'Synthetic calendar',
        'url': 'https://example.invalid/' + identifier, 'source_type': 'public_disclosure',
        'published_at': None, 'retrieved_at': '2026-10-15T09:00:00+00:00',
        'content': '2026年度 2026年4月～2027年3月 11月06日（予定） 2027年3月期第2四半期決算発表',
        'metadata': {'synthetic': True}}
    result.update(updates)
    return validate_source(result)


def event(saved_source):
    return {'id': 'synthetic-q2-release', 'company_id': saved_source['company_id'], 'synthetic': True,
        'kind': 'earnings_release', 'label': '2027年3月期第2四半期決算発表',
        'period': {'raw_label': '2027年3月期第2四半期', 'fiscal_year_label': '2027年3月期',
                   'quarter_label': '第2四半期', 'basis_quote': saved_source['content'], 'interpretation': 'Synthetic caller period mapping.'},
        'claims': [{'id': 'synthetic-schedule-1', 'kind': 'schedule', 'source_id': saved_source['id'],
            'source_snapshot_sha256': digest(saved_source), 'basis_quote': saved_source['content'],
            'basis_quote_location': None, 'raw_date_label': '11月06日（予定）', 'date': '2026-11-06',
            'time': None, 'timezone': None, 'date_context_quote': '2026年度 2026年4月～2027年3月',
            'date_context_rationale': 'Synthetic year mapping, not independently verified.', 'supersedes_claim_id': None}]}


class CatalystScheduleTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.executescript('CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT);' +
                             AVAILABILITY_SCHEMA + CLASSIFICATION_SCHEMA)
        self.saved_source = source()
        self.save(self.saved_source)
        self.request = event(self.saved_source)

    def save(self, value, *, saved_at=SAVED, classify=True, classification_kind='schedule', classified_at=CLASSIFIED):
        self.db.execute('BEGIN')
        self.db.execute('INSERT INTO sources VALUES (?,?)', (value['id'], json_text(value)))
        RecordAvailability(self.db).record_first_save('source', value['id'], value, now=saved_at)
        self.db.execute('COMMIT')
        if classify:
            self.classify(value, kind=classification_kind, recorded_at=classified_at, saved_at=classified_at)

    def classify(self, value, *, kind='schedule', version=1, recorded_at=CLASSIFIED, saved_at=CLASSIFIED):
        data = {'source_id': value['id'], 'version': version, 'kind': kind, 'basis_quote': value['content'],
                'source_sha256': sha256(value['content'].encode()).hexdigest(),
                'source_snapshot_sha256': digest(value), 'recorded_at': recorded_at,
                'first_saved_at': saved_at, 'inputs_verified': False}
        self.db.execute('INSERT INTO source_classifications VALUES (?,?,?,?,?)',
                        (value['id'], version, json_text(data), saved_at, 'synthetic-job'))

    def report(self, requests=None, *, as_of=AS_OF, now=NOW, window=None):
        return report_catalyst_schedule(self.db, [self.request] if requests is None else requests,
                                       as_of=as_of, now=now, calendar_window=window)

    def test_supported_candidate_remains_floating_and_does_not_complete_event(self):
        before, changes, request = list(self.db.iterdump()), self.db.total_changes, deepcopy(self.request)
        result = self.report(); item = result['events'][0]
        self.assertEqual(result['status'], 'schedule_monitor_only')
        self.assertEqual(item['status'], 'source_bound_candidate')
        self.assertEqual(item['source_binding']['status'], 'matched')
        self.assertEqual(item['timing']['status'], 'floating_date')
        self.assertIsNone(item['due']); self.assertIsNone(item['timing']['scheduled_at'])
        self.assertEqual(item['occurrence']['status'], 'not_established')
        self.assertEqual(item['result_documents']['status'], 'none_linked')
        self.assertTrue(item['semantic_review_required'])
        self.assertEqual(item['mapping_prospectiveness'], 'unverified')
        self.assertEqual(result, self.report())
        self.assertEqual(self.request, request); self.assertEqual(list(self.db.iterdump()), before)
        self.assertEqual(self.db.total_changes, changes); self.assertFalse(self.db.in_transaction)

    def test_window_groups_keep_outside_and_unknown_dates_in_population(self):
        values = [deepcopy(self.request) for _ in range(3)]
        for i, value in enumerate(values):
            value['id'] += str(i); value['claims'][0]['id'] += str(i)
        values[1]['claims'][0]['date'] = '2027-02-05'
        values[2]['claims'][0]['date'] = None
        result = self.report(values, window={'date_from': '2026-11-01', 'date_through': '2026-11-30'})
        self.assertEqual([e['window_group'] for e in result['events']], ['in_window', 'outside_window', 'date_unknown'])
        self.assertEqual(result['coverage'], {'event_count': 3, 'in_window_count': 1,
            'outside_window_count': 1, 'date_unknown_count': 1, 'source_bound_candidate_count': 3})
        self.assertEqual(result['events'][2]['timing']['status'], 'unknown')

    def test_utc_and_jst_midnight_never_resolve_floating_date(self):
        for cutoff in ('2026-11-05T15:00:00Z', '2026-11-06T00:00:00Z', '2026-11-07T00:00:00+09:00'):
            with self.subTest(cutoff=cutoff):
                item = self.report(as_of=cutoff)['events'][0]
                self.assertIsNone(item['due'])
                self.assertEqual(item['timing']['relation_to_as_of'], 'unknown_timezone')
                self.assertEqual(item['occurrence']['status'], 'not_established')

    def test_missing_tables_known_empty_and_missing_source_do_not_drop_events(self):
        empty = sqlite3.connect(':memory:', isolation_level=None); self.addCleanup(empty.close)
        result = report_catalyst_schedule(empty, [self.request], as_of=AS_OF, now=NOW)
        self.assertEqual(result['coverage']['event_count'], 1)
        self.assertEqual(result['events'][0]['status'], 'unknown')
        self.assertTrue(all(v == 'unknown' for v in result['table_status'].values()))
        self.assertTrue(all(v['row_count'] is None for v in result['source_sections'].values()))
        self.assertEqual(list(empty.execute("SELECT name FROM sqlite_master WHERE type='table'")), [])
        self.db.execute('DELETE FROM sources'); self.db.execute('DELETE FROM source_classifications')
        result = self.report([])
        self.assertEqual(result['coverage']['event_count'], 0)
        self.assertEqual(result['table_status']['sources'], 'known')
        self.assertEqual(result['source_sections']['sources']['row_count'], 0)
        self.assertEqual(self.report()['events'][0]['status'], 'unknown')

    def test_unclassified_future_and_late_sources_have_separate_historical_current_checks(self):
        for variant in ('unclassified', 'future', 'late'):
            value = source(variant)
            stamp = SAVED
            if variant == 'future':
                value['retrieved_at'] = '2026-11-09T09:00:00Z'; stamp = '2026-11-09T10:00:00Z'
            if variant == 'late': stamp = '2026-11-09T10:00:00Z'
            self.save(value, saved_at=stamp, classify=False)
            self.classify(value, recorded_at='2026-11-09T10:01:00Z' if variant != 'unclassified' else CLASSIFIED,
                          saved_at='2026-11-09T10:01:00Z' if variant != 'unclassified' else CLASSIFIED,
                          kind='unresolved' if variant == 'unclassified' else 'schedule')
            item = self.report([event(value)])['events'][0]
            with self.subTest(variant=variant):
                self.assertNotEqual(item['status'], 'source_bound_candidate')
                self.assertIn(item['historical_usability']['status'], ('unknown', 'held', 'mismatch'))
                if variant != 'unclassified': self.assertEqual(item['current_use']['status'], 'matched')
                self.assertEqual(item['source_binding']['status'], 'matched')

    def test_future_source_after_runtime_and_missing_receipt_are_never_usable(self):
        value = source('after-now', retrieved_at='2026-11-13T09:00:00Z')
        self.save(value, saved_at='2026-11-13T10:00:00Z', classify=False)
        item = self.report([event(value)])['events'][0]
        self.assertNotEqual(item['current_use']['status'], 'matched')
        self.db.execute('DELETE FROM record_availability WHERE entity_id=?', ('calendar',))
        item = self.report()['events'][0]
        self.assertEqual(item['historical_usability']['status'], 'unknown')
        self.assertIn('availability_receipt_missing', item['reason_codes'])

    def test_current_classification_hold_does_not_rewrite_historical_view(self):
        old = self.report(now=AS_OF)
        self.classify(self.saved_source, kind='unresolved', version=2,
                      recorded_at='2026-11-09T10:02:00Z', saved_at='2026-11-09T10:02:00Z')
        item = self.report()['events'][0]
        self.assertEqual(item['historical_usability']['status'], 'matched')
        self.assertEqual(item['current_use']['status'], 'held')
        self.assertEqual(item['lineage_checks'][0]['historical_classification']['version'], 1)
        self.assertEqual(item['lineage_checks'][0]['current_classification']['version'], 2)
        self.assertEqual(old['events'], self.report(now=AS_OF)['events'])

    def test_classification_late_save_cannot_be_backdated_into_historical_view(self):
        value = source('late-classification')
        self.save(value, classify=False)
        self.classify(value, recorded_at=CLASSIFIED, saved_at='2026-11-09T10:01:00Z')
        item = self.report([event(value)])['events'][0]
        self.assertEqual(item['historical_usability']['status'], 'unknown')
        self.assertEqual(item['current_use']['status'], 'matched')
        self.assertIn('classification_not_available', item['reason_codes'])

    def test_classification_hash_mismatch_cannot_verify_a_matching_schedule_quote(self):
        row = self.db.execute('SELECT data FROM source_classifications WHERE source_id=?', ('calendar',)).fetchone()
        damaged = parse_json(row[0]); damaged['source_snapshot_sha256'] = '0' * 64
        self.db.execute('UPDATE source_classifications SET data=? WHERE source_id=?', (json_text(damaged), 'calendar'))
        item = self.report()['events'][0]
        self.assertEqual(item['source_binding']['status'], 'matched')
        self.assertEqual(item['status'], 'mismatch')
        self.assertIn('classification_source_binding_mismatch', item['reason_codes'])

    def test_sha_quote_context_period_and_location_mismatches_are_reasons(self):
        variations = []
        for key, bad in [('source_snapshot_sha256', '0' * 64), ('basis_quote', 'Never in source'),
                         ('raw_date_label', '12月01日'), ('date_context_quote', '2028年度')]:
            value = deepcopy(self.request); value['claims'][0][key] = bad; variations.append(value)
        value = deepcopy(self.request); value['period']['basis_quote'] = 'Other period'; variations.append(value)
        value = deepcopy(self.request)
        value['claims'][0]['basis_quote_location'] = {'character_start': 1, 'character_end': 4,
            'pdf_page': None, 'printed_page': None, 'offset_unit': 'Unicode', 'saved_text_file': 'unused', 'section': 'Synthetic'}
        variations.append(value)
        for value in variations:
            with self.subTest(value=value):
                self.assertEqual(self.report([value])['events'][0]['source_binding']['status'], 'mismatch')

    def test_parent_gaps_company_synthetic_publicity_and_scope_cannot_hide(self):
        for variant in ('missing', 'company', 'synthetic', 'held', 'market_data', 'ir_reply'):
            parent = source('parent-' + variant, metadata={})
            if variant == 'company': parent['company_id'] = 'different-company'
            if variant == 'synthetic': parent['metadata']['synthetic'] = True
            if variant == 'held': parent['metadata']['information_status'] = 'potential_nonpublic'
            if variant in ('market_data', 'ir_reply'): parent['source_type'] = variant
            root = source('root-' + variant, metadata={'original_source_ids': ['calendar', parent['id']]})
            # The first parent must also be real, so the second parent is tested independently.
            first = source('real-first-' + variant, metadata={})
            root['metadata']['original_source_ids'][0] = first['id']
            self.save(first)
            if variant != 'missing': self.save(parent)
            self.save(root)
            request = event(root); request['synthetic'] = False
            item = self.report([request])['events'][0]
            with self.subTest(variant=variant):
                self.assertNotEqual(item['status'], 'source_bound_candidate')
                self.assertEqual(len(item['lineage_checks']), 3)
                self.assertTrue(item['reason_codes'])

    def test_shared_dag_is_not_cycle_and_cycle_is_diagnostic(self):
        first = source('first'); second = source('second', metadata={'original_source_id': 'first', 'synthetic': True})
        root = source('dag', metadata={'original_source_ids': ['first', 'second'], 'synthetic': True})
        for value in (first, second, root): self.save(value)
        item = self.report([event(root)])['events'][0]
        self.assertEqual(item['status'], 'source_bound_candidate')
        self.assertEqual(len(item['lineage_checks']), 3)
        a = source('cycle-a', metadata={'original_source_id': 'cycle-b', 'synthetic': True})
        b = source('cycle-b', metadata={'original_source_id': 'cycle-a', 'synthetic': True})
        for value in (a, b): self.save(value)
        self.assertIn('source_provenance_cycle', self.report([event(a)])['events'][0]['reason_codes'])

    def test_nonpublic_root_is_held_without_loading_reply_tables(self):
        value = source('reply', source_type='ir_reply', metadata={'information_status': 'public_clarification'})
        self.save(value)
        item = self.report([event(value)])['events'][0]
        self.assertEqual(item['status'], 'held')
        self.assertIn('source_type_outside_schedule_scope', item['reason_codes'])

    def test_malformed_and_out_of_scope_inputs_raise_valueerror_without_changes(self):
        variants = [None, {}, [None], [self.request, self.request]]
        duplicate_claim = deepcopy(self.request); duplicate_claim['id'] = 'different-event'
        variants.append([self.request, duplicate_claim])
        for field, bad in [('kind', []), ('synthetic', 1), ('period', None), ('claims', {}), ('approved', True)]:
            value = deepcopy(self.request); value[field] = bad; variants.append([value])
        for field, bad in [('date', True), ('date', '2026-02-30'), ('timezone', 'Asia/Tokyo'),
            ('time', '15:00'), ('supersedes_claim_id', 'old'), ('kind', 'occurrence'),
            ('source_snapshot_sha256', None), ('basis_quote_location', [])]:
            value = deepcopy(self.request); value['claims'][0][field] = bad; variants.append([value])
        before = list(self.db.iterdump())
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                report_catalyst_schedule(self.db, value, as_of=AS_OF, now=NOW)
        for window in ({}, {'date_from': '2026-11-30', 'date_through': '2026-11-01'}, False):
            with self.subTest(window=window), self.assertRaises(ValueError): self.report(window=window)
        for as_of, now in [('2026-10-15', NOW), (AS_OF, '2026-10-15T10:00:00Z'), (AS_OF, None)]:
            with self.subTest(as_of=as_of, now=now), self.assertRaises(ValueError): self.report(as_of=as_of, now=now)
        self.assertEqual(list(self.db.iterdump()), before)

    def test_query_only_and_external_transaction_are_preserved(self):
        self.db.execute('CREATE TABLE marker(value TEXT)')
        self.db.execute('BEGIN'); self.db.execute("INSERT INTO marker VALUES ('uncommitted')")
        self.report()
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT * FROM marker').fetchone(), ('uncommitted',))
        self.db.execute('ROLLBACK')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM marker').fetchone()[0], 0)
        self.db.execute('PRAGMA query_only=ON')
        self.assertEqual(self.report()['events'][0]['status'], 'source_bound_candidate')
        self.assertEqual(self.db.execute('PRAGMA query_only').fetchone()[0], 1)

    def test_read_only_disk_snapshot_does_not_change_database_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.sqlite3'
            disk = sqlite3.connect(path); self.db.backup(disk); disk.close()
            before = path.read_bytes()
            readonly = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, isolation_level=None)
            try:
                readonly.execute('PRAGMA query_only=ON')
                result = report_catalyst_schedule(readonly, [self.request], as_of=AS_OF, now=NOW)
                self.assertEqual(result['events'][0]['status'], 'source_bound_candidate')
            finally: readonly.close()
            self.assertEqual(path.read_bytes(), before)

    def test_saved_nissui_three_events_on_memory_copy_only(self):
        case = ROOT / 'research/ir-case-studies-2026-10-15/1332'
        candidates = parse_json((case / 'catalyst-schedule-candidates.json').read_text())
        source_bundle = parse_json((case / 'statement-calendar-followup/source-bundle.json').read_text())
        calendar_id = candidates['events'][0]['claims'][0]['source_id']
        calendar = next(s for s in source_bundle['sources'] if s['id'] == calendar_id)
        self.save(calendar, saved_at=SAVED, classified_at=CLASSIFIED)
        fields = {'id', 'company_id', 'synthetic', 'kind', 'label', 'period', 'claims'}
        requests = [{key: value for key, value in e.items() if key in fields} for e in candidates['events']]
        result = self.report(requests)
        self.assertEqual(result['coverage']['source_bound_candidate_count'], 3)
        self.assertEqual([e['timing']['scheduled_date'] for e in result['events']], ['2026-11-06', '2026-11-10', '2027-02-05'])
        self.assertEqual([e['kind'] for e in result['events']], ['earnings_release', 'earnings_presentation', 'earnings_release'])
        self.assertTrue(all(e['due'] is None and e['occurrence']['status'] == 'not_established' for e in result['events']))
