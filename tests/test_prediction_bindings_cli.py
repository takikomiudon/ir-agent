"""The evidence report must inspect a ledger without initializing or changing it."""
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

from ir_agent.observation_store import ObservationStore, SCHEMA as OBSERVATION_SCHEMA
from ir_agent.prediction_store import PredictionStore, SCHEMA as PREDICTION_SCHEMA
from test_observation_store import design
from test_prediction_store import candidate, DESIGN_SAVED, SAVED, LATER

spec = importlib.util.spec_from_file_location('report_prediction_bindings',
    Path(__file__).resolve().parents[1] / 'scripts/report_prediction_bindings.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


class PredictionBindingsCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / 'ledger.sqlite3'

    def invoke(self, *arguments, now=LATER):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(script, 'now_iso', return_value=now), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = script.main(['--db', str(self.path), *map(str, arguments)])
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def empty_database(self):
        connection = sqlite3.connect(self.path)
        connection.execute('CREATE TABLE unrelated (id TEXT)')
        connection.commit(); connection.close()

    def test_missing_database_is_not_created_by_report(self):
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 2); self.assertEqual(stdout, '')
        self.assertIn('error:', stderr); self.assertFalse(self.path.exists())

    def test_unknown_schema_stays_unknown_without_migration_or_writes(self):
        self.empty_database(); before = sha256(self.path.read_bytes()).hexdigest()
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result['status'], 'source_binding_report_only')
        self.assertIsNone(result['score']); self.assertIsNone(result['score_request'])
        self.assertEqual(result['observations'], [])
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),
                             [('unrelated',)])
        finally:
            connection.close()

    def test_existing_observation_with_no_bindings_remains_in_population_unscored(self):
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.executescript(OBSERVATION_SCHEMA + PREDICTION_SCHEMA)
        observations = ObservationStore(connection)
        saved = observations.register(design(synthetic=True), DESIGN_SAVED)
        PredictionStore(connection).register(candidate(saved), SAVED)
        connection.close()
        before = sha256(self.path.read_bytes()).hexdigest()
        code, stdout, stderr = self.invoke()
        self.assertEqual(code, 0, stderr)
        report = json.loads(stdout)
        self.assertEqual(len(report['observations']), 1)
        self.assertEqual(len(report['observations'][0]['predictions']), 1)
        self.assertIsNone(report['score_request']); self.assertIsNone(report['score'])
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)

    def test_duplicate_keys_nonfinite_and_caller_approval_are_rejected(self):
        self.empty_database(); before = sha256(self.path.read_bytes()).hexdigest()
        path = self.directory / 'bindings.json'
        for raw in ('[{"observation_ref": {}, "observation_ref": {}}]',
                    '[{"value": NaN}]', '[{"verified": true}]', '{}'):
            with self.subTest(raw=raw):
                path.write_text(raw)
                code, stdout, stderr = self.invoke('--bindings', path)
                self.assertEqual(code, 2); self.assertEqual(stdout, '')
                self.assertIn('error:', stderr)
                self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)

    def test_historical_cutoff_cannot_replace_runtime_or_select_future(self):
        self.empty_database()
        code, stdout, stderr = self.invoke('--as-of', '2026-11-04T18:00:00+09:00')
        self.assertEqual(code, 2); self.assertEqual(stdout, '')
        self.assertIn('error:', stderr)
        code, stdout, stderr = self.invoke('--now', '2026-11-04T18:00:00+09:00')
        self.assertEqual(code, 2); self.assertEqual(stdout, '')
        self.assertIn('unrecognized arguments', stderr)


if __name__ == '__main__':
    unittest.main()
