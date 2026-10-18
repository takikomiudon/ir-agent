"""Explicit composite displays reproduce cents without adopting share/period meaning."""
from copy import deepcopy
from decimal import Inexact, Rounded, localcontext
import json
import unittest

from ir_agent.adapters.common import canonical_json
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from ir_agent.model_inputs import audit_model_inputs
from test_disclosed_facts import NOW, LATER, request as legacy_request
from test_fact_model_pipeline import request as legacy_model_request


def request(raw='24 円 75 銭', *, quote=None, unit='JPY-per-share', raw_unit='円'):
    value = legacy_request(raw, raw_unit, unit, kind='issuer_guidance', quote=quote)
    value['facts'][0]['raw_value_format'] = 'jpy_yen_sen'
    value['source']['metadata']['synthetic'] = True
    return value


def first(bundle): return json.loads(bundle['sources'][1]['content'])['facts'][0]


def replay(bundle):
    return reproduce_disclosed_fact_source(bundle['sources'][1], {s['id']: s for s in bundle['sources']})


def model_request():
    value = legacy_model_request()
    value['sources'] = normalize_disclosed_facts(request(), now=NOW)['sources']
    value['valuation']['scenarios'][0]['inputs']['eps_jpy'] = '24.75'
    value['provenance']['scenarios.example.inputs.eps_jpy']['source_id'] = value['sources'][1]['id']
    return value


def row(result): return next(r for r in result['inputs'] if r['path'].endswith('eps_jpy'))


