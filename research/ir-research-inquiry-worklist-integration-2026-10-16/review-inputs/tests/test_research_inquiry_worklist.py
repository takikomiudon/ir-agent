"""Synthetic read-only follow-up visibility; no live DB or external services."""
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from contextlib import closing
import json
import os
import sqlite3
import subprocess
import sys
import unittest

import test_research_inquiries as fixtures
from ir_agent.information_review import add_assessment
from ir_agent.models import json_text
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.research_inquiry_worklist import read_research_inquiry_worklist
from ir_agent.store import Store

at = fixtures.at
ROOT = Path(__file__).resolve().parents[1]


class ResearchInquiryWorklistTests(unittest.TestCase):
    setUp = fixtures.ResearchInquiryTests.setUp
    add_source = fixtures.ResearchInquiryTests.add_source
    binding = fixtures.ResearchInquiryTests.binding
    inquiry = fixtures.ResearchInquiryTests.inquiry
    prepare = fixtures.ResearchInquiryTests.prepare
    receive = fixtures.ResearchInquiryTests.receive
    review = fixtures.ResearchInquiryTests.review

    def report(self, now=None):
        path = self.root / 'snapshot.sqlite3'
        with closing(sqlite3.connect(path)) as target:
            self.store.connection.backup(target)
        before = path.read_bytes()
        with patch.object(Store, '__init__', side_effect=AssertionError('Store constructor forbidden')):
            result = read_research_inquiry_worklist(path, now=now or at(12))
        self.assertEqual(path.read_bytes(), before)
        return result

    def test_draft_and_waiting_are_work_not_evidence_corrections(self):
        self.prepare()
        result = self.report()
        self.assertEqual(result['status'], 'known')
        self.assertEqual(result['inquiries'][0]['categories'], ['draft'])
        self.assertEqual(result['inquiries'][0]['no_reply_view']['reason_codes'], ['no_reply'])
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        result = self.report()
        self.assertEqual(result['categories']['awaiting_reply'], ['research-one'])
        self.assertEqual(result['categories']['evidence_held'], [])
        self.assertFalse(result['send_ready'])

    def test_all_replies_keep_older_unreviewed_next_to_new_comparison(self):
        self.receive()
        self.api.add_reply({'id': 'later', 'inquiry_id': 'research-one',
                           'received_at': at(8).isoformat(), 'raw_text': 'specified product series'}, now=at(8))
        self.api.add_review(self.review(reply_id='later', recorded_at=at(9).isoformat()), now=at(9))
        result = self.report()
        row = result['inquiries'][0]
        self.assertEqual(row['state'], 'answered')
        self.assertEqual(row['categories'], ['unreviewed', 'comparison_note'])
        self.assertEqual([r['reply_id'] for r in row['replies']], ['later', 'research-reply'])
        self.assertEqual(row['replies'][0]['comparison_note'], self.inquiry()['branches'][0]['comparison_note'])
        self.assertEqual(row['replies'][0]['review_version'], 1)
        self.assertIn('reply_unreviewed', row['replies'][1]['reason_codes'])
        encoded = json.dumps(result)
        for secret in (self.inquiry()['question'], 'See the specified product series in the public paragraph.',
                       self.review()['rationale'], self.source['content'], 'basis_quote', 'raw_text'):
            self.assertNotIn(secret, encoded)

    def test_later_information_correction_holds_and_hides_fixed_note(self):
        self.receive()
        self.api.add_review(self.review(), now=at(8))
        revised = self.review(expected_version=1, recorded_at=at(9).isoformat(),
                              information_status='potential_nonpublic', branch_id='unresolved')
        del revised['public_information_review']
        self.api.add_review(revised, now=at(9))
        view = self.report()['inquiries'][0]['replies'][0]
        self.assertEqual(view['review_version'], 2)
        self.assertEqual(view['categories'], ['evidence_held'])
        self.assertIn('reply_information_held', view['reason_codes'])
        self.assertIsNone(view['comparison_note'])

    def test_current_public_source_correction_uses_old_reply_question_adapter(self):
        # Minimal legacy formal-reply fixture; no financial thesis or interpretation.
        question = {'id': 'formal-q', 'company_id': 'synthetic', 'created_at': at(0).isoformat()}
        reply = {'id': 'formal-r', 'question_id': 'formal-q', 'received_at': at(0).isoformat(),
                 'raw_text': self.source['content'], 'information_status': 'public_clarification'}
        self.store.connection.execute(
            'INSERT INTO questions(id,company_id,topic,status,data,sent_at) VALUES (?,?,?,?,?,?)',
            ('formal-q', 'synthetic', 'prior', 'answered', json_text(question), at(0).isoformat()))
        self.store.connection.execute('INSERT INTO replies VALUES (?,?,?)',
                                       ('formal-r', 'formal-q', json_text(reply)))
        self.source = self.add_source('legacy-public-reply', source_type='ir_reply',
            metadata={'synthetic': True, 'reply_id': 'formal-r', 'information_status': 'public_clarification'})
        self.receive()
        self.api.add_review(self.review(), now=at(8))
        self.assertEqual(self.report()['inquiries'][0]['replies'][0]['status'], 'comparison_note')
        add_assessment(self.store, {'reply_id': 'formal-r', 'expected_version': 0,
            'information_status': 'unclear', 'basis_quote': self.source['content'],
            'rationale': 'Synthetic later public-information correction',
            'recorded_at': at(9).isoformat()}, now=at(9).isoformat())
        result = self.report()
        view = result['inquiries'][0]['replies'][0]
        self.assertEqual(view['categories'], ['evidence_held'])
        self.assertIn('public_information_held', view['reason_codes'])
        self.assertIn('review_public_information_held', view['reason_codes'])
        self.assertIsNone(view['comparison_note'])

    def test_case_change_holds_both_reviewed_and_unreviewed_replies(self):
        self.receive()
        self.api.add_review(self.review(), now=at(8))
        self.api.add_reply({'id': 'later', 'inquiry_id': 'research-one',
                           'received_at': at(8).isoformat(), 'raw_text': 'later raw'}, now=at(8))
        self.case_request['recorded_at'] = at(9).isoformat()
        QualitativeResearch(self.store).register_case(self.case_request, 1, research_root=self.root, now=at(9))
        result = self.report()
        self.assertEqual(result['inquiries'][0]['categories'], ['unreviewed', 'evidence_held'])
        for view in result['inquiries'][0]['replies']:
            self.assertIn('case_or_files_changed', view['reason_codes'])
            self.assertIsNone(view['comparison_note'])

    def test_no_response_is_not_negative_evidence_or_evidence_correction(self):
        self.prepare()
        self.api.mark_sent('research-one', at(5).isoformat(), now=at(5))
        self.api.close_inquiry('research-one', 'no_response', now=at(8))
        result = self.report()
        self.assertEqual(result['inquiries'][0]['closure_reason'], 'no_response')
        self.assertIn('no_response', result['inquiries'][0]['no_reply_view']['reason_codes'])
        self.assertEqual(result['categories']['evidence_held'], [])
        self.assertFalse(result['no_response_is_negative_evidence'])

    def test_inventory_is_not_silently_limited_to_twenty(self):
        for number in range(23):
            self.api.add_inquiry(self.inquiry(id=f'i-{number:02}', topic=f't-{number}'), now=at(4))
        result = self.report()
        self.assertEqual(len(result['inquiries']), 23)
        self.assertEqual(result['sections']['research_inquiries']['row_count'], 23)
        self.assertEqual(len(result['categories']['draft']), 23)

    def test_missing_table_is_unknown_not_empty_inventory(self):
        self.prepare()
        self.store.connection.execute('DROP TABLE research_inquiry_reviews')
        result = self.report()
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['sections']['research_inquiries']['row_count'], 1)
        self.assertIsNone(result['sections']['research_inquiry_reviews']['row_count'])
        self.assertEqual(result['sections']['research_inquiry_reviews']['reason_codes'], ['table_missing'])

    def test_unsupported_schema_preserves_unknown_count(self):
        self.store.connection.execute('DROP TABLE research_inquiry_reviews')
        self.store.connection.execute('CREATE TABLE research_inquiry_reviews(reply_id TEXT)')
        section = self.report()['sections']['research_inquiry_reviews']
        self.assertIsNone(section['row_count'])
        self.assertEqual(section['reason_codes'], ['table_schema_unsupported'])

    def test_cli_success_is_metadata_only_and_zero_requires_intact_tables(self):
        empty = self.report()
        self.assertEqual(empty['status'], 'known')
        self.assertTrue(all(section['row_count'] == 0 for section in empty['sections'].values()))
        self.prepare()
        self.report()
        path = self.root/'snapshot.sqlite3'
        before = path.read_bytes()
        result = subprocess.run([sys.executable, str(ROOT/'scripts/report_research_inquiries.py'),
                                 '--db', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['inquiries'][0]['inquiry_id'], 'research-one')
        self.assertNotIn(self.inquiry()['question'], result.stdout)
        self.assertEqual(before, path.read_bytes())

    def test_missing_support_table_is_unknown_and_does_not_emit_exception_text(self):
        self.prepare()
        self.store.connection.execute('DROP TABLE qualitative_case_versions')
        result = self.report()
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['dependencies']['qualitative_case_versions']['reason_codes'], ['table_missing'])
        self.assertEqual(result['categories']['unknown'], ['research-one'])
        self.assertEqual(result['inquiries'][0]['no_reply_view']['reason_codes'], ['current_view_unavailable'])

    def test_empty_inquiries_cannot_certify_missing_dependency_table_as_zero(self):
        self.store.connection.execute('DROP TABLE reply_information_reviews')
        result = self.report()
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['sections']['research_inquiries']['row_count'], 0)
        self.assertEqual(result['dependencies']['reply_information_reviews']['status'], 'unknown')

    def test_existing_path_opened_read_only_query_only_snapshot_and_closed(self):
        self.prepare()
        path = self.root / 'snapshot.sqlite3'
        with closing(sqlite3.connect(path)) as target:
            self.store.connection.backup(target)
        real_connect = sqlite3.connect
        connections, trace = [], []
        def connect(*args, **kwargs):
            self.assertTrue(args[0].endswith('?mode=ro'))
            self.assertTrue(kwargs['uri'])
            connection = real_connect(*args, **kwargs)
            connection.set_trace_callback(trace.append)
            connections.append(connection)
            return connection
        before = sha256(path.read_bytes()).hexdigest()
        with patch('ir_agent.research_inquiry_worklist.sqlite3.connect', side_effect=connect):
            read_research_inquiry_worklist(path, now=at(12))
        self.assertIn('PRAGMA query_only=ON', trace)
        self.assertIn('BEGIN', trace)
        self.assertIn('ROLLBACK', trace)
        self.assertFalse(any(s.split()[0].upper() in {'INSERT','UPDATE','DELETE','CREATE','ALTER','DROP'} for s in trace))
        with self.assertRaises(sqlite3.ProgrammingError): connections[0].execute('SELECT 1')
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), before)

    def test_cli_missing_db_not_created_and_no_historical_clock_option(self):
        path = self.root / 'does-not-exist.sqlite3'
        command = [sys.executable, str(ROOT/'scripts/report_research_inquiries.py'), '--db', str(path)]
        result = subprocess.run(command, capture_output=True, text=True,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertFalse(path.exists())
        result = subprocess.run(command + ['--as-of', at(1).isoformat()], capture_output=True, text=True)
        self.assertIn('unrecognized arguments', result.stderr)
        self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
