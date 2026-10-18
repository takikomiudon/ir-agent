"""DDM inputs obey the same precommitted IR and price-review boundaries."""
from copy import deepcopy
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path
import unittest

from ir_agent.decision import evaluate_decision, evaluate_ir_plan
from ir_agent.harness import Harness
from ir_agent.store import Store
from test_decision import plan, request, update_price


def convert(valuation):
    """Synthetic equivalence only: level DPS at 10% reproduces fixture EPS*PE."""
    value = deepcopy(valuation)
    for scenario in value['scenarios']:
        level = str(Decimal(scenario['inputs']['eps_jpy']) * Decimal(scenario['inputs']['pe']) / 10)
        scenario.update(method='dividend_discount', inputs={
            'dividends_per_share_jpy': [level], 'cost_of_equity': '.1',
            'terminal_cost_of_equity': '.1', 'terminal_growth_rate': '0',
            'terminal_dividend_per_share_jpy': level})
    return value


def ddm_plan():
    value = plan()
    value['thesis']['valuation'] = convert(value['thesis']['valuation'])
    for branch in value['question']['branches']:
        if 'valuation' in branch:
            branch['valuation'] = convert(branch['valuation'])
    value['question']['parameter_paths'] = ['scenarios.base.inputs.dividends_per_share_jpy.0',
                                            'scenarios.base.inputs.terminal_dividend_per_share_jpy']
    return value


class DividendDecisionTests(unittest.TestCase):
    def test_applied_reply_persists_ddm_and_price_checked_review_together(self):
        value = ddm_plan()
        root = Path(__file__).resolve().parents[1]
        bundle = json.loads((root / 'examples/demo.json').read_text())
        bundle['theses'] = [value['thesis']]
        bundle['sources'].append(value['sources'][1])
        store = Store(':memory:'); self.addCleanup(store.close)
        harness = Harness(store); harness.ingest(bundle, now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
        harness.register_decision_policy(value['policy'], now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
        question = value['question']
        question['decision_contract'] = {'policy_id': value['policy']['id'], 'policy_version': 1,
            'quote': value['quote'], 'synthetic': True,
            'synthetic_position': {'held': True, 'observed_at': '2026-10-09T09:59:00+09:00'}}
        harness.add_question(question, now=datetime.fromisoformat('2026-10-09T10:01:00+09:00'))
        harness.mark_sent(question['id'], '2026-10-09T10:05:00+09:00', now=datetime.fromisoformat('2026-10-09T10:06:00+09:00'))
        harness.add_reply(json.loads((root / 'examples/reply.json').read_text()), now=datetime.fromisoformat('2026-10-09T16:00:00+09:00'))
        price = deepcopy(value['sources'][1]); price.update(id='synthetic-ddm-reply-price', retrieved_at='2026-10-09T16:59:00+09:00')
        price['metadata'].update(price_jpy='1600', observed_at=price['retrieved_at'])
        harness.ingest({'schema_version': 1, 'sources': [price]}, now=datetime.fromisoformat('2026-10-09T16:59:00+09:00'))
        quote = deepcopy(value['quote']); quote.update(source_id=price['id'], price_jpy='1600',
            observed_at=price['retrieved_at'], retrieved_at=price['retrieved_at'])
        evaluation = json.loads((root / 'examples/reply-evaluation.json').read_text())
        evaluation.update(expected_thesis_version=1, decision_quote=quote)
        applied = harness.evaluate_reply(evaluation, now=datetime.fromisoformat('2026-10-09T17:00:00+09:00'))
        self.assertTrue(applied['applied']); self.assertEqual(applied['action'], 'exit_review')
        self.assertEqual(store.thesis('demo-services')['valuation']['scenarios'][1]['method'], 'dividend_discount')
        self.assertEqual(store.decision_review(applied['decision_review_id'])['thesis_version'], 2)
        self.assertEqual(harness.status()['evaluations'], 1)

    def test_ddm_price_review_and_target_exit_use_supplied_policy(self):
        value = request(); value['thesis']['valuation'] = convert(value['thesis']['valuation'])
        before = deepcopy(value)
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'buy_review')
        self.assertEqual(result['valuation']['expected_value_jpy'], '1278.75')
        self.assertEqual(value, before)
        value['context']['held'] = True; update_price(value, '1300')
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'exit_review')
        self.assertEqual(result['reason_codes'], ['valuation_target_reached'])

    def test_ddm_precommitted_dividend_paths_can_distinguish_decisions(self):
        value = ddm_plan()
        result = evaluate_ir_plan(value)
        self.assertEqual(result['question_value'], 'decision_distinguishing')
        self.assertTrue(any(x['proposed_action'] == 'unresolved' for x in result['outcomes']))
        changes = result['outcomes'][0]['parameter_changes']
        self.assertEqual(set(changes), set(value['question']['parameter_paths']))

    def test_ir_answer_cannot_silently_change_equity_risk_or_terminal_growth(self):
        for field, replacement in (('cost_of_equity', '.08'), ('terminal_cost_of_equity', '.08'),
                                   ('terminal_growth_rate', '.01')):
            value = ddm_plan()
            value['question']['branches'][0]['valuation']['scenarios'][1]['inputs'][field] = replacement
            with self.subTest(field=field):
                result = evaluate_ir_plan(value)
                self.assertEqual(result['question_value'], 'needs_review')
                self.assertIn('unmapped_parameter_change', result['outcomes'][0]['reason_codes'])


if __name__ == '__main__': unittest.main()
