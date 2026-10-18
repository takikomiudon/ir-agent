"""Receipt-mode envelopes and identity errors cross the JSON CLI boundary."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main
from test_workflow import source


class JobRequestCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name); self.database = self.directory / 'requests.sqlite3'
        self.now = datetime.fromisoformat('2026-10-09T09:55:00+09:00')
        bundle = self.directory / 'bundle.json'
        bundle.write_text(json.dumps({'schema_version': 1,
            'companies': [{'id': 'cli-company', 'name': 'Fictional receipt fixture'}],
            'sources': [source('cli-company', 'public-cli-evidence')]}))
        self.ok('ingest', bundle)
        queued = self.ok('intake', '--as-of', '2026-10-09T10:00:00+09:00')
        self.job_id = queued['selected'][0]['job_id']

    def invoke(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with patch('ir_agent.harness.datetime', wraps=datetime) as clock:
            clock.now.return_value = self.now
            with redirect_stdout(output), redirect_stderr(error):
                code = main(['--db', str(self.database), *map(str, args)])
        return code, output.getvalue(), error.getvalue()

    def ok(self, *args):
        code, output, error = self.invoke(*args)
        self.assertEqual(code, 0, error); self.assertEqual(error, '')
        return json.loads(output)

    def test_claim_and_renew_replays_return_original_metadata(self):
        flags = ['claim', '--worker', 'worker', '--measurement-kind', 'synthetic',
                 '--caller-namespace', 'cli-runner', '--request-id', 'poll-1']
        self.now = datetime.fromisoformat('2026-10-09T10:01:00+09:00')
        first = self.ok(*flags)
        self.assertEqual(first['original_response']['job_id'], self.job_id)
        self.assertTrue(first['current_lease']['valid_now'])
        self.now = datetime.fromisoformat('2026-10-09T10:02:00+09:00')
        repeated = self.ok(*flags)
        self.assertTrue(repeated['replayed'])
        self.assertEqual(repeated['original_response'], first['original_response'])
        renew = ['renew', self.job_id, '--worker', 'worker', '--expected-attempt', first['original_response']['generation'],
                 '--caller-namespace', 'cli-runner', '--request-id', 'extend-1']
        self.now = datetime.fromisoformat('2026-10-09T10:03:00+09:00')
        extended = self.ok(*renew)
        self.now = datetime.fromisoformat('2026-10-09T10:04:00+09:00')
        again = self.ok(*renew)
        self.assertTrue(again['replayed'])
        self.assertEqual(again['original_response'], extended['original_response'])
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM job_request_receipts').fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM job_attempt_events WHERE kind='lease_renewed'").fetchone()[0], 1)

    def test_partial_identity_rejection_leaves_the_job_pending(self):
        self.now = datetime.fromisoformat('2026-10-09T10:01:00+09:00')
        code, output, error = self.invoke('claim', '--worker', 'worker', '--request-id', 'partial')
        self.assertEqual(code, 1); self.assertEqual(output, '')
        self.assertIn('both request_id and caller_namespace', error)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute('SELECT status FROM jobs WHERE id=?', (self.job_id,)).fetchone()[0], 'pending')
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM job_request_receipts').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
