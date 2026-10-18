"""Read-only script boundaries use temporary databases and declared clocks."""
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('report_research_monitoring',
    Path(__file__).resolve().parents[1] / 'scripts/report_research_monitoring.py')
script = importlib.util.module_from_spec(spec); spec.loader.exec_module(script)


class ResearchMonitoringCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.database = self.root / 'ledger.sqlite3'
        self.cases = self.root / 'cases.json'; self.cases.write_text('[]', encoding='utf-8')

    def invoke(self, *extra):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(script, 'now_iso', return_value='2026-10-15T11:00:00Z'), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = script.main(['--db', str(self.database), '--cases', str(self.cases),
                                    '--research-root', str(self.root), *extra])
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def database_file(self):
        connection = sqlite3.connect(self.database)
        connection.execute('CREATE TABLE unrelated(id TEXT)'); connection.commit(); connection.close()

    def test_missing_database_is_not_created(self):
        code, stdout, _ = self.invoke()
        self.assertEqual(code, 2); self.assertEqual(stdout, '')
        self.assertFalse(self.database.exists())

    def test_unknown_schema_and_empty_population_leave_database_bytes_unchanged(self):
        self.database_file(); before = sha256(self.database.read_bytes()).hexdigest()
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result['coverage']['case_count'], 0)
        self.assertEqual(result['sections']['sources']['status'], 'unknown')
        self.assertEqual(result['jobs_created'], 0)
        self.assertEqual(sha256(self.database.read_bytes()).hexdigest(), before)

    def test_duplicate_nonfinite_or_approval_input_fail_normally(self):
        self.database_file(); before = self.database.read_bytes()
        for raw in ('[{"id":"one","id":"two"}]', '[NaN]', '[{"approved":true}]'):
            self.cases.write_text(raw, encoding='utf-8')
            with self.subTest(raw=raw):
                code, stdout, stderr = self.invoke()
                self.assertEqual(code, 2); self.assertEqual(stdout, '')
                self.assertIn('error:', stderr)
                self.assertEqual(self.database.read_bytes(), before)

    def test_future_cutoff_date_only_and_caller_clock_option_are_rejected(self):
        self.database_file()
        for args in (['--as-of', '2026-10-16T00:00:00Z'], ['--as-of', '2026-10-15'], ['--now', '2026-10-16T00:00:00Z']):
            with self.subTest(args=args):
                code, stdout, _ = self.invoke(*args)
                self.assertEqual(code, 2); self.assertEqual(stdout, '')


if __name__ == '__main__':
    unittest.main()
