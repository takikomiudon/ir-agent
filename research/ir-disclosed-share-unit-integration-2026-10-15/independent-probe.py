"""Small synthetic share-unit arithmetic and compatibility check, no DB/GET."""
from copy import deepcopy
from decimal import localcontext, Inexact, Rounded
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source, _UNIT_MULTIPLIERS
from ir_agent.adapters.common import canonical_json
from test_disclosed_facts import request as fixture_request, NOW, LATER

EXPECTED = {('shares', 'shares'): '1', ('株', 'shares'): '1', ('千株', 'shares'): '1000',
            ('万株', 'shares'): '10000', ('百万株', 'shares'): '1000000'}


def request(raw, label, unit='shares', kind='reported_fact'):
    value = fixture_request(raw, label, unit, kind=kind)
    value['source']['metadata']['synthetic'] = True
    value['facts'][0].update(concept='synthetic_count_for_unit_check',
        definition='Synthetic count, no denominator suitability adopted.', scope={'company_id': value['company_id'], 'meaning': 'unverified'})
    return value


def normalize(value):
    before = deepcopy(value)
    bundle = normalize_disclosed_facts(value, now=NOW)
    assert value == before and bundle['sources'][0] == value['source']
    fact = json.loads(bundle['sources'][1]['content'])['facts'][0]
    assert fact['financial_inputs_verified'] is False and fact['meaning_review_required'] is True
    assert bundle['companies'] == bundle['theses'] == [] and 'valuation' not in bundle
    return bundle, fact


def run():
    before_file = ROOT / 'research/ir-disclosed-share-unit-integration-2026-10-15/source-before/src/ir_agent/disclosed_facts.py'
    spec = importlib.util.spec_from_file_location('ir_agent._independent_before_shares', before_file)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    assert _UNIT_MULTIPLIERS == {**old._UNIT_MULTIPLIERS, **EXPECTED}
    factors = []
    with patch('sqlite3.connect', side_effect=AssertionError('DB forbidden')), \
         patch('socket.create_connection', side_effect=AssertionError('Network forbidden')):
        with localcontext() as context:
            context.prec = 3
            context.traps[Inexact] = context.traps[Rounded] = True
            for (label, unit), multiplier in EXPECTED.items():
                value = request('7.125', label, unit)
                bundle, fact = normalize(value)
                assert Fraction(fact['value']) == Fraction('7.125') * int(multiplier)
                assert fact['normalization']['explicit_unit_multiplier'] == multiplier
                for key in value['facts'][0]: assert fact[key] == value['facts'][0][key]
                factors.append({'label': label, 'canonical_unit': unit, 'factor': multiplier,
                                'value': fact['value'], 'independent_Fraction_equal': True})
        corners = []
        for raw, expected in [('0', Fraction(0)), ('△2.75', Fraction(-2750)), ('+0.0001', Fraction(1, 10)),
                              (None, None), ('-', None)]:
            _, fact = normalize(request(raw, '千株'))
            assert (None if fact['value'] is None else Fraction(fact['value'])) == expected
            corners.append({'raw': raw, 'normalized': fact['value']})
        rejected = []
        for label, unit in [('株', 'JPY'), ('円', 'shares'), ('million shares', 'shares')]:
            try: normalize(request('10', label, unit))
            except ValueError: rejected.append([label, unit])
            else: raise AssertionError('Unregistered dimension/alias accepted')
        bad_quote = request('10', '千株')
        bad_quote['facts'][0]['raw_value'] = '11'
        try: normalize(bad_quote)
        except ValueError: pass
        else: raise AssertionError('Unquoted token accepted')

        value = request('7.125', '千株')
        bundle, _ = normalize(value)
        sources = {s['id']: s for s in bundle['sources']}
        derived = bundle['sources'][1]
        assert reproduce_disclosed_fact_source(derived, sources)['status'] == 'reproduced'
        assert old.reproduce_disclosed_fact_source(derived, sources)['status'] == 'needs_review'
        later = normalize_disclosed_facts(value, now=LATER)['sources'][1]
        assert all(later[k] == derived[k] for k in ['id', 'content', 'metadata'])
        changed = deepcopy(derived)
        content = json.loads(changed['content'])
        content['facts'][0]['normalization']['explicit_unit_multiplier'] = '1'
        changed['content'] = canonical_json(content)
        assert reproduce_disclosed_fact_source(changed, sources)['status'] == 'needs_review'
        assert reproduce_disclosed_fact_source(derived, {})['status'] == 'needs_review'

        currency = []
        for kind in sorted(old._KINDS):
            value = fixture_request('2.375', '億円', 'JPY', kind=kind)
            before = deepcopy(value)
            assert normalize_disclosed_facts(value, now=NOW) == old.normalize_disclosed_facts(value, now=NOW)
            assert value == before
            currency.append(kind)
    return {'status': 'bounded_independent_share_unit_probe_pass', 'five_factors': factors, 'missing_zero_sign': corners,
            'rejected_dimension_or_alias_pairs': rejected, 'unquoted_numeric_token_rejected': True,
            'new_reproduction_succeeds': True, 'older_build_new_pair_needs_review': True,
            'later_retrieval_does_not_change_ID_content_metadata': True, 'tampered_factor_and_missing_origin_need_review': True,
            'old_oku_full_outputs_deep_equal_all_four_kinds': currency,
            'whole_mapping_table_delta_exactly_five': True, 'requests_and_original_sources_unchanged': True,
            'financial_meaning_unreviewed_and_no_valuation_assignment': True,
            'execution': {'GETs': 0, 'Store_or_DB_constructors': 0, 'actual_DB_accesses': 0, 'producer_tests_rerun': 0,
                          'full_suite_runs': 0, 'production_or_old_artifact_edits': 0},
            'limits': ['Synthetic unit tokens only; no real share definition, period, ownership or valuation denominator adopted.',
                       'Old52 saved fixture loop was reviewed for unchanged assertions, not independently rerun.']}


if __name__ == '__main__':
    result = run()
    Path('/tmp/ir_share_unit_independent_probe_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'factors': len(result['five_factors']),
                      'legacy_kinds': len(result['old_oku_full_outputs_deep_equal_all_four_kinds'])}))
