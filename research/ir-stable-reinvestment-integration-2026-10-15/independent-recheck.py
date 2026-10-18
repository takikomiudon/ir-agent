"""Bounded independent arithmetic/CLI recheck; synthetic temporary DB only.

Does not certify source authenticity, economic fit, taxes, or any investment.
Run from any directory with the repository virtualenv Python.
"""
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
from ir_agent.stable_reinvestment import calculate_stable_reinvestment
from ir_agent.cli import main, run
from ir_agent.store import Store

OUT = Path('/tmp/ir_stable_reinvestment_recheck.json')
paths = {
    'synthetic': ROOT / 'examples/stable-reinvestment.synthetic.json',
    'exxon_author': ROOT / 'examples/stable-reinvestment.exxon-author.json',
}
original_bytes = {name: path.read_bytes() for name, path in paths.items()}
requests = {name: json.loads(raw) for name, raw in original_bytes.items()}
report = {
    'scope': 'Bounded read-only arithmetic and CLI recheck; temporary synthetic DB only',
    'input_sha256': {name: sha256(raw).hexdigest() for name, raw in original_bytes.items()},
    'checks': {},
    'limitations': [
        'Source IDs, quotes, period labels and tax/ROC applicability are declarations, not verified evidence.',
        'Displayed historical author numbers are used literally; author textual/rounding discrepancies are not corrected.',
        'No DCF, forecast adoption, present issuer input, IR sending, scoring or investment judgment is performed.',
        'Only the specified finite cases were checked; no full suite or broad input exploration was run.',
    ],
}


def valid(value):
    before = deepcopy(value)
    result = calculate_stable_reinvestment(value)
    assert value == before
    assert result['request'] == value and result['request'] is not value
    assert result['status'] == 'intermediate_only'
    assert result['adoption'] == 'unresolved'
    assert set(result['verification'].values()) == {'unverified'}
    return result


def independent(value, result):
    # Exact rational arithmetic is independent of the implementation's Decimal context.
    nopat = Fraction(value['nopat_next']['value'])
    growth = Fraction(value['growth']['value'])
    roc = Fraction(value['roc_new']['value'])
    rate = growth / roc
    expected = {'reinvestment_rate': rate,
                'reinvestment_amount': nopat * rate,
                'fcff': nopat * (1 - rate)}
    comparisons = {}
    precision = result['calculation']['working_precision_digits']
    for key, exact in expected.items():
        displayed = result['arithmetic'][key]
        error = abs(Fraction(displayed) - exact)
        # Numerical rounding allowance only, derived from declared significant-digit
        # precision. This is not a financial/adoption threshold.
        magnitude = Decimal(displayed).adjusted() if displayed != '0' else 0
        rounding_bound = Fraction(10) ** (magnitude + 3 - precision)
        assert error <= rounding_bound, (key, error, rounding_bound)
        comparisons[key] = {
            'exact_fraction': str(exact), 'returned_decimal': displayed,
            'absolute_error_fraction': str(error),
            'rounding_bound_fraction': str(rounding_bound),
        }
    return comparisons


def rejected(name, mutate, expected_text=None):
    value = deepcopy(requests['synthetic'])
    mutate(value)
    before = deepcopy(value)
    try:
        calculate_stable_reinvestment(value)
    except ValueError as error:
        message = str(error)
        if expected_text is not None:
            assert expected_text in message, message
    else:
        raise AssertionError('Invalid case accepted: ' + name)
    assert value == before
    report['checks'].setdefault('rejections', {})[name] = message


results = {name: valid(value) for name, value in requests.items()}
report['checks']['independent_fraction'] = {
    name: independent(requests[name], result) for name, result in results.items()
}
synthetic_arithmetic = results['synthetic']['arithmetic']
assert Fraction(synthetic_arithmetic['reinvestment_rate']) == Fraction(1, 5)
assert Fraction(synthetic_arithmetic['reinvestment_amount']) == 20
assert Fraction(synthetic_arithmetic['fcff']) == 80

prepared_nopat = Fraction(34614) * Fraction('1.02') * Fraction('.62')
assert prepared_nopat == Fraction('21889.8936')
assert Fraction(requests['exxon_author']['nopat_next']['value']) == prepared_nopat
assert Fraction(requests['exxon_author']['growth']['value']) / Fraction(requests['exxon_author']['roc_new']['value']) == Fraction(2, 21)
report['checks']['nopat_preparation_outside_calculator'] = {
    'formula': '34614 * 1.02 * .62', 'exact_nopat_next': '21889.8936',
    'growth_and_tax_not_applied_again': True,
}

