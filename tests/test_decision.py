"""Financial and temporal boundary tests for explicitly configured decisions."""
from __future__ import annotations

from copy import deepcopy
from decimal import Inexact, localcontext
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from ir_agent.cli import main
from ir_agent.decision import evaluate_decision, evaluate_ir_plan
from ir_agent.valuation import calculate_valuation

ROOT = Path(__file__).resolve().parents[1]


def request():
    thesis = json.loads((ROOT / 'examples/demo.json').read_text())['theses'][0]
    thesis['next_review_date'] = '2026-10-30'
    values = {'minimum_upside_pct': '20', 'maximum_downside_pct': '35', 'entry_cost_pct': '0',
              'exit_cost_pct': '0', 'max_quote_age_seconds': 3600, 'target_scenario': 'base'}
    value = {'synthetic': True, 'as_of': '2026-10-09T10:00:00+09:00', 'thesis': thesis,
            'policy': {'id': 'synthetic-example-only', 'version': 1, 'recorded_at': '2026-10-01T17:00:00+09:00',
                       'parameters': values,
                       'parameter_sources': {k: {'kind': 'synthetic_example', 'reference': 'unit-test fixture',
                                                 'rationale': 'Arbitrary test value, not an investment recommendation'} for k in values}},
            'quote': {'company_id': thesis['company_id'], 'source_id': 'synthetic-price', 'currency': 'JPY',
                      'price_jpy': '1000', 'observed_at': '2026-10-09T09:55:00+09:00',
                      'retrieved_at': '2026-10-09T09:56:00+09:00'},
            'context': {'held': False, 'thesis_status': 'intact', 'information_status': 'public_disclosure',
                        'evidence_ids': thesis['evidence_ids']}}
    value['sources'] = [json.loads((ROOT / 'examples/demo.json').read_text())['sources'][0],
                        {'id': 'synthetic-price', 'company_id': thesis['company_id'], 'title': 'Synthetic quote',
                         'url': 'https://example.invalid/quote', 'source_type': 'market_data', 'published_at': None,
                         'retrieved_at': value['quote']['retrieved_at'], 'content': 'Synthetic market data only',
                         'metadata': {'price_jpy': value['quote']['price_jpy'], 'observed_at': value['quote']['observed_at']}}]
    value['quote'].update(price_path=['metadata', 'price_jpy'], observed_at_path=['metadata', 'observed_at'])
    return value


def update_price(value, price):
    value['quote']['price_jpy'] = price
    value['sources'][1]['metadata']['price_jpy'] = price


def plan():
    value = request()
    question = json.loads((ROOT / 'examples/question.json').read_text())
    question.update(thesis_version=1, evidence_ids=value['thesis']['evidence_ids'],
                    public_answer_status='not_found', parameter_paths=['scenarios.base.inputs.eps_jpy'])
    for b in question['branches']:
        if b['action'] != 'unresolved':
            b['thesis_status'] = 'invalidated' if b['id'] == 'persistent' else 'intact'
    # A single disclosed cost parameter, not an unexplained EPS+multiple re-rating.
    for scenario in question['branches'][1]['valuation']['scenarios']:
        original = next(x for x in value['thesis']['valuation']['scenarios'] if x['name'] == scenario['name'])
        scenario.update(deepcopy(original))
        if scenario['name'] == 'base':
            scenario['inputs']['eps_jpy'] = '40'
    value['question'] = question
    return value


