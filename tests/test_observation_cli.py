"""Persisted observation visibility at the JSON CLI boundary."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main
from ir_agent.models import json_text
from test_observation_store import design, fixture


class ObservationCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name); self.db = self.directory / 'observations.sqlite3'

    def call(self, *args, now='2026-10-01T10:01:00+09:00'):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch('ir_agent.cli.now_iso', return_value=now), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', str(self.db), *map(str, args)])
        return code, stdout.getvalue(), stderr.getvalue()

    def ok(self, *args, **kwargs):
        code, stdout, stderr = self.call(*args, **kwargs)
        self.assertEqual(code, 0, stderr); self.assertEqual(stderr, '')
        return json.loads(stdout)

    def file(self, name, value):
        path = self.directory / name; path.write_text(json.dumps(value)); return path

    def test_design_and_append_survive_reopen_without_exposing_later_outcomes(self):
        record = design()
        saved = self.ok('observations', 'register', self.file('design.json', record))
        self.assertEqual(saved['version'], 1)
        self.assertEqual(self.ok('observations', 'summarize', '--as-of', '2026-10-01T10:00:00+09:00')['record_count'], 0)
        record['dispatch'] = fixture()['dispatch']
        self.ok('observations', 'append', self.file('sent.json', record), '--expected-version', 1, now='2026-10-01T10:02:00+09:00')
        record['replies'] = fixture()['replies']
        self.ok('observations', 'append', self.file('reply.json', record), '--expected-version', 2, now='2026-10-02T10:01:00+09:00')
        record['verification'] = fixture()['verification']
        self.ok('observations', 'append', self.file('verified.json', record), '--expected-version', 3, now='2026-11-03T12:00:00+09:00')
        self.assertEqual(len(self.ok('observations', 'show', record['id'])), 4)
        earlier = self.ok('observations', 'summarize', '--as-of', '2026-11-02T16:00:00+09:00')
        later = self.ok('observations', 'summarize', '--as-of', '2026-11-03T12:00:00+09:00')
        self.assertEqual(earlier['eligible_count'], 0)
        self.assertEqual(later['eligible_count'], 1)
        self.assertEqual(later['calibration_status'], 'needs_calibration')
        self.assertEqual(self.ok('status')['questions'], {})

    def test_live_backfilled_sent_record_and_changed_design_fail_normally(self):
        record = design(); record['dispatch'] = fixture()['dispatch']
        code, stdout, stderr = self.call('observations', 'register', self.file('backfilled.json', record), now='2026-10-02T10:00:00+09:00')
        self.assertEqual(code, 1); self.assertEqual(stdout, ''); self.assertNotIn('Traceback', stderr)
        self.ok('observations', 'register', self.file('design.json', design()))
        changed = deepcopy(design()); changed['reply_deadline'] = '2026-10-09T17:00:00+09:00'
        code, stdout, stderr = self.call('observations', 'append', self.file('changed.json', changed), '--expected-version', 1, now='2026-10-01T10:02:00+09:00')
        self.assertEqual(code, 1); self.assertEqual(stdout, ''); self.assertNotIn('Traceback', stderr)
        self.assertEqual(len(self.ok('observations', 'show', changed['id'])), 1)

    def test_safety_correction_survives_reopening_without_rewriting_the_reply(self):
        record = fixture()  # An explicitly synthetic, already adjudicated fixture.
        self.assertTrue(record['synthetic'])
        self.ok('observations', 'register', self.file('synthetic-complete.json', record),
                now='2026-11-03T12:00:00+09:00')
        reply = deepcopy(record['replies'][0])
        before = '2026-11-03T12:00:00+09:00'
        after = '2026-11-04T12:00:00+09:00'
        self.assertEqual(self.ok('observations', 'summarize', '--as-of', before)['eligible_count'], 1)
        record['assessments'] = [{
            'id': 'synthetic-safety-hold', 'target_kind': 'reply', 'target_id': reply['id'],
            'target_snapshot_sha256': sha256(json_text(reply).encode()).hexdigest(),
            'version': 1, 'expected_previous_version': 0, 'recorded_at': after,
            'reviewer': 'Synthetic fixture reviewer',
            'rationale': 'Public basis needs review; original text is not bound in this fixture.',
            'basis': {'public_evidence_references': []},
            'assessment': {'signal': reply['signal'], 'information_status': 'unclear'}}]
        path = self.file('synthetic-hold.json', record)
        saved = self.ok('observations', 'append', path, '--expected-version', 1, now=after)
        self.assertEqual(saved['version'], 2)
        self.assertEqual(saved['record']['assessments'][0]['basis_verification']['status'], 'unverified')
        retried = self.ok('observations', 'append', path, '--expected-version', 1, now=after)
        self.assertEqual(retried['version'], 2)
        self.assertEqual(self.ok('observations', 'summarize', '--as-of', before)['eligible_count'], 1)
        self.assertEqual(self.ok('observations', 'summarize', '--as-of', after)['eligible_count'], 0)
        history = self.ok('observations', 'show', record['id'])
        self.assertEqual(len(history), 2)
        self.assertNotIn('assessments', history[0]['record'])
        self.assertEqual(history[1]['record']['replies'][0], reply)
        self.assertEqual(self.ok('status')['questions'], {})


if __name__ == '__main__': unittest.main()