class YenSenFactsTests(unittest.TestCase):
    def test_exact_display_signs_cents_and_spans_preserve_source_and_meaning(self):
        cases = [('24 円 75 銭', '24.75'), ('99 円 00 銭', '99.00'), ('198 円 00 銭', '198.00'),
                 ('1,234円05銭', '1234.05'), ('24円1銭', '24.01'), ('00024円01銭', '24.01'),
                 ('+24円75銭', '24.75'), ('△24円75銭', '-24.75'), ('▲24円75銭', '-24.75'),
                 ('-0円05銭', '-0.05'), ('-0円00銭', '0'), ('0円00銭', '0'),
                 ('24\t円\u300075\t銭', '24.75')]
        for raw, expected in cases:
            for unit in ('JPY', 'JPY-per-share'):
                with self.subTest(raw=raw, unit=unit):
                    value = request(raw, unit=unit); saved = deepcopy(value)
                    bundle = normalize_disclosed_facts(value, now=NOW); fact = first(bundle)
                    self.assertEqual(fact['value'], expected)
                    self.assertEqual(fact['raw_value'], raw)
                    normalization = fact['normalization']
                    self.assertFalse(normalization['raw_numeric_token_verified'])
                    self.assertTrue(normalization['raw_display_verified'])
                    self.assertNotIn('explicit_unit_multiplier', normalization)
                    for component in normalization['components'].values():
                        start, end = component['raw_value_span']
                        self.assertEqual(raw[start:end], component['raw_token'])
                    self.assertEqual(normalization['components']['sen']['unit_multiplier_to_JPY'], '0.01')
                    self.assertEqual(bundle['sources'][1]['metadata']['normalization_version'], 2)
                    self.assertFalse(fact['financial_inputs_verified']); self.assertTrue(fact['meaning_review_required'])
                    self.assertEqual(bundle['sources'][0], saved['source']); self.assertEqual(value, saved)
                    self.assertEqual(bundle['theses'], [])
        fact = first(normalize_disclosed_facts(request(), now=NOW))
        self.assertEqual(fact['normalization']['components']['yen']['raw_value_span'], [0, 2])
        self.assertEqual(fact['normalization']['components']['sen']['raw_value_span'], [5, 7])
        self.assertEqual(fact['normalization']['components']['sign']['raw_value_span'], [0, 0])

    def test_bad_grammar_and_vertical_or_nonhorizontal_whitespace_are_refused(self):
        cases = ['1,00円75銭', '1234,567円75銭', '24.0円75銭', '24円100銭', '24円000銭',
                 '24円7.5銭', '24円-75銭', '24円+75銭', '△-24円75銭', '24銭75円', '24円75',
                 '２４円７５銭', '24e0円75銭', '24円75銭銭', '24円円75銭', '【24円75銭】',
                 '24円75銭注2', ' 24円75銭', '24円75銭\t', '- 24円75銭']
        for sep in ('\n', '\r\n', '\f', '\v', '\x85', '\u2028', '\u2029', '\u00a0'):
            cases.extend(['24円' + sep + '75銭', sep])
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_disclosed_facts(request(raw), now=NOW)

    def test_display_presence_and_larger_token_boundaries_are_not_reconstructed(self):
        for display in ('124円75銭', '24円75銭0', '24円75銭.0', '２24円75銭',
                        '−24円75銭', '－24円75銭', '﹣24円75銭', '＋24円75銭', '—24円75銭',
                        'A24円75銭', '24円75銭銭', '24円75銭円'):
            with self.subTest(display=display), self.assertRaisesRegex(ValueError, 'larger token'):
                normalize_disclosed_facts(request('24円75銭', quote='2026年度 円 ' + display), now=NOW)
        # A later intact occurrence is acceptable; the source does not select a table column.
        value = request('24円75銭', quote='2026年度 円 124円75銭 / 24円75銭。')
        self.assertEqual(first(normalize_disclosed_facts(value, now=NOW))['value'], '24.75')
        for raw in ('24 円75銭', '24.75'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_disclosed_facts(request(raw, quote='2026年度 円 24円75銭。'), now=NOW)

    def test_missing_empty_and_dash_remain_distinct_from_zero(self):
        for raw, status in [(None, 'missing_value'), ('', 'empty_value'), (' \t\u3000', 'empty_value'),
                            *[(x, 'unconfirmed_dash') for x in ('-', '－', '—', '–', '―')]]:
            with self.subTest(raw=raw):
                fact = first(normalize_disclosed_facts(request(raw), now=NOW))
                self.assertIsNone(fact['value']); self.assertEqual(fact['normalization']['status'], status)
                self.assertFalse(fact['normalization']['raw_display_verified'])
                self.assertFalse(fact['normalization']['raw_numeric_token_verified'])
                self.assertIsNone(fact['normalization']['components'])
        with self.assertRaises(ValueError):
            normalize_disclosed_facts(request('-', quote='2026年度 円 2026-03-31。'), now=NOW)
        for raw in (0, False, [], {}):
            with self.subTest(raw=raw), self.assertRaises(ValueError): normalize_disclosed_facts(request(raw), now=NOW)

    def test_format_and_unit_opt_in_are_strict_even_for_missing_values(self):
        for raw in (None, '24円75銭'):
            for fmt in (None, '', False, 2, {}, [], 'jpy', 'JPY_YEN_SEN'):
                value = request(raw); value['facts'][0]['raw_value_format'] = fmt
                with self.subTest(raw=raw, fmt=fmt), self.assertRaisesRegex(ValueError, 'raw_value_format'):
                    normalize_disclosed_facts(value, now=NOW)
            for label, unit in [('千円', 'JPY'), ('百万円', 'JPY'), ('億円', 'JPY'), ('銭', 'JPY'),
                                ('JPY', 'JPY'), ('円銭', 'JPY'), ('円/株', 'JPY-per-share'),
                                ('円', 'ratio'), ('円', 'shares')]:
                with self.subTest(label=label, unit=unit), self.assertRaisesRegex(ValueError, 'mapping'):
                    normalize_disclosed_facts(request(raw, raw_unit=label, unit=unit), now=NOW)
        for raw in ('24円75銭', '12円'):
            value = request(raw); value['facts'][0].pop('raw_value_format')
            with self.subTest(no_format=raw), self.assertRaises(ValueError): normalize_disclosed_facts(value, now=NOW)
        legacy = normalize_disclosed_facts(legacy_request('\n', '円', 'JPY'), now=NOW)
        self.assertIsNone(first(legacy)['value'])

    def test_cents_arithmetic_is_exact_and_isolated_from_ambient_decimal_context(self):
        raw = '9' * 150 + '円75銭'
        value = request(raw); original = deepcopy(value)
        with localcontext() as context:
            context.prec = 3; context.Emax = 5; context.Emin = -5
            context.traps[Inexact] = context.traps[Rounded] = True
            result = normalize_disclosed_facts(value, now=NOW)
            self.assertFalse(context.flags[Inexact]); self.assertFalse(context.flags[Rounded])
        self.assertEqual(first(result)['value'], '9' * 150 + '.75')
        self.assertEqual(value, original)

    def test_mixed_version2_keeps_each_legacy_fact_exact_and_retrieval_out_of_identity(self):
        value = request(); old = legacy_request('12.5', '円', 'JPY-per-share', kind='external_estimate')
        old['facts'][0]['id'] = 'old'; old['facts'][0]['basis_quote'] = value['source']['content'] + ' 12.5 円'
        value['source']['content'] = old['source']['content'] = old['facts'][0]['basis_quote']
        old['source']['metadata'] = deepcopy(value['source']['metadata'])
        old_fact = first(normalize_disclosed_facts(old, now=NOW))
        value['facts'].append(old['facts'][0]); original = deepcopy(value)
        one = normalize_disclosed_facts(value, now=NOW); two = normalize_disclosed_facts(value, now=LATER)
        self.assertEqual(json.loads(one['sources'][1]['content'])['facts'][1], old_fact)
        for key in ('id', 'content', 'metadata'): self.assertEqual(one['sources'][1][key], two['sources'][1][key])
        self.assertNotEqual(one['sources'][1]['retrieved_at'], two['sources'][1]['retrieved_at'])
        self.assertEqual(replay(one)['status'], 'reproduced'); self.assertEqual(value, original)
        self.assertEqual(normalize_disclosed_facts(old, now=NOW)['sources'][1]['metadata']['normalization_version'], 1)

    def test_full_replay_detects_component_flag_sign_display_value_and_format_tampering(self):
        bundle = normalize_disclosed_facts(request(), now=NOW); original = deepcopy(bundle)
        self.assertEqual(replay(bundle)['status'], 'reproduced')
        for kind in ('yen', 'sen', 'sign', 'span', 'value', 'flag', 'raw', 'unit', 'quote', 'format', 'version1', 'versionbool', 'version3'):
            damaged = deepcopy(bundle); derived = damaged['sources'][1]; content = json.loads(derived['content']); fact = content['facts'][0]
            if kind in ('yen', 'sen'): fact['normalization']['components'][kind]['raw_token'] = '99'
            elif kind == 'sign': fact['normalization']['components']['sign']['multiplier'] = '-1'
            elif kind == 'span': fact['normalization']['components']['sen']['raw_value_span'] = [0, 2]
            elif kind == 'value': fact['value'] = '99.00'
            elif kind == 'flag': fact['normalization']['raw_numeric_token_verified'] = True
            elif kind == 'raw': fact['raw_value'] = '24円75銭'
            elif kind == 'unit': fact['raw_unit_label'] = '千円'
            elif kind == 'quote': fact['basis_quote'] += ' absent'
            elif kind == 'format': fact['raw_value_format'] = None
            else: derived['metadata']['normalization_version'] = {'version1': 1, 'versionbool': True, 'version3': 3}[kind]
            derived['content'] = canonical_json(content)
            with self.subTest(kind=kind): self.assertEqual(replay(damaged)['status'], 'needs_review')
        self.assertEqual(bundle, original)
        old = normalize_disclosed_facts(legacy_request(), now=NOW); old['sources'][1]['metadata']['normalization_version'] = 2
        self.assertIn('unsupported_normalization_version', replay(old)['reason_codes'])

    def test_original_snapshot_checks_remain_separate_from_content_reproduction(self):
        bundle = normalize_disclosed_facts(request(), now=NOW)
        bundle['sources'][0]['retrieved_at'] = '2026-10-14T23:59:00+00:00'
        check = replay(bundle)
        self.assertEqual(check['status'], 'reproduced')
        self.assertEqual(check['original_snapshot_sha256_status'], 'not_reverified')
        self.assertEqual(check['original_content_sha256_status'], 'matched')
        bundle['sources'][0]['content'] = bundle['sources'][0]['content'].replace('75', '76')
        self.assertIn('original_content_hash_mismatch', replay(bundle)['reason_codes'])
        self.assertIn('missing_origin_source_snapshot', reproduce_disclosed_fact_source(bundle['sources'][1], {})['reason_codes'])

    def test_model_numeric_match_still_requires_meaning_and_kind_with_tamper_held(self):
        value = model_request(); original = deepcopy(value); audit = audit_model_inputs(value); checked = row(audit)
        self.assertEqual(checked['normalization_checks'][0]['status'], 'reproduced')
        self.assertEqual(checked['status'], 'source_value_matched')
        self.assertEqual(checked['meaning_review_status'], 'unreviewed')
        self.assertFalse(audit['financial_inputs_verified']); self.assertFalse(audit['expected_value_available'])
        self.assertEqual(value, original)
        for damage, reason in [('kind', 'disclosed_fact_kind_mismatch'), ('both_values', 'normalized_content_not_reproduced'),
                               ('time', 'source_not_available_at_recording')]:
            value = model_request()
            if damage == 'kind': value['provenance']['scenarios.example.inputs.eps_jpy']['kind'] = 'reported_fact'
            elif damage == 'both_values':
                content = json.loads(value['sources'][1]['content']); content['facts'][0]['value'] = '99.00'
                value['sources'][1]['content'] = canonical_json(content)
                value['valuation']['scenarios'][0]['inputs']['eps_jpy'] = '99.00'
            else: value['provenance']['scenarios.example.inputs.eps_jpy']['recorded_at'] = '2026-10-15T00:30:00+00:00'
            with self.subTest(damage=damage):
                checked = row(audit_model_inputs(value)); self.assertEqual(checked['status'], 'needs_review')
                self.assertIn(reason, checked['reason_codes'])

    def test_page_company_quote_and_availability_guards_still_apply(self):
        for target, key, changed in [('facts', 'location', {'pdf_page': 2}), ('facts', 'source_id', 'other'),
                                     ('facts', 'raw_period_label', '2027年度'), ('facts', 'basis_quote', 'absent'),
                                     ('review', 'recorded_at', LATER), ('source', 'retrieved_at', LATER)]:
            value = request(); section = value['facts'][0] if target == 'facts' else value[target]
            section[key] = changed
            with self.subTest(target=target, key=key), self.assertRaises(ValueError): normalize_disclosed_facts(value, now=NOW)


if __name__ == '__main__': unittest.main()
