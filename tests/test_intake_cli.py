"""Thesis-free source intake and operational reporting through the CLI."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main

ROOT = Path(__file__).resolve().parents[1]


class IntakeCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name); self.db = self.root / 'intake.sqlite3'

    def call(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', str(self.db), *map(str, args)])
        return code, stdout.getvalue(), stderr.getvalue()

    def ok(self, *args):
        code, stdout, stderr = self.call(*args)
        self.assertEqual(code, 0, stderr); self.assertEqual(stderr, '')
        return json.loads(stdout)

    def file(self, name, value):
        path = self.root / name; path.write_text(json.dumps(value)); return path

    def test_watch_company_can_complete_source_classification_without_a_valuation(self):
        bundle = {'schema_version': 1, 'companies': [{'id': 'test', 'name': 'Synthetic intake company'}],
                  'sources': [{'id': 'statement', 'company_id': 'test', 'title': 'Synthetic financial statement',
                      'url': 'https://example.invalid/statement', 'source_type': 'public_disclosure',
                      'published_at': None, 'retrieved_at': '2026-10-01T10:00:00+09:00',
                      'content': 'Synthetic financial statement: balance sheet and income statement.'}]}
        with patch('ir_agent.harness.datetime', wraps=datetime) as seed_clock:
            seed_clock.now.return_value = datetime.fromisoformat('2026-10-01T10:00:00+09:00')
            self.ok('ingest', self.file('bundle.json', bundle))
        queued = self.ok('intake', '--company-id', 'test')
        self.assertEqual(len(queued['selected']), 1)
        job = self.ok('claim', '--worker', 'intake-worker')
        self.assertEqual(job['packet']['kind'], 'intake')
        result = {'classifications': [{'source_id': 'statement', 'expected_version': 0,
                   'kind': 'financial_statement', 'financial_content': True,
                   'basis_quote': 'balance sheet and income statement', 'rationale': 'The saved text contains statement sections.'}]}
        file = self.file('classification.json', result)
        completed = self.ok('complete', job['id'], '--worker', 'intake-worker', '--expected-attempt', job['attempts'], '--result', file)
        self.assertEqual(completed['status'], 'completed')
        self.assertEqual(self.ok('complete', job['id'], '--worker', 'intake-worker', '--expected-attempt', job['attempts'], '--result', file), completed)
        history = self.ok('source-classification', 'statement')
        self.assertTrue(history[0]['financial_content']); self.assertFalse(history[0]['inputs_verified'])
        self.assertEqual(self.ok('source-classification', 'statement', '--as-of', '2026-10-01T10:01:00+09:00'), [])
        self.assertEqual(self.ok('intake')['selected'], [])
        status = self.ok('status')
        self.assertEqual(status['theses'], 0); self.assertEqual(status['sources'], 1)
        self.assertEqual(status['questions'], {})

    def test_capacity_cli_reports_synthetic_measurements_without_claiming_company_limit(self):
        result = self.ok('capacity', ROOT / 'examples/work-measurements.json')
        self.assertEqual(result['measurement_mode'], 'synthetic_only')
        self.assertIsNone(result['company_upper_bound'])
        self.assertEqual(result['capacity_status'], 'not_estimated')
        self.assertNotIn('proposed_action', result)
        self.assertEqual(self.ok('status')['companies'], 0)


if __name__ == '__main__': unittest.main()
