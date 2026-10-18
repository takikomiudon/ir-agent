"""Independent Fraction/Decimal arithmetic; stdout only, no upstream imports.

Reproduce the two explicitly separated historical input lanes. No price,
market-cap, policy decision, external fetch or database operation is used.
"""
from decimal import Decimal, Context, localcontext, ROUND_HALF_EVEN, ROUND_HALF_UP, getcontext
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
def digest(p): return sha256(p.read_bytes()).hexdigest()
def fraction_data(f): return {'numerator': str(f.numerator), 'denominator': str(f.denominator)}
def decimal_value(f, precision):
    with localcontext(Context(prec=precision, rounding=ROUND_HALF_EVEN)):
        return Decimal(f.numerator) / Decimal(f.denominator)
def calculate(name, eps, bvps, basis):
    assert eps > 0 and bvps > 0
    radicand = Fraction('22.5') * eps * bvps
    # Guard digits for rational conversion; square root has 60 significant digits.
    radicand_guard = decimal_value(radicand, 120)
    root = Context(prec=60, rounding=ROUND_HALF_EVEN).sqrt(radicand_guard)
    # Check correct nearest rounding against exact rational midpoint bounds.
    with localcontext(Context(prec=120, rounding=ROUND_HALF_EVEN)):
        quantum = Decimal(1).scaleb(root.adjusted() - 59)
        lo, hi = Fraction(root - quantum / 2), Fraction(root + quantum / 2)
        display = str(root.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    assert lo * lo < radicand < hi * hi
    return {'lane': name, 'basis': basis,
            'EPS_exact': fraction_data(eps), 'BVPS_exact': fraction_data(bvps),
            'EPS_Decimal60_reference': str(decimal_value(eps, 60)),
            'BVPS_Decimal60_reference': str(decimal_value(bvps, 60)),
            'radicand_exact_JPY_squared_per_share_squared': fraction_data(radicand),
            'radicand_Decimal60_reference': str(decimal_value(radicand, 60)),
            'sqrt_Decimal60_JPY_per_share': str(root),
            'sqrt_correct_60sig_rounding_verified_by_exact_Fraction_midpoints': True,
            'reference_2dp_JPY_per_share_ROUND_HALF_UP': display,
            'price_JPY': None, 'margin_of_safety': None, 'screen_pass': None,
            'fair_value_certified': False, 'financial_adopted': False}
def main():
    input_path = HERE / 'inputs.json'
    value = json.loads(input_path.read_bytes())
    assert all(digest(ROOT / p) == h for p,h in value['pinned_files'].items())
    discovery = ROOT / value['issuer_review']
    review = json.loads(discovery.read_bytes())
    # Only the existing reviewed quotes are checked; no PDF/image reread.
    assert len(review['positive_quotes']) == 13
    for q in review['positive_quotes']:
        data = (discovery.parent / q['file']).read_bytes()
        assert digest(discovery.parent / q['file']) == q['text_sha256']
        assert data.decode('utf-8')[q['unicode_start']:q['unicode_end_exclusive']] == q['quote']
        assert data[q['utf8_start']:q['utf8_end_exclusive']].decode('utf-8') == q['quote']
    annual = review['displayed_annual_inputs']
    assert annual['basic_EPS']['current'] == value['A']['EPS_JPY_per_share'] == '358.13'
    assert annual['BPS']['current'] == value['A']['BVPS_JPY_per_share'] == '1965.51'
    b = value['B']
    assert annual['ordinary_parent_net_income']['current'] == b['ordinary_parent_NI_million_JPY'] == '9240'
    assert annual['ordinary_common_net_assets']['current'] == b['ordinary_common_net_assets_million_JPY'] == '50858'
    assert str(annual['annual_average_common_shares_exact']['current']) == b['annual_average_common_shares'] == '25802361'
    assert str(annual['end_issued_common_shares_including_treasury']['current']) == b['end_issued_common_including_treasury'] == '27200000'
    assert str(annual['end_reported_treasury_shares']['current']) == b['end_treasury_shares'] == '1324317'
    before_context = getcontext().copy()
    a_eps, a_bvps = Fraction(value['A']['EPS_JPY_per_share']), Fraction(value['A']['BVPS_JPY_per_share'])
    end_shares = int(b['end_issued_common_including_treasury']) - int(b['end_treasury_shares'])
    assert end_shares == 25875683
    b_eps = Fraction(int(b['ordinary_parent_NI_million_JPY']) * 1000000, int(b['annual_average_common_shares']))
    b_bvps = Fraction(int(b['ordinary_common_net_assets_million_JPY']) * 1000000, end_shares)
    lanes = [calculate('A_direct_issuer_display', a_eps, a_bvps, 'Unmodified annual issuer EPS/BPS printed to two decimals.'),
             calculate('B_rounded_amount_share_formula', b_eps, b_bvps, 'Annual common NI and ordinary common net assets from truncated-million-JPY displays; exact p2 share counts, different EPS/BPS denominators.')]
    after_context = getcontext()
    assert (before_context.prec, before_context.rounding, before_context.Emin, before_context.Emax, before_context.flags, before_context.traps) == (after_context.prec, after_context.rounding, after_context.Emin, after_context.Emax, after_context.flags, after_context.traps)
    assert all(digest(ROOT / p) == h for p,h in value['pinned_files'].items())
    return {'calculation_recorded_at': value['calculation_recorded_at'], 'company_id': 'jp:1975',
            'method_author': value['method_author'], 'formula': 'sqrt(22.5 * EPS * BVPS)',
            'period': value['period'], 'source_inputs_sha256': digest(input_path),
            'independent_arithmetic_not_upstream_execution': True,
            'numeric_algorithm': {'exact_radicand': 'fractions.Fraction', 'rational_to_decimal_guard_precision': 120,
                                  'sqrt_significant_digits': 60, 'sqrt_rounding': 'ROUND_HALF_EVEN',
                                  'two_decimal_reference_only': 'ROUND_HALF_UP'},
            'lanes': lanes, 'B_end_common_shares_after_reported_treasury_subtraction': str(end_shares),
            'A_and_B_inputs_not_mixed_or_equalized': True,
            'precision_limit': 'Exact on specified displayed inputs; B truncated reported money and A printed per-share precision do not recover hidden ledger values. Any difference is preserved, not repaired.',
            'validation': {'all13_existing_quote_Unicode_UTF8_spans_exact': True,
                           'pinned_files_unchanged': True, 'caller_Decimal_context_unchanged': True,
                           'originals_or_method_source_modified': False},
            'exclusions': value['exclusions'],
            'execution': {'GET_DB_Store_normalizer_upstream_import_run': 0,
                          'production_shared_or_old_artifact_edits': 0,
                          'current_price_MOS_passfail_valuation_adoption_trade_IR': 0}}
if __name__ == '__main__':
    print(json.dumps(main(), ensure_ascii=False, sort_keys=True, indent=2))
