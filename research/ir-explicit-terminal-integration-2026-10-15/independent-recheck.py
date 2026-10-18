"""Bounded independent explicit-terminal DCF verification; synthetic only."""
from argparse import Namespace
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from decimal import Decimal, Inexact, Rounded, ROUND_DOWN, localcontext
from fractions import Fraction
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path('/workspace/ir-agent')
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))
from ir_agent.cli import main, run
from ir_agent.decision import _flatten, evaluate_ir_plan
from ir_agent.model_inputs import audit_model_inputs
from ir_agent.stable_reinvestment import calculate_stable_reinvestment
from ir_agent.store import Store
from ir_agent.valuation import calculate_valuation
from test_decision import plan as existing_synthetic_plan  # Fixture factory only; no tests invoked.

PATH = ROOT / 'examples/valuation-explicit-terminal.synthetic.json'
RAW = PATH.read_bytes()
example = json.loads(RAW)
report = {'scope': 'Finite explicit-terminal arithmetic and existing canonical IR constraints',
          'input_sha256': sha256(RAW).hexdigest(), 'checks': {},
          'limitations': [
              'Numerical reproduction does not verify source authenticity, financial adoption, currency, annual period, tax, ROC, or stable-growth applicability.',
              'JPY and year-end FCFF are caller declarations. Million-JPY conversion below is explicit arithmetic; no automatic unit or FX conversion is certified.',
              'Only a single forecast/stable discount rate is implemented. The author year-specific WACC example is not reproduced as a complete valuation.',
              'No real database, network, IR sending, forecast adoption or production/test file is modified.',
          ]}


def calculate(value):
    before = deepcopy(value)
    result = calculate_valuation(value, '100', include_unrounded=True)
    assert value == before
    return result


def exact(value, result):
    inputs = value['scenarios'][0]['inputs']
    flows = list(map(Fraction, inputs['fcf_jpy']))
    rate, growth = Fraction(inputs['discount_rate']), Fraction(inputs['terminal_growth_rate'])
    forecast = sum((flow / (1 + rate) ** period for period, flow in enumerate(flows, 1)), Fraction(0))
    tv = Fraction(inputs['terminal_fcff_jpy']) / (rate - growth)
    terminal_pv = tv / (1 + rate) ** len(flows)
    equity = forecast + terminal_pv + Fraction(inputs['cash_jpy']) - Fraction(inputs['debt_jpy'])
    price = equity / Fraction(inputs['shares_outstanding'])
    actual = result['unrounded']['scenarios'][0]['fair_value_jpy']
    error = abs(Fraction(actual) - price)
    # Arithmetic precision check, never a financial or adoption threshold.
    assert error < Fraction(1, 10 ** 70), (error, price)
    row = result['scenarios'][0]
    assert row['forecast_periods'] == len(flows)
    assert Fraction(row['terminal_fcff_jpy']) == Fraction(inputs['terminal_fcff_jpy'])
    for key, amount in [('present_value_of_forecast_fcf_jpy', forecast), ('terminal_value_jpy', tv),
                        ('present_value_of_terminal_value_jpy', terminal_pv), ('equity_value_jpy', equity),
                        ('fair_value_jpy', price)]:
        # Independent integer HALF_UP serialization, without Decimal arithmetic.
        absolute = abs(amount) * 100
        rounded = (absolute + Fraction(1, 2)).numerator // (absolute + Fraction(1, 2)).denominator
        rounded = -rounded if amount < 0 else rounded
        assert Fraction(row[key]) == Fraction(rounded, 100), (key, row[key], amount)
    return {'forecast_periods': len(flows), 'forecast_pv_fraction': str(forecast),
            'terminal_value_fraction': str(tv), 'terminal_pv_fraction': str(terminal_pv),
            'fair_value_fraction': str(price), 'returned_unrounded_jpy': actual,
            'absolute_error_fraction': str(error)}


example_result = calculate(example)
report['checks']['sample_fraction'] = exact(example, example_result)
assert Fraction(report['checks']['sample_fraction']['fair_value_fraction']) == Fraction(1010, 11)
assert example_result['status'] == 'scenario_values_only'
assert example_result['expected_value_jpy'] is None and example_result['unrounded']['expected_value_jpy'] is None
assert example_result['scenarios'][0]['probability'] is None

