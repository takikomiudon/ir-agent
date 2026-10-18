"""Expose annual-margin arithmetic without adopting a normalized profit or model."""
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


class CyclicalMarginCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name); self.db = self.directory/'arithmetic.sqlite3'
        self.request = json.loads((ROOT/'examples/cyclical-margin.synthetic.json').read_text())

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', str(self.db), *map(str, arguments)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_signed_equal_period_average_is_an_unadopted_intermediate(self):
        path = self.directory/'input.json'; path.write_text(json.dumps(self.request))
        code, stdout, stderr = self.invoke('cycle-margin', path)
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result['status'], 'intermediate_only')
        self.assertEqual(result['adoption'], 'unresolved')
        self.assertEqual(result['request'], self.request)
        arithmetic = result['arithmetic']
        self.assertEqual(Decimal(arithmetic['annual_margins'][0]['operating_margin_ratio']), Decimal('-.1'))
        self.assertEqual(Decimal(arithmetic['mean_operating_margin_ratio']), Decimal('.1'))
        self.assertEqual(Decimal(arithmetic['applied_operating_income']), Decimal('20'))
        self.assertEqual(set(result['verification'].values()), {'unverified'})
        code, stdout, stderr = self.invoke('status')
        self.assertEqual(code, 0, stderr)
        status = json.loads(stdout)
        self.assertEqual(status['sources'], 0); self.assertEqual(status['theses'], 0)
        self.assertEqual(status['signal_predictions'], 0); self.assertEqual(status['questions'], {})

    def test_unsupported_methods_and_mixed_or_missing_inputs_are_not_filled(self):
        modifications = [lambda r: r.pop('method'),
                         lambda r: r.update(method='sales_weighted'),
                         lambda r: r['annual_observations'][0]['period'].update(kind='quarter'),
                         lambda r: r['annual_observations'][0].update(operating_income=None),
                         lambda r: r['annual_observations'][0].update(revenue='0'),
                         lambda r: r['annual_observations'][0].update(revenue=100),
                         lambda r: r['annual_observations'][0]['basis'].update(currency='USD')]
        path = self.directory/'invalid.json'
        for modify in modifications:
            request = deepcopy(self.request); modify(request); path.write_text(json.dumps(request))
            with self.subTest(request=request):
                code, stdout, stderr = self.invoke('cycle-margin', path)
                self.assertEqual(code, 1); self.assertEqual(stdout, '')
                self.assertTrue(stderr.startswith('ir-agent: '), stderr)


if __name__ == '__main__':
    unittest.main()
