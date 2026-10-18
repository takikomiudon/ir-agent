"""Freeze explicitly synthetic predictions through separate CLI invocations."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main
from ir_agent.models import json_text
from test_observation_store import design, fixture


def digest(value):
    return sha256(json_text(value).encode()).hexdigest()


class PredictionCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.db = self.directory / 'predictions.sqlite3'

    def invoke(self, *args, now='2026-10-01T10:01:00+09:00'):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch('ir_agent.cli.now_iso', return_value=now), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', str(self.db), *map(str, args)])
        return code, stdout.getvalue(), stderr.getvalue()

    def ok(self, *args, **kwargs):
        code, stdout, stderr = self.invoke(*args, **kwargs)
        self.assertEqual(code, 0, stderr); self.assertEqual(stderr, '')
        return json.loads(stdout)

    def file(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value))
        return path

    def request(self):
        record = design(synthetic=True)
        saved = self.ok('observations', 'register', self.file('design.json', record))
        model = {'synthetic': True, 'description': 'Protocol fixture; no trained model'}
        training = {'synthetic': True, 'description': 'No real training observations'}
        signals = list(record['signals'])
        states = list(record['hypothesis']['states'])
        # Explicit boundary fixture: all probability mass on the first label.
        # This is not an estimate or a default provided by the registry.
        likelihoods = {signal: {state: '1' if signal == signals[0] else '0' for state in states}
                       for signal in signals}
        return record, {
            'id': 'synthetic-candidate', 'synthetic': True,
            'observation_ref': {'id': record['id'], 'version': saved['version'],
                                'snapshot_sha256': digest(saved['record']),
                                'design_sha256': saved['design_sha256']},
            'model_ref': {'id': 'synthetic-model', 'version': 1, 'trained_at': '2026-10-01T09:00:00+09:00',
                          'manifest': model, 'manifest_sha256': digest(model)},
            'training_ref': {'information_cutoff': '2026-09-30T23:59:00+09:00',
                             'manifest': training, 'manifest_sha256': digest(training)},
            'created_at': '2026-10-01T10:01:30+09:00', 'likelihoods': likelihoods,
            'provenance': {'kind': 'synthetic_example', 'reference': 'CLI protocol fixture',
                           'rationale': 'Invented values only to check immutable persistence.'}}

    def test_registration_readback_visibility_and_retry_after_observation_progress(self):
        record, value = self.request()
        path = self.file('prediction.json', value)
        now = '2026-10-01T10:01:45+09:00'
        saved = self.ok('predictions', 'register', path, now=now)
        self.assertEqual(saved['status'], 'candidate_prediction_only')
        self.assertFalse(saved['verification']['calibration_verified'])
        self.assertFalse(saved['verification']['training_provenance_verified'])
        self.assertEqual(self.ok('predictions', 'show', value['id'])['request'], value)
        self.assertEqual(self.ok('predictions', 'list', '--as-of', value['created_at']), [])
        self.assertEqual(len(self.ok('predictions', 'list', '--as-of', now)), 1)
        record['dispatch'] = fixture()['dispatch']
        later = '2026-10-01T10:02:00+09:00'
        self.ok('observations', 'append', self.file('sent.json', record), '--expected-version', 1, now=later)
        retried = self.ok('predictions', 'register', path, now=later)
        self.assertFalse(retried['added'])
        self.assertEqual(retried['first_saved_at'], saved['first_saved_at'])
        self.assertEqual(self.ok('status')['signal_predictions'], 1)
        self.assertEqual(self.ok('status')['theses'], 0)

    def test_manifest_hash_mismatch_fails_normally_without_partial_registration(self):
        _, value = self.request()
        changed = deepcopy(value)
        changed['model_ref']['manifest']['description'] = 'Changed after its commitment'
        code, stdout, stderr = self.invoke('predictions', 'register', self.file('changed.json', changed),
                                          now='2026-10-01T10:01:45+09:00')
        self.assertEqual(code, 1); self.assertEqual(stdout, '')
        self.assertNotIn('Traceback', stderr)
        self.assertEqual(self.ok('predictions', 'list'), [])
        self.assertEqual(self.ok('status')['signal_predictions'], 0)


if __name__ == '__main__': unittest.main()