# Existing spec's two-period synthetic case independently separates n from n+1.
two = {'scenarios': [{'name': 'synthetic', 'probability': '1', 'method': 'dcf_explicit_terminal',
        'inputs': {'fcf_jpy': ['-110', '121'], 'terminal_fcff_jpy': '200',
                   'discount_rate': '.1', 'terminal_growth_rate': '.02',
                   'cash_jpy': '0', 'debt_jpy': '0', 'shares_outstanding': '10'}}]}
two_result = calculate(two)
report['checks']['two_period_fraction'] = exact(two, two_result)
assert Fraction(report['checks']['two_period_fraction']['forecast_pv_fraction']) == 0
assert Fraction(report['checks']['two_period_fraction']['terminal_value_fraction']) == 2500
assert Fraction(report['checks']['two_period_fraction']['fair_value_fraction']) == Fraction(25000, 121)
assert two_result['scenarios'][0]['fair_value_jpy'] == '206.61'

separate_final = deepcopy(two)
separate_final['scenarios'][0]['inputs']['fcf_jpy'] = ['0', '0']
separate_result = calculate(separate_final)
assert separate_result['scenarios'][0]['terminal_value_jpy'] == two_result['scenarios'][0]['terminal_value_jpy']
assert separate_result['scenarios'][0]['fair_value_jpy'] == two_result['scenarios'][0]['fair_value_jpy']
report['checks']['terminal_separate_from_last_forecast_and_no_growth_tax_reinvestment_repeat'] = True

zero = deepcopy(two)
zero['scenarios'][0]['inputs'].update(fcf_jpy=['0'], terminal_fcff_jpy='0')
zero_result = calculate(zero)
assert zero_result['scenarios'][0]['equity_value_jpy'] == '0.00'
assert zero_result['scenarios'][0]['terminal_fcff_jpy'] == '0'
report['checks']['zero_terminal_and_equity'] = exact(zero, zero_result)

negative = deepcopy(two)
negative['scenarios'][0]['inputs']['terminal_fcff_jpy'] = '-200'
try:
    calculate(negative)
except ValueError as error:
    assert 'negative equity value' in str(error)
else:
    raise AssertionError('Negative equity allowed')
negative['scenarios'][0]['inputs']['cash_jpy'] = '3000'
negative_result = calculate(negative)
assert negative_result['scenarios'][0]['terminal_value_jpy'] == '-2500.00'
report['checks']['negative_terminal_retained_with_positive_equity'] = exact(negative, negative_result)

rejections = {}
def reject(name, value):
    before = deepcopy(value)
    try:
        calculate_valuation(value, '100')
    except ValueError as error:
        rejections[name] = str(error)
    else:
        raise AssertionError('Invalid request accepted: ' + name)
    assert value == before

for key in two['scenarios'][0]['inputs']:
    bad = deepcopy(two)
    del bad['scenarios'][0]['inputs'][key]
    reject('missing_' + key, bad)
for key in ('tax_rate', 'reinvestment_rate', 'terminal_discount_rate'):
    bad = deepcopy(two)
    bad['scenarios'][0]['inputs'][key] = '.2'
    reject('extra_' + key, bad)
for name, replacement in [('null_terminal', None), ('bool_terminal', True)]:
    bad = deepcopy(two)
    bad['scenarios'][0]['inputs']['terminal_fcff_jpy'] = replacement
    reject(name, bad)
bad = deepcopy(two)
bad['scenarios'][0]['inputs']['discount_rate'] = ['.1', '.1']
reject('year_specific_rate_unimplemented', bad)
report['checks']['strict_seven_fields_rejections'] = rejections

# Legacy DCF's saved input/output semantics remain unchanged even with ignored raw fields.
legacy = {'scenarios': [{'name': 'base', 'probability': '1', 'method': 'dcf', 'inputs': {
    'fcf_jpy': ['100'], 'discount_rate': '.10', 'terminal_growth_rate': '.02',
    'cash_jpy': '50', 'debt_jpy': '100', 'shares_outstanding': '10'}}]}
legacy_expected = {'scenarios': [{'name': 'base', 'probability': '1', 'method': 'dcf',
    'fair_value_jpy': '120.00', 'upside_pct': '20.00', 'enterprise_value_jpy': '1250.00',
    'equity_value_jpy': '1200.00'}], 'expected_value_jpy': '120.00',
    'expected_upside_pct': '20.00', 'worst_case_downside_pct': '0.00'}
