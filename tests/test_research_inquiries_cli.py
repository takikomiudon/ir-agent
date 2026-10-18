"""CLI workflow stays separate from financial questions and qualitative jobs."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ir_agent.cli import parser, run
from ir_agent.models import json_text
import test_qualitative_research_integration as fixtures


class ResearchInquiryCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.QualitativeIntegrationTests(
            'test_watch_without_thesis_queues_once_completes_and_never_writes_financial_records')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture
        self.f.register()
        source = self.f.store.source('A')
        self.public = {'reviewed_at': fixtures.at(8).isoformat(), 'reviewer': 'synthetic-reader',
            'rationale': 'Read the public term before asking.', 'sources': [{
                'source_id': 'A', 'source_snapshot_sha256': sha256(json_text(source).encode()).hexdigest(),
                'scope': 'Synthetic public observation', 'basis_quote': source['content']}]}
        self.request = {'id': 'inquiry-test', 'case_id': 'orders-case', 'issue_id': 'orders',
            'expected_case_version': 1, 'expected_config_revision': 1,
            'created_at': fixtures.at(9).isoformat(), 'topic': 'term-scope',
            'question': 'Which public term is being referenced?',
            'already_answered': 'The public observation is saved.',
            'remaining_uncertainty': 'The term referenced in the explanation.',
            'branches': [{'id': 'A', 'condition': 'The saved term is referenced.',
                          'comparison_note': 'Annotate the referenced term only.'},
                         {'id': 'unresolved', 'condition': 'The reference remains unclear.',
                          'comparison_note': 'Keep the definition unresolved.'}],
            'public_information_review': self.public}

    def call(self, *arguments, minute=10):
        args = parser().parse_args(['research-inquiry', *map(str, arguments)])
        with patch('ir_agent.cli.now_iso', return_value=fixtures.at(minute).isoformat()):
            return run(args, self.f.store)

    def file(self, name, value):
        path = self.f.root / name
        path.write_text(json.dumps(value))
        return path

    def prepare(self):
        return self.call('add', self.file('inquiry.json', self.request))

    def test_full_cli_cycle_preserves_case_and_financial_namespace(self):
        case_before = deepcopy(self.f.registry.show_case('orders-case'))
        financial_before = deepcopy(self.f.harness.inbox())
        saved = self.prepare()
        self.assertEqual(self.call('show', 'inquiry-test')['record'], saved)
        self.assertEqual(self.call('list')[0]['status'], 'draft')
        self.call('mark-sent', 'inquiry-test', '--sent-at', fixtures.at(11).isoformat(), minute=12)
        reply = {'id': 'reply-test', 'inquiry_id': 'inquiry-test',
                 'received_at': fixtures.at(13).isoformat(),
                 'raw_text': 'Refer to Synthetic order observation A.'}
        received = self.call('reply-add', self.file('reply.json', reply), minute=14)
        self.assertEqual(self.call('reply-show', 'reply-test')['record'], received)
        self.assertEqual(self.call('view', 'inquiry-test', minute=15)['status'], 'held')
        public = deepcopy(self.public)
        public['reviewed_at'] = fixtures.at(15).isoformat()
        review = {'reply_id': 'reply-test', 'expected_version': 0, 'branch_id': 'A',
                  'basis_quote': 'Synthetic order observation A', 'rationale': 'Match the public term.',
                  'recorded_at': fixtures.at(16).isoformat(), 'information_status': 'public_clarification',
                  'public_information_review': public}
        stored = self.call('review', self.file('review.json', review), minute=17)
        self.assertEqual(self.call('reply-show', 'reply-test')['reviews'], [stored])
        view = self.call('view', 'inquiry-test', '--reply-id', 'reply-test', minute=18)
        self.assertEqual(view['comparison_note'], 'Annotate the referenced term only.')
        self.assertTrue(view['meaning_review_required'])
        self.assertFalse(view['case_applied'])
        self.assertEqual(self.f.registry.show_case('orders-case'), case_before)
        self.assertEqual(self.f.harness.inbox(), financial_before)
        for table in ('questions', 'replies', 'theses', 'evaluations', 'decision_reviews'):
            self.assertEqual(self.f.store.connection.execute('SELECT count(*) FROM ' + table).fetchone()[0], 0)

    def test_cli_no_response_keeps_unresolved_without_a_fake_reply(self):
        self.prepare()
        self.call('mark-sent', 'inquiry-test', '--sent-at', fixtures.at(11).isoformat(), minute=12)
        self.call('close', 'inquiry-test', '--reason', 'no_response', minute=13)
        view = self.call('view', 'inquiry-test', minute=14)
        self.assertEqual(view['status'], 'held')
        self.assertIn('no_response', view['reason_codes'])
        self.assertIsNone(view['comparison_note'])
        self.assertEqual(self.call('show', 'inquiry-test')['replies'], [])

    def test_cli_cannot_store_an_unsent_reply(self):
        self.prepare()
        reply = {'id': 'reply-test', 'inquiry_id': 'inquiry-test',
                 'received_at': fixtures.at(11).isoformat(), 'raw_text': 'Synthetic reply.'}
        with self.assertRaisesRegex(ValueError, 'sent'):
            self.call('reply-add', self.file('reply.json', reply), minute=12)
        self.assertEqual(self.call('show', 'inquiry-test')['replies'], [])


if __name__ == '__main__':
    unittest.main()
