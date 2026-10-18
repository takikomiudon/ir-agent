"""Evaluation plans persist across CLI calls without becoming approved rules."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main


def draft():
    return {'id': 'synthetic-protocol-draft', 'version': 1,
            'recorded_at': '2026-10-15T00:00:00+00:00', 'recorded_by': 'Synthetic CLI test',
            'evaluation_task': None,
            'cohort': {key: None for key in ('id', 'design_version', 'definition_sha256', 'state_timing',
                'target_period', 'question_type', 'states', 'signals', 'synthetic')},
            'model_refs': [], 'source_refs': [],
            'rules': {key: None for key in ('inclusion', 'state', 'signal', 'information_separation',
                'no_response', 'external_change', 'correction', 'group_time', 'prediction_selection', 'population_output')}}


class EvaluationProtocolCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name); self.path = self.directory/'protocols.sqlite3'

    def invoke(self, *arguments, now='2026-10-15T00:05:00+00:00'):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch('ir_agent.cli.now_iso', return_value=now), redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = main(['--db', str(self.path), *map(str, arguments)])
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def ok(self, *arguments, **kwargs):
        code, stdout, stderr = self.invoke(*arguments, **kwargs)
        self.assertEqual(code, 0, stderr)
        return json.loads(stdout)

    def register(self, request, previous, **kwargs):
        path = self.directory/('version-'+str(request['version'])+'.json')
        path.write_text(json.dumps(request))
        return self.ok('evaluation-protocol', 'register', path,
                       '--expected-previous-version', previous, **kwargs)

    def test_versions_replay_and_status_survive_separate_cli_invocations(self):
        original = draft(); first = self.register(original, 0)
        self.assertEqual(first['status'], 'protocol_commitment_only')
        self.assertTrue(first['added']); self.assertEqual(first['request'], original)
        later = deepcopy(original); later['version'] = 2
        later['recorded_at'] = '2026-10-15T00:06:00+00:00'
        later['recorded_by'] = 'Another synthetic fixture editor'
        self.register(later, 1, now='2026-10-15T00:06:00+00:00')
        replay = self.register(original, 0, now='2026-10-15T00:07:00+00:00')
        self.assertFalse(replay['added']); self.assertEqual(replay['first_saved_at'], first['first_saved_at'])
        self.assertEqual(replay['request'], original)
        self.assertEqual(self.ok('evaluation-protocol', 'show', original['id'])['request'], later)
        self.assertEqual(self.ok('evaluation-protocol', 'show', original['id'], '--version', 1)['request'], original)
        self.assertEqual(len(self.ok('evaluation-protocol', 'history', original['id'])), 2)
        status = self.ok('status')
        self.assertEqual(status['evaluation_protocol_versions'], 2)
        self.assertEqual(status['theses'], 0); self.assertEqual(status['signal_predictions'], 0)

    def test_changed_content_future_clock_and_forged_approval_do_not_add_versions(self):
        original = draft(); self.register(original, 0)
        changes = []
        changed = deepcopy(original); changed['recorded_by'] = 'Different'; changes.append((changed, 0))
        skipped = deepcopy(original); skipped['version'] = 3; changes.append((skipped, 2))
        approved = deepcopy(original); approved['independent'] = True; changes.append((approved, 0))
        backfilled = deepcopy(original); backfilled['first_saved_at'] = original['recorded_at']; changes.append((backfilled, 0))
        future = deepcopy(original); future['version'] = 2
        future['recorded_at'] = '2026-10-16T00:00:00+00:00'; changes.append((future, 1))
        path = self.directory/'invalid.json'
        for request, previous in changes:
            with self.subTest(request=request):
                path.write_text(json.dumps(request))
                code, stdout, stderr = self.invoke('evaluation-protocol', 'register', path,
                                                   '--expected-previous-version', previous)
                self.assertEqual(code, 1); self.assertTrue(stderr.startswith('ir-agent: '), stderr)
        history = self.ok('evaluation-protocol', 'history', original['id'])
        self.assertEqual(len(history), 1); self.assertEqual(history[0]['request'], original)

    def test_explicit_cas_and_trusted_internal_clock_are_required(self):
        path = self.directory/'draft.json'; path.write_text(json.dumps(draft()))
        code, stdout, stderr = self.invoke('evaluation-protocol', 'register', path)
        self.assertEqual(code, 2); self.assertIn('--expected-previous-version', stderr)
        code, stdout, stderr = self.invoke('evaluation-protocol', 'register', path,
            '--expected-previous-version', 0, '--now', '2026-10-01T00:00:00Z')
        self.assertEqual(code, 2); self.assertIn('unrecognized arguments', stderr)


if __name__ == '__main__':
    unittest.main()
