"""Bounded parent verification: exact author-display arithmetic, no database writes."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.valuation import calculate_valuation

OUT = Path(__file__).resolve().parent
report = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'checks': {},
          'input_sha256': {}, 'execution': {'GET': 0, 'database_writes': 0, 'IR_sends': 0, 'orders': 0},
          'financial_inputs_verified': False, 'current_company_model_adopted': False}


def read(relative):
    raw = (ROOT / relative).read_bytes()
    report['input_sha256'][relative] = sha256(raw).hexdigest()
    return json.loads(raw)


def money(amount):
    """HALF_UP by rational integer arithmetic; no shared Decimal calculator."""
    scaled = abs(amount) * 100 + Fraction(1, 2)
    cents = scaled.numerator // scaled.denominator
    if amount < 0:
        cents = -cents
    sign = '-' if cents < 0 else ''
    return f'{sign}{abs(cents) // 100}.{abs(cents) % 100:02d}'


readiness = read('research/ir-toyota-author-valuation-readiness-2026-10-15/readiness.json')
independent = read('research/ir-toyota-author-valuation-readiness-2026-10-15/independent-review.json')
toyota = read('examples/valuation-equity-bridge.toyota-author-display.json')
synthetic = read('examples/valuation-equity-bridge.synthetic.json')
expected = {row['key']: row['scale_only_candidate_value']
            for row in readiness['adaptive_case']['required_input_readiness']}
assert toyota['scenarios'][0]['inputs'] == expected
assert len(expected) == 9
report['checks']['nine_inputs_equal_original_readiness_candidates'] = True

for label, fixture, comparison in [('author_display', toyota, '3060'), ('synthetic', synthetic, '100')]:
    before = deepcopy(fixture)
    result = calculate_valuation(fixture, comparison, include_unrounded=True)
    assert fixture == before
    i = fixture['scenarios'][0]['inputs']
    r, g = Fraction(i['discount_rate']), Fraction(i['terminal_growth_rate'])
    forecast = sum((Fraction(cf) / (1 + r) ** t for t, cf in enumerate(i['fcf_jpy'], 1)), Fraction(0))
    tv = Fraction(i['terminal_fcff_jpy']) / (r - g)
    terminal_pv = tv / (1 + r) ** len(i['fcf_jpy'])
    operating = forecast + terminal_pv
    equity = operating + Fraction(i['cash_jpy']) + Fraction(i['non_operating_assets_jpy']) - Fraction(i['debt_jpy']) - Fraction(i['minority_interests_jpy'])
    fair = equity / Fraction(i['shares_outstanding'])
    row = result['scenarios'][0]
    for key, amount in [('enterprise_value_jpy', operating), ('equity_value_jpy', equity),
                        ('terminal_value_jpy', tv), ('present_value_of_terminal_value_jpy', terminal_pv),
                        ('present_value_of_forecast_fcf_jpy', forecast), ('fair_value_jpy', fair)]:
        assert row[key] == money(amount), (key, row[key], money(amount))
    error = abs(Fraction(result['unrounded']['scenarios'][0]['fair_value_jpy']) - fair)
    assert error < Fraction(1, 10 ** 70)  # Computation precision, never an investment threshold.
    assert result['expected_value_jpy'] is None and result['expected_upside_pct'] is None
    assert row['probability'] is None
    report['checks'][label] = {'result': result, 'fair_value_fraction': str(fair),
        'operating_value_fraction': str(operating), 'equity_value_fraction': str(equity),
        'terminal_value_fraction': str(tv), 'unrounded_absolute_error_fraction': str(error)}
    if label == 'author_display':
        assert money(fair) == '3944.09'
        assert tv != Fraction('19856') * 10 ** 9
        assert fixture['research_context']['author_displayed_results']['per_share_jpy'] == '3943'
    else:
        assert money(fair) == '92.82'

# Read-only observation; the file hash must be unchanged by this script.
db = ROOT / 'data/ir-research-2026-10-15.sqlite3'
before_db = sha256(db.read_bytes()).hexdigest()
with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as connection:
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts = {name: connection.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0]
              for name in ('companies', 'sources', 'source_classifications', 'theses', 'questions', 'replies') if name in tables}
after_db = sha256(db.read_bytes()).hexdigest()
assert before_db == after_db
assert counts['sources'] == 64 and counts['source_classifications'] == 63
assert counts['questions'] == counts['replies'] == 0
report['checks']['database_read_only'] = {'counts': counts, 'sha256_before': before_db,
                                          'sha256_after': after_db, 'unchanged': True}
report['limits'] = ['Author-display reproduction is historical, not a current Toyota forecast or adopted investment policy.',
    'Original printed terminal value already differs from arithmetic; no hidden inputs were reverse engineered.',
    'Source matching, reviewer agreement and calculation do not certify financial meaning, current market values or returns.']
(OUT / 'independent-recheck.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'checks': list(report['checks']), 'actual_database_counts': counts}, ensure_ascii=False))
