"""The CLI keeps explicit retrospective research separate from strict PIT."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import main


class AvailabilityCliTests(unittest.TestCase):
    def test_explicit_two_clock_view_and_pit_mismatch(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / 'view.sqlite3'

            def call(*args, now=None):
                output, error = io.StringIO(), io.StringIO()
                with patch('ir_agent.harness.datetime', wraps=datetime) as clock:
                    clock.now.return_value = now or datetime.fromisoformat('2026-10-09T18:00:00+09:00')
                    with redirect_stdout(output), redirect_stderr(error):
                        code = main(['--db', str(database), *map(str, args)])
                return code, output.getvalue(), error.getvalue()

            self.assertEqual(call('ingest', root/'examples/demo.json', now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))[0], 0)
            data = json.loads((root/'examples/demo.json').read_text())
            thesis = deepcopy(data['theses'][0]); thesis.update(version=2, recorded_at='2026-10-09T17:20:00+09:00')
            bundle = Path(temporary) / 'later.json'
            bundle.write_text(json.dumps({'schema_version': 1, 'theses': [thesis]}))
            self.assertEqual(call('ingest', bundle)[0], 0)
            flags = ['thesis-view', 'demo-services', '--as-of', '2026-10-09T17:30:00+09:00']
            code, output, error = call(*flags, '--knowledge-at', '2026-10-09T17:30:00+09:00', '--mode', 'pit')
            self.assertEqual(code, 0, error)
            self.assertEqual(json.loads(output)['record']['version'], 1)
            code, output, error = call(*flags, '--knowledge-at', '2026-10-09T18:00:00+09:00', '--mode', 'retrospective')
            self.assertEqual(code, 0, error)
            self.assertEqual(json.loads(output)['record']['version'], 2)
            self.assertEqual(json.loads(output)['temporal_mode'], 'retrospective')
            code, output, error = call(*flags, '--knowledge-at', '2026-10-09T18:00:00+09:00', '--mode', 'pit')
            self.assertEqual(code, 1); self.assertEqual(output, '')
            self.assertIn('PIT requires equal', error)


if __name__ == '__main__':
    unittest.main()
