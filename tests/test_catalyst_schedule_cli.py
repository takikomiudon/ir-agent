"""The catalyst report must read its database without creating or migrating it."""
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


spec = importlib.util.spec_from_file_location(
    'report_catalyst_schedule',
    Path(__file__).resolve().parents[1] / 'scripts/report_catalyst_schedule.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


class CatalystScheduleCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / 'ledger.sqlite3'

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(script, 'now_iso', return_value='2026-10-15T05:00:00+00:00'), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = script.main(['--db', str(self.path), *map(str, arguments)])
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def empty_database(self):
        connection = sqlite3.connect(self.path)
        connection.execute('CREATE TABLE unrelated (id TEXT)')
        connection.commit()
        connection.close()

    def test_missing_database_is_not_created(self):
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(stdout, '')
        self.assertIn('error:', stderr)
        self.assertFalse(self.path.exists())

    def test_empty_input_does_not_certify_no_catalysts_or_migrate_unknown_schema(self):
        self.empty_database()
        before = sha256(self.path.read_bytes()).hexdigest()
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result['status'], 'schedule_monitor_only')
        self.assertEqual(result['events'], [])
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [('unrelated',)])
        finally:
            connection.close()

    def test_display_window_requires_both_bounds_before_opening_database(self):
        code, stdout, stderr = self.invoke('--date-from', '2026-11-01')
        self.assertEqual(code, 2)
        self.assertEqual(stdout, '')
        self.assertIn('Provide both', stderr)
        self.assertFalse(self.path.exists())

    def test_runtime_clock_cannot_be_replaced_by_date_only_or_future_cutoff(self):
        self.empty_database()
        before = self.path.read_bytes()
        for cutoff in ['2026-10-15', '2026-10-16T05:00:00+00:00']:
            with self.subTest(cutoff=cutoff):
                code, stdout, stderr = self.invoke('--as-of', cutoff)
                self.assertEqual(code, 2)
                self.assertEqual(stdout, '')
                self.assertIn('error:', stderr)
                self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