class DecisionTests(unittest.TestCase):
    def test_configured_entry_uses_current_quote_and_records_source_policy(self):
        value = request(); before = deepcopy(value)
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'buy_review')
        self.assertEqual(result['policy_snapshot'], value['policy'])
        self.assertEqual(result['quote']['source_id'], 'synthetic-price')
        self.assertEqual(value, before)

    def test_missing_policy_does_not_supply_financial_defaults(self):
        value = request()
        value['policy']['parameters']['minimum_upside_pct'] = None
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'unresolved')
        self.assertEqual(result['missing_parameters'], ['minimum_upside_pct'])

    def test_unsourced_or_nonfinite_limits_and_synthetic_live_use_are_rejected(self):
        for mutate in ('source', 'nan', 'bool', 'synthetic'):
            with self.subTest(mutate=mutate):
                value = request()
                if mutate == 'source': value['policy']['parameter_sources'].pop('minimum_upside_pct')
                if mutate == 'nan': value['policy']['parameters']['entry_cost_pct'] = 'NaN'
                if mutate == 'bool': value['policy']['parameters']['max_quote_age_seconds'] = True
                if mutate == 'synthetic': value['synthetic'] = False
                with self.assertRaises(ValueError): evaluate_decision(value)

    def test_fees_can_change_buy_to_watch(self):
        value = request()
        value['policy']['parameters']['minimum_upside_pct'] = '30'
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'watch')
        value['policy']['parameters']['minimum_upside_pct'] = '29'
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'watch')
        value['policy']['parameters']['minimum_upside_pct'] = '27'
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'buy_review')
        value['policy']['parameters'].update(entry_cost_pct='1', exit_cost_pct='1')
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'watch')

    def test_downside_at_exact_limit_passes_and_tighter_limit_fails(self):
        value = request(); value['policy']['parameters']['maximum_downside_pct'] = '32.5'
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'buy_review')
        value['policy']['parameters']['maximum_downside_pct'] = '32.499999999999999999'
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'watch')

    def test_target_boundary_uses_unrounded_value(self):
        value = request(); value['context']['held'] = True
        value['thesis']['valuation']['scenarios'] = [
            {'name': 'base', 'probability': '1', 'method': 'eps_multiple',
             'inputs': {'eps_jpy': '100.0004', 'pe': '10'}}]
        update_price(value, '1000.003')
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'hold_review')
        update_price(value, '1000.004')
        self.assertEqual(evaluate_decision(value)['reason_codes'], ['valuation_target_reached'])

    def test_invalidation_exit_and_nonpublic_or_ambiguous_information_gate(self):
        value = request(); value['context'].update(held=True, thesis_status='invalidated')
        self.assertEqual(evaluate_decision(value)['reason_codes'], ['thesis_invalidated'])
        for status in ('unclear', 'potential_nonpublic'):
            value['context']['information_status'] = status
            self.assertEqual(evaluate_decision(value)['proposed_action'], 'unresolved')
        value['context'].update(information_status='public_clarification', thesis_status='uncertain')
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'unresolved')

    def test_future_stale_and_wrong_issuer_quotes_cannot_generate_buy(self):
        for kind in ('future', 'stale', 'issuer', 'currency'):
            with self.subTest(kind=kind):
                value = request()
                if kind == 'future':
                    value['quote']['retrieved_at'] = '2026-10-09T10:01:00+09:00'
                    value['sources'][1]['retrieved_at'] = value['quote']['retrieved_at']
                if kind == 'stale':
                    value['quote']['observed_at'] = '2026-10-09T08:59:59+09:00'
                    value['sources'][1]['metadata']['observed_at'] = value['quote']['observed_at']
                if kind == 'issuer': value['quote']['company_id'] = 'another-company'
                if kind == 'currency': value['quote']['currency'] = 'USD'
                if kind in ('issuer', 'currency'):
                    with self.assertRaises(ValueError): evaluate_decision(value)
                else: self.assertEqual(evaluate_decision(value)['proposed_action'], 'unresolved')

    def test_future_policy_thesis_and_unbound_evidence_are_rejected(self):
        for kind in ('policy', 'thesis', 'evidence'):
            with self.subTest(kind=kind):
                value = request()
                if kind == 'evidence': value['context']['evidence_ids'] = ['unknown']
                else: value[kind]['recorded_at'] = '2026-10-10T00:00:00+09:00'
                with self.assertRaises(ValueError): evaluate_decision(value)

    def test_decimal_caller_precision_and_inexact_traps_do_not_change_decision(self):
        expected = evaluate_decision(request())
        with localcontext() as context:
            context.prec = 2; context.traps[Inexact] = True
            self.assertEqual(evaluate_decision(request()), expected)

    def test_sources_are_required_and_cannot_be_from_future_wrong_issuer_or_unclear_ir(self):
        for kind in ('missing', 'future', 'issuer', 'nonpublic'):
            with self.subTest(kind=kind):
                value = request()
                if kind == 'missing': value.pop('sources')
                if kind == 'future': value['sources'][0]['retrieved_at'] = '2026-10-10T00:00:00+09:00'
                if kind == 'issuer': value['sources'][0]['company_id'] = 'wrong-company'
                if kind == 'nonpublic':
                    value['sources'][0].update(source_type='ir_reply', metadata={'information_status': 'potential_nonpublic'})
                if kind == 'issuer':
                    with self.assertRaises(ValueError): evaluate_decision(value)
                else: self.assertEqual(evaluate_decision(value)['proposed_action'], 'unresolved')

    def test_quote_price_observation_and_retrieval_are_bound_to_snapshot(self):
        for field, changed in (('price_jpy', '1'), ('observed_at', '2026-10-09T09:59:00+09:00'),
                               ('retrieved_at', '2026-10-09T09:59:00+09:00')):
            value = request(); value['quote'][field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError): evaluate_decision(value)

    def test_huge_age_is_safe_and_unknown_sources_are_validation_errors(self):
        value = request(); value['policy']['parameters']['max_quote_age_seconds'] = 10 ** 100
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'buy_review')
        value['policy']['parameter_sources']['unused'] = 'not-an-object'
        with self.assertRaises(ValueError): evaluate_decision(value)

    def test_existing_holding_does_not_pay_a_hypothetical_new_purchase_fee(self):
        value = request()
        value['policy']['parameters'].update(entry_cost_pct='1', maximum_downside_pct='33')
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'watch')
        value['context']['held'] = True
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'hold_review')

    def test_declared_source_origin_cannot_hide_future_unclear_or_cyclic_evidence(self):
        for kind in ('future', 'unclear', 'missing', 'cycle'):
            with self.subTest(kind=kind):
                value = request()
                value['sources'][0]['metadata']['original_source_id'] = 'origin'
                if kind != 'missing':
                    origin = deepcopy(value['sources'][0]); origin['id'] = 'origin'
                    origin['metadata'].pop('original_source_id')
                    if kind == 'future': origin['retrieved_at'] = '2027-01-01T00:00:00+09:00'
                    if kind == 'unclear': origin.update(source_type='ir_reply', metadata={'information_status':'unclear'})
                    if kind == 'cycle': origin['metadata']['original_source_id'] = value['sources'][0]['id']
                    value['sources'].append(origin)
                if kind == 'cycle':
                    with self.assertRaisesRegex(ValueError, 'Cyclic'): evaluate_decision(value)
                else: self.assertEqual(evaluate_decision(value)['proposed_action'], 'unresolved')

    def test_daily_precision_requires_explicit_acceptance_and_original_lineage(self):
        from ir_agent.quotes import normalize_jquants_quote
        normalized = normalize_jquants_quote(json.loads((ROOT / 'examples/quote-source.json').read_text()))
        value = request()
        company_id = normalized['quote']['company_id']
        value['thesis']['company_id'] = company_id
        value['sources'][0]['company_id'] = company_id
        value['sources'] = value['sources'][:1] + normalized['sources']
        value['quote'] = normalized['quote']
        value['as_of'] = value['quote']['retrieved_at']
        value['thesis']['next_review_date'] = '2026-12-30'
        result = evaluate_decision(value)
        self.assertEqual(result['reason_codes'], ['observation_precision_not_accepted'])
        value['policy']['parameters'].update(allow_date_precision=True, max_quote_age_seconds=172800)
        value['policy']['parameter_sources']['allow_date_precision'] = deepcopy(value['policy']['parameter_sources']['minimum_upside_pct'])
        self.assertEqual(evaluate_decision(value)['status'], 'reviewed')
        forged = json.loads(value['sources'][-1]['content']); forged['price_jpy'] = '1'
        value['sources'][-1]['content'] = json.dumps(forged)
        with self.assertRaisesRegex(ValueError, 'deterministic normalization'): evaluate_decision(value)

    def test_due_thesis_requires_research_even_with_a_fresh_quote(self):
        value = request(); value['thesis']['next_review_date'] = '2026-10-09'
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'unresolved')
        self.assertEqual(result['reason_codes'], ['thesis_review_due'])

    def test_existing_valuation_output_unchanged_without_opt_in(self):
        value = request()
        old = calculate_valuation(value['thesis']['valuation'], '1000')
        new = calculate_valuation(value['thesis']['valuation'], '1000', include_unrounded=True)
        self.assertNotIn('unrounded', old)
        self.assertEqual(old, {k: v for k, v in new.items() if k != 'unrounded'})


