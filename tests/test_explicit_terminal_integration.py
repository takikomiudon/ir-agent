"""Explicit terminal FCFF retains provenance and precommitted IR boundaries."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from decimal import Decimal, localcontext
import io
import json
from pathlib import Path
import unittest

from ir_agent.cli import main
from ir_agent.decision import _flatten, evaluate_ir_plan
from ir_agent.model_inputs import audit_model_inputs
from ir_agent.stable_reinvestment import calculate_stable_reinvestment
from test_decision import plan

ROOT = Path(__file__).resolve().parents[1]


def convert(valuation):
    result = deepcopy(valuation)
    with localcontext() as context:
        context.prec = 80
        for scenario in result['scenarios']:
            fair = Decimal(scenario['inputs']['eps_jpy']) * Decimal(scenario['inputs']['pe'])
            scenario.update(method='dcf_explicit_terminal', inputs={
                'fcf_jpy': ['0'], 'discount_rate': '.1', 'terminal_growth_rate': '0',
                'cash_jpy': '0', 'debt_jpy': '0', 'shares_outstanding': '1',
                'terminal_fcff_jpy': str(fair * Decimal('.11'))})
    return result


def explicit_plan():
    result = plan()
    result['thesis']['valuation'] = convert(result['thesis']['valuation'])
    for branch in result['question']['branches']:
        if 'valuation' in branch:
            branch['valuation'] = convert(branch['valuation'])
    result['question']['parameter_paths'] = ['scenarios.base.inputs.terminal_fcff_jpy']
    return result


class ExplicitTerminalIntegrationTests(unittest.TestCase):
    def test_synthetic_bridge_converts_millions_to_jpy_and_keeps_adoption_unresolved(self):
        request = json.loads((ROOT / 'examples/stable-reinvestment.synthetic.json').read_bytes())
        intermediate = calculate_stable_reinvestment(request)
        self.assertEqual(intermediate['arithmetic']['basis']['currency'], 'JPY')
        self.assertEqual(intermediate['arithmetic']['basis']['amount_unit'], 'millions')
        explicit = json.loads((ROOT / 'examples/valuation-explicit-terminal.synthetic.json').read_bytes())
        self.assertEqual(Decimal(intermediate['arithmetic']['fcff']) * Decimal('1000000'),
                         Decimal(explicit['scenarios'][0]['inputs']['terminal_fcff_jpy']))
        self.assertEqual(intermediate['adoption'], 'unresolved')
        self.assertEqual(set(intermediate['verification'].values()), {'unverified'})

    def test_terminal_path_is_a_required_audit_input_without_imputing_probability(self):
        valuation = json.loads((ROOT / 'examples/valuation-explicit-terminal.synthetic.json').read_bytes())
        values = valuation['scenarios'][0]['inputs']
        source = {'id': 'synthetic-terminal-values', 'company_id': 'synthetic:terminal',
                  'title': 'Synthetic arithmetic inputs, not issuer information',
                  'url': 'https://example.invalid/synthetic-terminal', 'source_type': 'public_disclosure',
                  'published_at': None, 'retrieved_at': '2026-10-14T00:00:00+00:00',
                  'content': 'Fictional values for an integration test.',
                  'metadata': {'synthetic': True, 'values': deepcopy(values)}}
        provenance = {}
        for path in _flatten(valuation):
            if path.endswith('.method') or path.endswith('.probability'):
                continue
            suffix = path.split('.inputs.', 1)[1].split('.')
            value_path = ['metadata', 'values', suffix[0]] + [int(x) for x in suffix[1:]]
            provenance[path] = {'kind': 'synthetic_example', 'reference': 'Explicit fictional fixture',
                'rationale': 'Source-number agreement is separate from financial meaning.',
                'recorded_at': '2026-10-14T01:00:00+00:00', 'author': 'Synthetic test',
                'source_id': source['id'], 'value_path': value_path, 'unit': 'Declared fixture unit',
                'period': 'Declared fixture period'}
        terminal = 'scenarios.synthetic-base.inputs.terminal_fcff_jpy'
        request = {'company_id': source['company_id'], 'as_of': '2026-10-15T00:00:00+00:00',
                   'valuation': valuation, 'sources': [source], 'synthetic': True, 'provenance': provenance}
        before = deepcopy(request)
        result = audit_model_inputs(request)
        self.assertIn(terminal, result['required_paths'])
        self.assertEqual(next(row for row in result['inputs'] if row['path'] == terminal)['source_value'], '80000000')
        self.assertEqual(result['unset_probability_paths'], ['scenarios.synthetic-base.probability'])
        self.assertFalse(result['expected_value_available'])
        self.assertFalse(result['financial_inputs_verified'])
        self.assertTrue(result['meaning_review_required'])
        self.assertEqual(request, before)
        del request['provenance'][terminal]
        self.assertIn(terminal, audit_model_inputs(request)['missing_paths'])

    def test_explicit_terminal_branch_remains_precommitted(self):
        request = explicit_plan()
        before = deepcopy(request)
        result = evaluate_ir_plan(request)
        self.assertEqual(result['question_value'], 'decision_distinguishing')
        self.assertEqual(set(result['outcomes'][0]['parameter_changes']),
                         {'scenarios.base.inputs.terminal_fcff_jpy'})
        self.assertEqual(request, before)

    def test_terminal_answer_cannot_silently_change_discount_rate(self):
        request = explicit_plan()
        request['question']['branches'][0]['valuation']['scenarios'][1]['inputs']['discount_rate'] = '.08'
        result = evaluate_ir_plan(request)
        self.assertEqual(result['question_value'], 'needs_review')
        self.assertTrue(any('unmapped_parameter_change' in row.get('reason_codes', [])
                            for row in result['outcomes']))

    def test_old_dcf_question_cannot_add_a_new_terminal_path(self):
        request = explicit_plan()
        for scenario in request['thesis']['valuation']['scenarios']:
            scenario['method'] = 'dcf'
            del scenario['inputs']['terminal_fcff_jpy']
        with self.assertRaisesRegex(ValueError, 'existing valuation inputs'):
            evaluate_ir_plan(request)

    def test_cli_explicit_terminal_does_not_grow_it_or_create_expected_value(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', ':memory:', 'value',
                         str(ROOT / 'examples/valuation-explicit-terminal.synthetic.json'), '--price', '100'])
        self.assertEqual(code, 0, stderr.getvalue())
        result = json.loads(stdout.getvalue())
        self.assertIsNone(result['expected_value_jpy'])
        self.assertEqual(result['scenarios'][0]['fair_value_jpy'], '91.82')
        self.assertEqual(Decimal(result['scenarios'][0]['terminal_fcff_jpy']), Decimal('80000000'))
        self.assertEqual(result['scenarios'][0]['forecast_periods'], 1)


if __name__ == '__main__':
    unittest.main()
