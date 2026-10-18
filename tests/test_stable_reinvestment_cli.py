"""CLI connection for explicit stable-period reinvestment arithmetic."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest

from ir_agent.cli import main

ROOT = Path(__file__).resolve().parents[1]


class StableReinvestmentCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.request = json.loads((ROOT / 'examples/stable-reinvestment.synthetic.json').read_bytes())

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', ':memory:', *map(str, arguments)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_explicit_next_period_is_not_grown_or_taxed_again(self):
        path = self.directory / 'request.json'
        path.write_text(json.dumps(self.request))
        code, stdout, stderr = self.invoke('stable-reinvestment', path)
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result['status'], 'intermediate_only')
        self.assertEqual(result['adoption'], 'unresolved')
        self.assertEqual(result['request'], self.request)
        self.assertEqual(Decimal(result['arithmetic']['reinvestment_rate']), Decimal('.2'))
        self.assertEqual(Decimal(result['arithmetic']['reinvestment_amount']), Decimal('20'))
        self.assertEqual(Decimal(result['arithmetic']['fcff']), Decimal('80'))
        self.assertEqual(set(result['verification'].values()), {'unverified'})

    def test_pretax_or_base_period_or_percent_inputs_are_not_converted(self):
        modifications = [
            lambda value: value['nopat_next'].update(concept='pretax_operating_income'),
            lambda value: value['nopat_next'].update(timing='current_period'),
            lambda value: value['growth'].update(unit='percent'),
            lambda value: value['roc_new'].update(value=None),
        ]
        path = self.directory / 'invalid.json'
        for modify in modifications:
            value = deepcopy(self.request)
            modify(value)
            path.write_text(json.dumps(value))
            with self.subTest(value=value):
                code, stdout, stderr = self.invoke('stable-reinvestment', path)
                self.assertEqual(code, 1)
                self.assertEqual(stdout, '')
                self.assertTrue(stderr.startswith('ir-agent: '), stderr)


if __name__ == '__main__':
    unittest.main()