negative = deepcopy(requests['synthetic'])
negative['growth']['value'] = '.12'
negative['roc_new']['value'] = '.06'
negative_result = valid(negative)
assert Fraction(negative_result['arithmetic']['reinvestment_rate']) == 2
assert Fraction(negative_result['arithmetic']['reinvestment_amount']) == 200
assert Fraction(negative_result['arithmetic']['fcff']) == -100
assert negative_result['verification']['funding_and_survival'] == 'unverified'
report['checks']['negative_fcff_retained'] = independent(negative, negative_result)

rejected('zero_growth_defined_but_scope_unsupported', lambda q: q['growth'].update(value='0'), 'mathematically defined')
rejected('zero_roc_undefined', lambda q: q['roc_new'].update(value='0'), 'undefined denominator')
rejected('both_zero_denominator_precedence', lambda q: (q['growth'].update(value='0'), q['roc_new'].update(value='0')), 'undefined denominator')
rejected('missing_nopat_value', lambda q: q['nopat_next'].pop('value'))
rejected('pretax_concept', lambda q: q['nopat_next'].update(concept='pretax_operating_income'))
rejected('old_period_timing', lambda q: q['nopat_next'].update(timing='base_period'))
rejected('percent_not_decimal_ratio', lambda q: q['growth'].update(unit='percent'))
rejected('mixed_amount_unit', lambda q: q['roc_new']['basis'].update(amount_unit='billions'))
rejected('mixed_company_basis', lambda q: q['growth']['basis'].update(company_id='synthetic:another-company'))
rejected('mixed_period', lambda q: q['growth']['period'].update(label='Another period'))
rejected('quarter_period', lambda q: q['nopat_next']['period'].update(kind='quarter'))
rejected('missing_explicit_method', lambda q: q.pop('method'))

with localcontext() as hostile:
    hostile.prec = 3
    hostile.rounding = ROUND_DOWN
    hostile.traps[Inexact] = True
    hostile.traps[Rounded] = True
    hostile_results = {name: valid(value) for name, value in requests.items()}
    assert hostile.prec == 3 and hostile.rounding == ROUND_DOWN
    assert hostile.traps[Inexact] and hostile.traps[Rounded]
assert hostile_results == results
report['checks']['ambient_decimal_independent'] = True

filled_assessment = deepcopy(requests['synthetic'])
for key in filled_assessment['assessment']:
    if key != 'source_refs':
        filled_assessment['assessment'][key] = 'Caller-provided explanation; independent applicability review pending.'
filled = valid(filled_assessment)
assert filled['assessment_fields_unset'] == []
assert filled['verification'] == results['synthetic']['verification']
report['checks']['fully_declared_assessment_does_not_verify_or_adopt'] = True

# Exercise actual CLI dispatch with a live isolated Store and compare every SQL row
# plus total_changes. This measures no writes after normal Store setup.
store = Store(':memory:')
try:
    before_dump = '\n'.join(store.connection.iterdump())
    before_changes = store.connection.total_changes
    for name, path in paths.items():
        result = run(Namespace(command='stable-reinvestment', file=str(path)), store)
        assert result == results[name]
        assert '\n'.join(store.connection.iterdump()) == before_dump
        assert store.connection.total_changes == before_changes
    report['checks']['cli_dispatch_db_dump_and_total_changes_unchanged'] = True
finally:
    store.close()

# Also exercise argument parsing, JSON stdout and main lifecycle against an already
# initialized, empty temporary DB. No actual workspace DB is opened.
with tempfile.TemporaryDirectory(prefix='ir-stable-reinvestment-recheck-') as temporary:
    dbpath = Path(temporary) / 'synthetic.sqlite'
    Store(dbpath).close()
    before_db = dbpath.read_bytes()
    cli_results = {}
    for name, path in paths.items():
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--db', str(dbpath), 'stable-reinvestment', str(path)])
        assert code == 0 and stderr.getvalue() == '', stderr.getvalue()
        parsed = json.loads(stdout.getvalue())
        assert parsed == results[name]
        assert dbpath.read_bytes() == before_db
        cli_results[name] = {'exit_code': code, 'matches_api': True}
    report['checks']['cli_main'] = cli_results
    report['checks']['temporary_db_bytes_unchanged'] = True

for name, path in paths.items():
    assert path.read_bytes() == original_bytes[name]
report['checks']['input_files_and_requests_unchanged'] = True
report['status'] = 'passed'
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'artifact': str(OUT),
                  'rejected_cases': len(report['checks']['rejections']),
                  'checks': list(report['checks'])}, ensure_ascii=False))
