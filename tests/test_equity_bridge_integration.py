"""Synthetic equity-bridge inputs retain audit and precommitted IR limits.

No live company, author PDF, research ledger, network or external IR is used.
The only SQLite use is the existing CLI's isolated in-memory test database.
"""
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
from ir_agent.valuation import calculate_valuation
from test_decision import plan

ROOT = Path(__file__).resolve().parents[1]
METHOD = 'dcf_explicit_terminal_equity_bridge'
NEW_FIELDS = ('non_operating_assets_jpy', 'minority_interests_jpy')
FORMULA = 'enterprise_value_jpy + cash_jpy + non_operating_assets_jpy - debt_jpy - minority_interests_jpy'


def synthetic_valuation():
    return json.loads((ROOT / 'examples/valuation-equity-bridge.synthetic.json').read_text())


def synthetic_audit_request():
    valuation = synthetic_valuation()
    source = {'id': 'synthetic-equity-bridge-values', 'company_id': 'synthetic:equity-bridge',
        'title': 'Fictional equity-bridge amounts; no issuer or investment assumptions',
        'url': 'https://example.invalid/synthetic-equity-bridge', 'source_type': 'public_disclosure',
        'published_at': None, 'retrieved_at': '2026-10-14T00:00:00+00:00',
        'content': 'Explicit synthetic integration-test numbers only.',
        'metadata': {'synthetic': True, 'values': deepcopy(valuation['scenarios'][0]['inputs'])}}
    provenance = {}
    for path in _flatten(valuation):
        if path.endswith(('.method', '.probability')):
            continue
        suffix = path.split('.inputs.', 1)[1].split('.')
        value_path = ['metadata', 'values', suffix[0]] + [int(index) for index in suffix[1:]]
        provenance[path] = {'kind': 'synthetic_example', 'reference': 'Fictional amount fixture only',
            'rationale': 'Stored number matching does not verify financial meaning.',
            'recorded_at': '2026-10-14T01:00:00+00:00', 'author': 'Synthetic integration fixture',
            'source_id': source['id'], 'value_path': value_path,
            'unit': 'Caller-declared fixture unit, not independently verified',
            'period': 'Caller-declared fixture period, not independently verified'}
    return {'company_id': source['company_id'], 'as_of': '2026-10-15T00:00:00+00:00',
            'valuation': valuation, 'sources': [source], 'synthetic': True, 'provenance': provenance}


def synthetic_bridge_plan(field):
    request = plan()
    with localcontext() as context:
        context.prec = 80
        for scenario in request['thesis']['valuation']['scenarios']:
            original_fair = Decimal(scenario['inputs']['eps_jpy']) * Decimal(scenario['inputs']['pe'])
            # These equal fictional bridge amounts cancel, retaining the old
            # synthetic scenario values without introducing financial defaults.
            scenario.update(method=METHOD, inputs={'fcf_jpy': ['0'], 'discount_rate': '.1',
                'terminal_growth_rate': '0', 'cash_jpy': '0', 'debt_jpy': '0', 'shares_outstanding': '1',
                'terminal_fcff_jpy': str(original_fair * Decimal('.11')),
                'non_operating_assets_jpy': '10', 'minority_interests_jpy': '10'})
    question = request['question']
    question.update(id='synthetic-equity-bridge-' + field, topic='Synthetic bridge amount',
        question='Fictional precommitted bridge-input comparison; not an actual IR message.',
        target_parameter=field, parameter_paths=['scenarios.base.inputs.' + field])
    for branch in question['branches']:
        if branch['action'] == 'unresolved':
            continue
        branch['valuation'] = deepcopy(request['thesis']['valuation'])
        base = next(s for s in branch['valuation']['scenarios'] if s['name'] == 'base')
        favorable = branch['id'] != 'persistent'
        base['inputs'][field] = ('20' if favorable else '0') if field == 'non_operating_assets_jpy' else ('0' if favorable else '20')
    for source in request['sources']:
        source.setdefault('metadata', {})['synthetic'] = True
    return request