assert calculate_valuation(legacy, '100') == legacy_expected
legacy_full = calculate(legacy)
for ignored in ('200', None, 'NaN', {'ignored': True}):
    changed = deepcopy(legacy)
    changed['scenarios'][0]['inputs']['terminal_fcff_jpy'] = ignored
    assert calculate(changed) == legacy_full
    assert 'scenarios.base.inputs.terminal_fcff_jpy' not in _flatten(changed)
same_terminal = deepcopy(legacy)
same_terminal['scenarios'][0]['method'] = 'dcf_explicit_terminal'
same_terminal['scenarios'][0]['inputs']['terminal_fcff_jpy'] = '102'
same_result = calculate(same_terminal)
assert Fraction(same_result['unrounded']['scenarios'][0]['fair_value_jpy']) == Fraction(legacy_full['unrounded']['scenarios'][0]['fair_value_jpy'])
report['checks']['legacy_raw_terminal_ignored_and_complete_old_output_unchanged'] = True

with localcontext() as hostile:
    hostile.prec = 2
    hostile.rounding = ROUND_DOWN
    hostile.Emin, hostile.Emax = -2, 2
    hostile.traps[Inexact] = hostile.traps[Rounded] = True
    flags = hostile.flags.copy()
    assert calculate(two) == two_result
    assert hostile.prec == 2 and hostile.flags == flags
report['checks']['ambient_decimal_independence'] = True

stable = json.loads((ROOT / 'examples/stable-reinvestment.synthetic.json').read_bytes())
stable_before = deepcopy(stable)
intermediate = calculate_stable_reinvestment(stable)
assert intermediate['arithmetic']['basis']['currency'] == 'JPY'
assert intermediate['arithmetic']['basis']['amount_unit'] == 'millions'
assert Fraction(intermediate['arithmetic']['fcff']) * 1_000_000 == Fraction(example['scenarios'][0]['inputs']['terminal_fcff_jpy'])
assert intermediate['adoption'] == 'unresolved'
assert set(intermediate['verification'].values()) == {'unverified'}
assert stable == stable_before
report['checks']['explicit_million_jpy_conversion_keeps_upstream_adoption_unresolved'] = True

source = {'id': 'synthetic-terminal', 'company_id': 'synthetic:terminal', 'title': 'Synthetic number snapshot',
          'url': 'https://example.invalid/terminal', 'source_type': 'public_disclosure',
          'published_at': None, 'retrieved_at': '2026-10-14T00:00:00+00:00',
          'content': 'Synthetic arithmetic only; meanings remain unverified.',
          'metadata': {'synthetic': True, 'values': deepcopy(example['scenarios'][0]['inputs'])}}
provenance = {}
for path, numeric in _flatten(example).items():
    if path.endswith('.method') or numeric is None:
        continue
    suffix = path.split('.inputs.', 1)[1].split('.')
    provenance[path] = {'kind': 'synthetic_example', 'reference': 'Explicit synthetic snapshot',
        'rationale': 'Numerical equality is separate from financial meaning.', 'author': 'Bounded check',
        'recorded_at': '2026-10-14T01:00:00+00:00', 'source_id': source['id'],
        'value_path': ['metadata', 'values', suffix[0]] + [int(item) for item in suffix[1:]],
        'unit': 'Synthetic declared unit; unverified', 'period': 'Synthetic declared period; unverified'}
audit_request = {'synthetic': True, 'company_id': source['company_id'], 'as_of': '2026-10-15T00:00:00+00:00',
                 'valuation': example, 'sources': [source], 'provenance': provenance}
audit_before = deepcopy(audit_request)
audit = audit_model_inputs(audit_request)
terminal_path = 'scenarios.synthetic-base.inputs.terminal_fcff_jpy'
assert terminal_path in audit['required_paths']
assert next(row for row in audit['inputs'] if row['path'] == terminal_path)['source_value'] == '80000000'
assert audit['meaning_review_required'] is True and audit['financial_inputs_verified'] is False
assert audit['expected_value_available'] is False
assert audit['unset_probability_paths'] == ['scenarios.synthetic-base.probability']
assert audit_request == audit_before
missing = deepcopy(audit_request)
del missing['provenance'][terminal_path]
missing_audit = audit_model_inputs(missing)
assert terminal_path in missing_audit['missing_paths'] and missing_audit['status'] == 'needs_review'
mismatch = deepcopy(audit_request)
mismatch['sources'][0]['metadata']['values']['terminal_fcff_jpy'] = '80000001'
mismatch_audit = audit_model_inputs(mismatch)
assert 'source_value_mismatch' in next(row for row in mismatch_audit['inputs'] if row['path'] == terminal_path)['reason_codes']
report['checks']['canonical_terminal_provenance_required'] = {
    'required_path': terminal_path, 'matched_value': '80000000', 'missing_status': missing_audit['status'],
    'mismatched_status': mismatch_audit['status'], 'meaning_review_required': True, 'financial_inputs_verified': False}