class IRPlanTests(unittest.TestCase):
    def test_ir_answers_change_decision_and_ambiguity_preserves_baseline(self):
        result = evaluate_ir_plan(plan())
        self.assertEqual(result['question_value'], 'decision_distinguishing')
        self.assertEqual([x['proposed_action'] for x in result['outcomes']], ['buy_review', 'watch', 'unresolved'])
        self.assertEqual(result['outcomes'][-1]['parameter_changes'], [])

    def test_favorable_branch_does_not_force_buy_when_price_has_risen(self):
        value = plan(); update_price(value, '2000')
        result = evaluate_ir_plan(value)
        self.assertEqual(result['outcomes'][0]['precommitted_action'], 'buy_review')
        self.assertEqual(result['outcomes'][0]['proposed_action'], 'watch')
        self.assertEqual(result['question_value'], 'no_decision_change')

    def test_unmapped_multiple_change_is_held_for_review(self):
        value = plan()
        value['question']['branches'][0]['valuation']['scenarios'][1]['inputs']['pe'] = '25'
        result = evaluate_ir_plan(value)
        self.assertEqual(result['question_value'], 'needs_review')
        self.assertIn('scenarios.base.inputs.pe', result['outcomes'][0]['unmapped_parameters'])

    def test_dotted_metadata_cannot_hide_an_actual_eps_change(self):
        value = plan()
        value['thesis']['valuation']['scenarios.base.inputs.eps_jpy'] = '65'
        branch = value['question']['branches'][0]
        branch['valuation']['scenarios.base.inputs.eps_jpy'] = '65'
        branch['valuation']['scenarios'][1]['inputs']['eps_jpy'] = '100'
        value['question']['parameter_paths'] = []
        result = evaluate_ir_plan(value)
        self.assertEqual(result['outcomes'][0]['proposed_action'], 'unresolved')
        self.assertIn('scenarios.base.inputs.eps_jpy', result['outcomes'][0]['unmapped_parameters'])

    def test_later_policy_wrong_version_and_unreviewed_public_information(self):
        for kind in ('policy', 'version', 'public_review'):
            with self.subTest(kind=kind):
                value = plan()
                if kind == 'policy': value['policy']['recorded_at'] = '2026-10-09T10:01:00+09:00'
                if kind == 'version': value['question']['thesis_version'] = 2
                if kind == 'public_review': value['question'].pop('public_answer_status')
                if kind == 'public_review': self.assertEqual(evaluate_ir_plan(value)['question_value'], 'needs_review')
                else:
                    with self.assertRaises(ValueError): evaluate_ir_plan(value)

    def test_json_cli_exercises_both_commands_and_reports_errors_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for command, value in (('decision', request()), ('ir-plan', plan())):
                path = folder / (command + '.json'); path.write_text(json.dumps(value))
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = main(['--db', ':memory:', command, str(path)])
                self.assertEqual(code, 0, stderr.getvalue())
                self.assertIsInstance(json.loads(stdout.getvalue()), dict)
            value = request(); value['quote']['currency'] = 'USD'
            path.write_text(json.dumps(value))
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr): code = main(['--db', ':memory:', 'decision', str(path)])
            self.assertEqual(code, 1); self.assertEqual(stdout.getvalue(), '')
            self.assertNotIn('Traceback', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
