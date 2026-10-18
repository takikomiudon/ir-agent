"""Unknown scenario probabilities do not become numerical investment beliefs."""
from copy import deepcopy
from datetime import datetime
import unittest

from ir_agent.decision import evaluate_decision, evaluate_ir_plan
from ir_agent.harness import Harness
from ir_agent.store import Store
from test_decision import request, plan, update_price


def unweight(value):
    value = deepcopy(value)
    value['aggregation'] = 'unweighted'
    for scenario in value['scenarios']:
        scenario.pop('probability', None)
    return value


class UnweightedDecisionTests(unittest.TestCase):
    def value(self):
        value = request(); value['thesis']['valuation'] = unweight(value['thesis']['valuation'])
        return value

    def test_unknown_expected_return_blocks_a_new_purchase_without_invented_weights(self):
        value = self.value(); before = deepcopy(value)
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'unresolved')
        self.assertEqual(result['reason_codes'], ['scenario_probabilities_not_configured'])
        self.assertIsNone(result['valuation']['expected_value_jpy'])
        self.assertIsNone(result['metrics']['net_expected_upside_pct'])
        self.assertIsNone(result['metrics']['entry_upside_pass'])
        self.assertIsNone(result['metrics']['entry_price_ceiling_jpy'])
        self.assertEqual(value, before)

    def test_existing_position_target_and_scenario_risk_checks_need_no_probability(self):
        value = self.value(); value['context']['held'] = True
        result = evaluate_decision(value)
        self.assertEqual(result['proposed_action'], 'hold_review')
        self.assertIsNone(result['metrics']['net_expected_upside_pct'])
        update_price(value, '1300')
        self.assertEqual(evaluate_decision(value)['reason_codes'], ['valuation_target_reached'])
        update_price(value, '1200')
        self.assertEqual(evaluate_decision(value)['reason_codes'], ['scenario_risk_limit_exceeded'])

    def test_reviewed_invalidation_is_not_hidden_by_unknown_expected_return(self):
        value = self.value(); value['context']['thesis_status'] = 'invalidated'
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'watch')
        value['context']['held'] = True
        self.assertEqual(evaluate_decision(value)['proposed_action'], 'exit_review')
        value['quote'] = {}
        self.assertEqual(evaluate_decision(value)['reason_codes'], ['missing_market_quote'])

    def test_ir_plan_for_existing_position_can_compare_exit_and_continue_without_weights(self):
        value = plan(); value['context']['held'] = True
        value['thesis']['valuation'] = unweight(value['thesis']['valuation'])
        for branch in value['question']['branches']:
            if 'valuation' in branch:
                branch['valuation'] = unweight(branch['valuation'])
        result = evaluate_ir_plan(value)
        self.assertEqual(result['question_value'], 'decision_distinguishing')
        self.assertEqual(result['outcomes'][0]['proposed_action'], 'hold_review')
        self.assertEqual(result['outcomes'][1]['proposed_action'], 'exit_review')
        value['context']['held'] = False
        result = evaluate_ir_plan(value)
        self.assertEqual(result['question_value'], 'needs_review')
        self.assertIn('scenario_probabilities_not_configured', result['outcomes'][0]['reason_codes'])

    def test_unweighted_thesis_can_be_saved_and_reviewed_without_fabricating_probabilities(self):
        value = self.value()
        store = Store(':memory:'); self.addCleanup(store.close)
        harness = Harness(store)
        harness.ingest({'schema_version': 1, 'companies': [{'id': value['thesis']['company_id'], 'name': 'Synthetic', 'status': 'active'}],
                        'sources': value['sources'], 'theses': [value['thesis']]},
                       now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
        selected = harness.daily('2026-10-30T10:00:00+09:00', now=datetime.fromisoformat('2026-10-30T10:00:00+09:00'))['selected']
        self.assertEqual(len(selected), 1)
        packet = store.job(selected[0]['job_id'])['packet']
        self.assertIsNone(packet['valuation']['expected_value_jpy'])
        self.assertTrue(all(s['probability'] is None for s in packet['valuation']['scenarios']))
        self.assertEqual(store.thesis(value['thesis']['company_id'])['valuation'], value['thesis']['valuation'])


if __name__ == '__main__': unittest.main()