class EquityBridgeIntegrationTests(unittest.TestCase):
    def test_both_new_canonical_inputs_are_audited_without_verifying_meaning_or_probability(self):
        request = synthetic_audit_request(); before = deepcopy(request)
        result = audit_model_inputs(request)
        rows = {row['path']: row for row in result['inputs']}
        scenario_name = request['valuation']['scenarios'][0]['name']
        for field, value in (('non_operating_assets_jpy', '20000000'), ('minority_interests_jpy', '10000000')):
            path = 'scenarios.' + scenario_name + '.inputs.' + field
            self.assertIn(path, result['required_paths'])
            self.assertEqual(rows[path]['source_value'], value)
            self.assertEqual(rows[path]['status'], 'synthetic_example')
            self.assertEqual(rows[path]['meaning_review_status'], 'unreviewed')
            self.assertIn('definition_not_verified', rows[path]['meaning_checks'])
        self.assertEqual(result['missing_paths'], [])
        self.assertEqual(result['unset_probability_paths'], ['scenarios.' + scenario_name + '.probability'])
        self.assertFalse(result['expected_value_available'])
        self.assertFalse(result['financial_inputs_verified']); self.assertTrue(result['meaning_review_required'])
        self.assertEqual(request, before)

    def test_each_new_input_detects_missing_provenance_and_saved_value_mismatch(self):
        for field in NEW_FIELDS:
            scenario_name = synthetic_valuation()['scenarios'][0]['name']
            path = 'scenarios.' + scenario_name + '.inputs.' + field
            missing = synthetic_audit_request(); del missing['provenance'][path]
            mismatch = synthetic_audit_request(); mismatch['sources'][0]['metadata']['values'][field] = '1'
            with self.subTest(field=field, damage='missing'):
                result = audit_model_inputs(missing)
                self.assertIn(path, result['missing_paths']); self.assertEqual(result['status'], 'needs_review')
            with self.subTest(field=field, damage='mismatch'):
                result = audit_model_inputs(mismatch)
                row = next(item for item in result['inputs'] if item['path'] == path)
                self.assertIn('source_value_mismatch', row['reason_codes'])
                self.assertEqual(row['status'], 'needs_review')
                self.assertFalse(result['financial_inputs_verified'])

    def test_precommitted_nonoperating_asset_change_is_the_only_applied_parameter(self):
        request = synthetic_bridge_plan('non_operating_assets_jpy'); before = deepcopy(request)
        result = evaluate_ir_plan(request)
        self.assertEqual(result['question_value'], 'decision_distinguishing')
        self.assertEqual([item['proposed_action'] for item in result['outcomes']], ['buy_review', 'watch', 'unresolved'])
        path = 'scenarios.base.inputs.non_operating_assets_jpy'
        self.assertTrue(all(item['parameter_changes'] == [path] for item in result['outcomes'][:2]))
        self.assertEqual(result['outcomes'][-1]['parameter_changes'], [])
        self.assertEqual(request, before)

    def test_precommitted_minority_change_is_the_only_applied_parameter(self):
        request = synthetic_bridge_plan('minority_interests_jpy'); before = deepcopy(request)
        result = evaluate_ir_plan(request)
        self.assertEqual(result['question_value'], 'decision_distinguishing')
        self.assertEqual([item['proposed_action'] for item in result['outcomes']], ['buy_review', 'watch', 'unresolved'])
        path = 'scenarios.base.inputs.minority_interests_jpy'
        self.assertTrue(all(item['parameter_changes'] == [path] for item in result['outcomes'][:2]))
        self.assertEqual(result['outcomes'][-1]['parameter_changes'], [])
        self.assertEqual(request, before)

    def test_unmapped_discount_or_companion_bridge_input_holds_branch(self):
        for field, bad in (('discount_rate', '.08'), ('minority_interests_jpy', '11')):
            request = synthetic_bridge_plan('non_operating_assets_jpy')
            base = next(s for s in request['question']['branches'][0]['valuation']['scenarios'] if s['name'] == 'base')
            base['inputs'][field] = bad
            result = evaluate_ir_plan(request); first = result['outcomes'][0]
            with self.subTest(field=field):
                self.assertEqual(result['question_value'], 'needs_review')
                self.assertEqual(first['proposed_action'], 'unresolved')
                self.assertIn('unmapped_parameter_change', first['reason_codes'])
                self.assertEqual(first['unmapped_parameters'], ['scenarios.base.inputs.' + field])

    def test_old_baseline_cannot_add_either_new_allowed_path_after_question(self):
        for field in NEW_FIELDS:
            request = synthetic_bridge_plan(field)
            for scenario in request['thesis']['valuation']['scenarios']:
                scenario['method'] = 'dcf_explicit_terminal'
                for key in NEW_FIELDS: del scenario['inputs'][key]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'existing valuation inputs'):
                evaluate_ir_plan(request)

    def test_legacy_dcf_ignores_unconsumed_fields_and_old_explicit_remains_strict_seven(self):
        old = synthetic_valuation()
        old['scenarios'][0]['method'] = 'dcf'
        for field in NEW_FIELDS: del old['scenarios'][0]['inputs'][field]
        before = calculate_valuation(old, '100')
        with_unused = deepcopy(old)
        with_unused['scenarios'][0]['inputs'].update(non_operating_assets_jpy='20000000', minority_interests_jpy='10000000')
        self.assertEqual(calculate_valuation(with_unused, '100'), before)
        self.assertEqual(_flatten(with_unused), _flatten(old))
        strict = synthetic_valuation(); strict['scenarios'][0]['method'] = 'dcf_explicit_terminal'
        with self.assertRaises(ValueError): calculate_valuation(strict, '100')
        for field in NEW_FIELDS: del strict['scenarios'][0]['inputs'][field]
        old_result = calculate_valuation(strict, '100')['scenarios'][0]
        self.assertEqual(old_result['fair_value_jpy'], '91.82')
        self.assertNotIn('equity_bridge_formula', old_result)
        self.assertTrue(all(field not in old_result for field in NEW_FIELDS))

    def test_cli_new_example_reports_9282_and_full_bridge_without_expected_value(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', ':memory:', 'value',
                str(ROOT / 'examples/valuation-equity-bridge.synthetic.json'), '--price', '100'])
        self.assertEqual(code, 0, stderr.getvalue())
        result = json.loads(stdout.getvalue()); scenario = result['scenarios'][0]
        self.assertIsNone(result['expected_value_jpy']); self.assertIsNone(result['expected_upside_pct'])
        self.assertEqual(result['aggregation'], 'unweighted')
        self.assertEqual(scenario['method'], METHOD); self.assertEqual(scenario['fair_value_jpy'], '92.82')
        self.assertEqual(Decimal(scenario['terminal_fcff_jpy']), Decimal('80000000'))
        self.assertEqual(scenario['forecast_periods'], 1)
        for field in ('terminal_value_jpy', 'present_value_of_terminal_value_jpy', 'present_value_of_forecast_fcf_jpy'):
            self.assertIn(field, scenario)
        self.assertEqual({key: scenario[key] for key in ('cash_jpy', 'non_operating_assets_jpy', 'debt_jpy', 'minority_interests_jpy')},
            {'cash_jpy': '0.00', 'non_operating_assets_jpy': '20000000.00', 'debt_jpy': '0.00', 'minority_interests_jpy': '10000000.00'})
        self.assertEqual(scenario['equity_bridge_formula'], FORMULA)


if __name__ == '__main__':
    unittest.main()
