"""File-only CLI operations must not create or depend on a mutable database."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from ir_agent.cli import main
from ir_agent.store import Store
from test_contacts import row

ROOT = Path(__file__).resolve().parents[1]
NOW = '2026-10-15T12:30:00+00:00'


@contextmanager
def current_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class PureCliDatabaseBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.database = self.directory / 'state.sqlite3'
        self.catalog = self.directory / 'catalog.csv'
        contact = row()
        with self.catalog.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(contact))
            writer.writeheader()
            writer.writerow(contact)

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with current_directory(self.directory), patch('ir_agent.cli.now_iso', return_value=NOW), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([str(arg) for arg in args])
        return code, stdout.getvalue(), stderr.getvalue()

    def file_commands(self, replacement=None):
        def example(name):
            return replacement if replacement is not None else ROOT / 'examples' / name
        return [
            ('value', example('unweighted-valuation.json'), '--price', '100'),
            ('cycle-margin', example('cyclical-margin.synthetic.json')),
            ('decision', example('decision.json')),
            ('ir-plan', example('ir-plan.json')),
            ('information-value', example('information-value.json')),
            ('screen', example('screening.json')),
            ('capacity', example('work-measurements.json')),
            ('stable-reinvestment', example('stable-reinvestment.synthetic.json')),
            ('model-inputs', example('model-input-review.json')),
            ('score-probabilities', example('probability-scoring.json')),
            ('normalize-quote', example('quote-source.json')),
            ('normalize-facts', example('disclosed-facts.json')),
            ('observations', 'summarize', example('ir-observations.json'), '--as-of', NOW),
        ]

    def test_all_file_routes_calculate_without_store_or_default_database(self):
        commands = self.file_commands() + [('contacts', 'import', self.catalog, '--dry-run')]
        for command in commands:
            with self.subTest(command=command[0:2]), \
                    patch('ir_agent.cli.Store', side_effect=AssertionError('Store must not open')) as store:
                code, stdout, stderr = self.invoke(*command)
                self.assertEqual(code, 0, stderr)
                self.assertEqual(stderr, '')
                self.assertTrue(json.loads(stdout))
                store.assert_not_called()
                self.assertFalse((self.directory / 'data').exists())

    def test_file_validation_errors_do_not_open_or_create_database(self):
        invalid = self.directory / 'invalid.json'
        invalid.write_text('{"ambiguous": 1, "ambiguous": 2}')
        for command in self.file_commands(invalid):
            with self.subTest(command=command[0:2]), \
                    patch('ir_agent.cli.Store', side_effect=AssertionError('No Store even for bad file')) as store:
                code, stdout, stderr = self.invoke(*command)
                self.assertEqual(code, 1)
                self.assertEqual(stdout, '')
                self.assertIn('Duplicate JSON key', stderr)
                self.assertNotIn('Traceback', stderr)
                store.assert_not_called()
                self.assertFalse((self.directory / 'data').exists())
        with patch('ir_agent.cli.Store', side_effect=AssertionError('No Store for dry-run errors')):
            code, stdout, stderr = self.invoke('contacts', 'import', self.directory / 'missing.csv', '--dry-run')
        self.assertEqual(code, 1)
        self.assertEqual(stdout, '')
        self.assertTrue(stderr.startswith('ir-agent: '))
        self.assertFalse((self.directory / 'data').exists())

    def test_valid_normalization_ignores_impossible_or_non_sqlite_db_paths(self):
        blocker = self.directory / 'blocked-parent'
        blocker.write_bytes(b'explicit synthetic parent-file blocker')
        non_sqlite = self.directory / 'existing.txt'
        non_sqlite.write_bytes(b'preserve this non-database file')
        before = sha256(non_sqlite.read_bytes()).hexdigest()
        for path in [blocker / 'db.sqlite3', non_sqlite]:
            with self.subTest(path=path), patch('ir_agent.cli.Store') as store:
                code, stdout, stderr = self.invoke('--db', path, 'normalize-facts', ROOT / 'examples/disclosed-facts.json')
                self.assertEqual(code, 0, stderr)
                result = json.loads(stdout)
                self.assertEqual(len(result['sources']), 2)
                self.assertEqual(result['sources'][1]['retrieved_at'], NOW)
                self.assertFalse(result['sources'][1]['metadata']['financial_inputs_verified'])
                store.assert_not_called()
        self.assertEqual(sha256(non_sqlite.read_bytes()).hexdigest(), before)
        self.assertFalse((self.directory / 'data').exists())

    def test_observation_file_and_contacts_dry_run_do_not_bypass_saved_routes(self):
        code, stdout, stderr = self.invoke('--db', self.database, 'contacts', 'import', self.catalog)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(json.loads(stdout)['status'], 'imported')
        self.assertTrue(self.database.exists())
        code, stdout, stderr = self.invoke('--db', self.database, 'observations', 'summarize', '--as-of', NOW)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(json.loads(stdout)['record_count'], 0)
        with sqlite3.connect(self.database.as_uri() + '?mode=ro', uri=True) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM companies').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM ir_observation_versions').fetchone()[0], 0)

    def test_saved_status_PIT_and_registry_routes_still_require_database(self):
        commands = [
            ('status',),
            ('thesis-view', 'synthetic', '--as-of', NOW, '--knowledge-at', NOW, '--mode', 'pit'),
            ('decision-review', 'show', 'review-id'),
            ('quote', 'from-source', 'saved-source'),
            ('observations', 'summarize', '--as-of', NOW),
            ('observations', 'show', 'saved-observation'),
            ('contacts', 'import', self.catalog),
        ]
        for command in commands:
            with self.subTest(command=command), \
                    patch('ir_agent.cli.Store', side_effect=OSError('synthetic unavailable DB')) as store:
                code, stdout, stderr = self.invoke('--db', self.database, *command)
                self.assertEqual(code, 1)
                self.assertEqual(stdout, '')
                self.assertIn('synthetic unavailable DB', stderr)
                store.assert_called_once_with(str(self.database))

    def test_database_needed_success_and_input_failure_close_the_store(self):
        for command in [('status',), ('ingest', self.directory / 'missing.json')]:
            created = []
            def open_store(path):
                store = Store(path)
                created.append(store)
                return store
            with self.subTest(command=command), patch('ir_agent.cli.Store', side_effect=open_store):
                code, stdout, stderr = self.invoke('--db', self.database, *command)
            self.assertEqual(len(created), 1)
            if command[0] == 'status':
                self.assertEqual(code, 0, stderr)
                self.assertEqual(json.loads(stdout)['companies'], 0)
            else:
                self.assertEqual(code, 1)
                self.assertEqual(stdout, '')
                self.assertTrue(stderr.startswith('ir-agent: '))
            with self.assertRaises(sqlite3.ProgrammingError):
                created[0].connection.execute('SELECT 1')

    def test_database_run_error_remains_normal_and_closes_once(self):
        store = Mock()
        with patch('ir_agent.cli.Store', return_value=store), \
                patch('ir_agent.cli.run', side_effect=ValueError('synthetic saved-operation failure')):
            code, stdout, stderr = self.invoke('--db', self.database, 'status')
        self.assertEqual(code, 1)
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'ir-agent: synthetic saved-operation failure\n')
        store.close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