# Reuse only the existing synthetic policy/question fixture, with the valuation
# representation converted independently to preserve each scenario's fair price.
def explicit_plan():
    value = existing_synthetic_plan()
    valuations = [value['thesis']['valuation']] + [branch['valuation'] for branch in value['question']['branches'] if 'valuation' in branch]
    for valuation in valuations:
        for scenario in valuation['scenarios']:
            fair = Fraction(scenario['inputs']['eps_jpy']) * Fraction(scenario['inputs']['pe'])
            terminal = fair * Fraction(11, 100)
            with localcontext() as context:
                context.prec = 100
                decimal_terminal = str(Decimal(terminal.numerator) / Decimal(terminal.denominator))
            scenario.update(method='dcf_explicit_terminal', inputs={
                'fcf_jpy': ['0'], 'discount_rate': '.1', 'terminal_growth_rate': '0',
                'cash_jpy': '0', 'debt_jpy': '0', 'shares_outstanding': '1',
                'terminal_fcff_jpy': decimal_terminal})
    value['question']['parameter_paths'] = ['scenarios.base.inputs.terminal_fcff_jpy']
    return value

ir = explicit_plan()
ir_before = deepcopy(ir)
ir_result = evaluate_ir_plan(ir)
assert ir == ir_before and ir_result['question_value'] == 'decision_distinguishing'
assert any(row['parameter_changes'] for row in ir_result['outcomes'])
assert all(set(row['parameter_changes']) <= {'scenarios.base.inputs.terminal_fcff_jpy'} for row in ir_result['outcomes'])
unauthorized = deepcopy(ir)
unauthorized['question']['branches'][0]['valuation']['scenarios'][1]['inputs']['discount_rate'] = '.08'
blocked = evaluate_ir_plan(unauthorized)
assert blocked['question_value'] == 'needs_review'
assert any('unmapped_parameter_change' in row.get('reason_codes', []) for row in blocked['outcomes'])
assert any('scenarios.base.inputs.discount_rate' in row.get('unmapped_parameters', []) for row in blocked['outcomes'])
old = deepcopy(ir)
for scenario in old['thesis']['valuation']['scenarios']:
    scenario['method'] = 'dcf'  # Even keeping the raw terminal amount does not add a canonical path.
try:
    evaluate_ir_plan(old)
except ValueError as error:
    assert 'existing valuation inputs' in str(error)
else:
    raise AssertionError('Old question acquired a newly consumed terminal path')
report['checks']['precommitted_terminal_only_rate_change_hold_old_question_reject'] = True

store = Store(':memory:')
try:
    before_dump, before_changes = list(store.connection.iterdump()), store.connection.total_changes
    dispatched = run(Namespace(command='value', file=str(PATH), price='100'), store)
    assert dispatched == {key: value for key, value in example_result.items() if key != 'unrounded'}
    assert list(store.connection.iterdump()) == before_dump and store.connection.total_changes == before_changes
finally:
    store.close()
stdout, stderr = io.StringIO(), io.StringIO()
with redirect_stdout(stdout), redirect_stderr(stderr):
    code = main(['--db', ':memory:', 'value', str(PATH), '--price', '100'])
assert code == 0 and stderr.getvalue() == '', stderr.getvalue()
assert json.loads(stdout.getvalue()) == dispatched
report['checks']['actual_cli_and_memory_db_no_mutation'] = True
assert PATH.read_bytes() == RAW
report['status'] = 'passed'
out = Path('/tmp/ir_explicit_terminal_recheck.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'artifact': str(out),
                  'strict_rejected_cases': len(rejections), 'checks': list(report['checks'])}, ensure_ascii=False))
