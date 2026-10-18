"""Finite pure-code dependency check, using existing synthetic fixture only.

This does not run test methods, access a DB/network or adopt fixture finances.
"""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))
from ir_agent.decision import evaluate_decision
from test_decision import request as existing_synthetic_request, update_price

base = existing_synthetic_request()
original = deepcopy(base)
unweighted = deepcopy(base)
unweighted['thesis']['valuation']['aggregation'] = 'unweighted'
for scenario in unweighted['thesis']['valuation']['scenarios']:
    del scenario['probability']

cases = []
def check(name, value, *, action=None, status=None, reason=None, error_text=None):
    before = deepcopy(value)
    try:
        result = evaluate_decision(value)
    except ValueError as error:
        assert error_text and error_text in str(error), (name, str(error))
        output = {'exception': 'ValueError', 'message': str(error)}
    else:
        assert error_text is None
        assert result['proposed_action'] == action, (name, result)
        assert result['status'] == status
        assert reason in result['reason_codes']
        output = {key: result[key] for key in ('status', 'proposed_action', 'reason_codes')}
        output['missing_parameters'] = result.get('missing_parameters', [])
        output['net_expected_upside_pct'] = result.get('metrics', {}).get('net_expected_upside_pct')
    assert value == before
    cases.append({'name': name, 'synthetic': True, 'output': output})

check('weighted_fixture_control', deepcopy(base), action='buy_review', status='reviewed', reason='entry_conditions_met')
check('unweighted_unheld_intact', deepcopy(unweighted), action='unresolved', status='unresolved',
      reason='scenario_probabilities_not_configured')
invalidated = deepcopy(unweighted)
invalidated['context']['thesis_status'] = 'invalidated'
check('unweighted_unheld_invalidated', deepcopy(invalidated), action='watch', status='reviewed', reason='thesis_invalidated')
invalidated['context']['held'] = True
check('unweighted_held_invalidated', deepcopy(invalidated), action='exit_review', status='reviewed', reason='thesis_invalidated')
held = deepcopy(unweighted)
held['context']['held'] = True
check('unweighted_held_intact_below_target', deepcopy(held), action='hold_review', status='reviewed',
      reason='thesis_intact_below_target')
target = deepcopy(held)
update_price(target, '2000')  # Existing test_decision fixture price case; no real estimate.
check('unweighted_held_target_reached', target, action='exit_review', status='reviewed', reason='valuation_target_reached')
missing_buy_only = deepcopy(invalidated)
del missing_buy_only['policy']['parameters']['minimum_upside_pct']
check('invalidated_held_still_needs_buy_parameter', missing_buy_only,
      action='unresolved', status='unresolved', reason='policy_not_configured')
due = deepcopy(invalidated)
due['thesis']['next_review_date'] = datetime.fromisoformat(due['as_of']).date().isoformat()
check('review_due_is_not_automatic_exit', due, action='unresolved', status='unresolved', reason='thesis_review_due')
missing_model = deepcopy(invalidated)
missing_model['thesis']['valuation'] = None
check('qualitative_invalidated_still_requires_complete_valuation', missing_model, error_text='thesis.valuation')

assert base == original
output = {'status': 'passed', 'scope': 'Nine pure synthetic dependency cases; not an empirical financial test',
    'implementation_sha256': {rel: sha256((ROOT / rel).read_bytes()).hexdigest()
                              for rel in ('src/ir_agent/decision.py', 'src/ir_agent/models.py', 'src/ir_agent/valuation.py', 'tests/test_decision.py')},
    'cases': cases, 'database_accesses': 0, 'network_calls': 0,
    'request_mutation': False, 'real_company_forecast_or_policy_adopted': False,
    'limits': ['Configured numerical valuations and sourced synthetic policy remain present in all successful unweighted cases.',
               'This does not show that qualitative-only real-company data can pass the current decision contract.',
               'Current-view receipt/quote/thesis-version wrappers are not exercised; this is only pure decision dependency inspection.']}
destination = Path(__file__).with_name('code-requirements-repro.json')
destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'cases': len(cases), 'artifact': str(destination)}, ensure_ascii=False))
