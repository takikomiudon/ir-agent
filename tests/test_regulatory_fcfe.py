"""Regulatory-FCFE arithmetic and scope failures; all fixtures are illustrative."""
from copy import deepcopy
from decimal import getcontext, localcontext
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr

from ir_agent.cli import main
from ir_agent.regulatory_fcfe import calculate_regulatory_fcfe


def request():
    basis={'company_id':'illustrative-bank','currency':'USD','amount_unit':'millions',
           'entity_scope':'consolidated group','equity_scope':'common equity holders'}
    period={'kind':'full_fiscal_year','label':'illustrative-year1','start':'2030-01-01','end':'2030-12-31'}
    def amount(value,concept,measurement):
        return {'value':value,'concept':concept,'basis':deepcopy(basis),'period':deepcopy(period),
            'measurement_basis':measurement,'data_kind':'synthetic_example','source_refs':[],
            'rationale':'Illustrative explicit input, not a real forecast.'}
    return {'method':'financial_regulatory_fcfe','basis':basis,'rows':[{'period':period,
        'net_income':amount('15','net_income_to_equity_holders','Net income under supplied income accounting'),
        'regulatory_capital_reinvestment':amount('10','regulatory_capital_reinvestment','Explicit capital-policy reinvestment, not a total capital balance')}],
        'assessment':{'capital_definition_rationale':None,'capital_target_and_buffer_rationale':None,
            'equity_claim_scope_rationale':None,'forecast_comparability_rationale':None,'source_refs':[]}}


class RegulatoryFCFETests(unittest.TestCase):
    def test_author_illustration_arithmetic_does_not_adopt_a_policy_or_value(self):
        value=request();original=deepcopy(value);result=calculate_regulatory_fcfe(value)
        self.assertEqual(result['arithmetic'][0]['fcfe'],'5')
        self.assertEqual(result['status'],'intermediate_only')
        self.assertEqual(result['adoption'],'unresolved')
        self.assertEqual(len(result['assessment_fields_unset']),4)
        self.assertTrue(all(x=='unverified' for x in result['verification'].values()))
        self.assertEqual(value,original)
        result['request']['rows'][0]['net_income']['value']='changed output'
        self.assertEqual(value,original)

    def test_negative_zero_and_released_capital_are_retained_without_clamping(self):
        for income,reinvestment,expected in [('0','0','0'),('1','3','-2'),('-3','4','-7'),('7','-2','9')]:
            with self.subTest(income=income,reinvestment=reinvestment):
                value=request();row=value['rows'][0]
                row['net_income']['value']=income;row['regulatory_capital_reinvestment']['value']=reinvestment
                self.assertEqual(calculate_regulatory_fcfe(value)['arithmetic'][0]['fcfe'],expected)

    def test_income_and_regulatory_measurement_bases_remain_distinct(self):
        value=request();row=value['rows'][0]
        row['net_income']['measurement_basis']='Issuer Japanese GAAP attribution to specified equity holders'
        row['regulatory_capital_reinvestment']['measurement_basis']='Specified regulatory capital-policy definition'
        result=calculate_regulatory_fcfe(value)
        self.assertNotEqual(result['request']['rows'][0]['net_income']['measurement_basis'],
                            result['request']['rows'][0]['regulatory_capital_reinvestment']['measurement_basis'])
        self.assertEqual(result['verification']['basis_and_equity_attribution'],'unverified')

    def test_cross_company_currency_unit_entity_or_equity_scope_fails(self):
        for key,wrong in [('company_id','other-bank'),('currency','JPY'),('amount_unit','billions'),
                          ('entity_scope','operating-bank solo'),('equity_scope','preferred shareholders')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                value=request();value['rows'][0]['regulatory_capital_reinvestment']['basis'][key]=wrong
                calculate_regulatory_fcfe(value)

    def test_operating_income_capital_balance_and_automatic_ratio_inputs_are_rejected(self):
        variants=[]
        for key,concept in [('net_income','operating_income'),('regulatory_capital_reinvestment','total_regulatory_capital')]:
            value=request();value['rows'][0][key]['concept']=concept;variants.append(value)
        value=request();value['capital_ratio']='0.08';variants.append(value)
        value=request();value['terminal_growth']='0.02';variants.append(value)
        for value in variants:
            with self.subTest(value=value),self.assertRaises(ValueError):calculate_regulatory_fcfe(value)

    def test_missing_invalid_and_non_decimal_values_do_not_become_zero(self):
        for wrong in (None,True,15,15.0,'NaN','Infinity',' 15',''):
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):
                value=request();value['rows'][0]['net_income']['value']=wrong
                calculate_regulatory_fcfe(value)

    def test_period_mismatch_quarter_and_overlapping_annual_rows_fail(self):
        variants=[]
        value=request();value['rows'][0]['net_income']['period']['end']='2031-12-31';variants.append(value)
        value=request();value['rows'][0]['period']['kind']='quarter';variants.append(value)
        value=request();value['rows'].append(deepcopy(value['rows'][0]));variants.append(value)
        value=request();value['rows'][0]['period']['start']=None;variants.append(value)
        for value in variants:
            with self.subTest(value=value),self.assertRaises(ValueError):calculate_regulatory_fcfe(value)

    def test_successive_annual_rows_are_not_summed_or_annualized(self):
        value=request();second=deepcopy(value['rows'][0]);second['period'].update(label='illustrative-year2',start='2031-01-01',end='2031-12-31')
        for key in ('net_income','regulatory_capital_reinvestment'):second[key]['period']=deepcopy(second['period'])
        second['net_income']['value']='20';value['rows'].append(second)
        result=calculate_regulatory_fcfe(value)
        self.assertEqual([x['fcfe'] for x in result['arithmetic']],['5','10'])
        self.assertNotIn('total_fcfe',result)

    def test_exact_subtraction_survives_cancellation_and_host_decimal_precision(self):
        value=request();value['rows'][0]['net_income']['value']='1'+'0'*99+'1'
        value['rows'][0]['regulatory_capital_reinvestment']['value']='1'+'0'*100
        with localcontext() as context:
            context.prec=3;before=context.copy();result=calculate_regulatory_fcfe(value)
            self.assertEqual(result['arithmetic'][0]['fcfe'],'1')
            self.assertEqual(getcontext().prec,before.prec)
            self.assertEqual(getcontext().flags,before.flags)

    def test_reference_shape_is_checked_without_claiming_resolution(self):
        value=request();reference={'id':'unresolved-external-proof','version':None,'sha256':'a'*64,
                                   'location':'claimed p22','quote':'unresolved declared quote'}
        value['rows'][0]['net_income']['source_refs']=[reference]
        result=calculate_regulatory_fcfe(value)
        self.assertEqual(result['verification']['source_references'],'unverified')
        value['rows'][0]['net_income']['source_refs'][0]['sha256']='invalid'
        with self.assertRaises(ValueError):calculate_regulatory_fcfe(value)

    def test_CLI_uses_no_store_even_when_a_database_path_is_supplied(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'input.json';path.write_text(json.dumps(request()))
            db=root/'not-created'/'research.sqlite3';stdout=io.StringIO()
            with patch('ir_agent.cli.Store',side_effect=AssertionError('Store must not start')),redirect_stdout(stdout):
                status=main(['--db',str(db),'regulatory-fcfe',str(path)])
            self.assertEqual(status,0);self.assertFalse(db.parent.exists())
            self.assertEqual(json.loads(stdout.getvalue())['arithmetic'][0]['fcfe'],'5')

    def test_CLI_duplicate_JSON_is_rejected_before_store_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json';path.write_text('{"method":"a","method":"b"}')
            stdout,stderr=io.StringIO(),io.StringIO()
            with patch('ir_agent.cli.Store',side_effect=AssertionError('Store must not start')),redirect_stdout(stdout),redirect_stderr(stderr):
                status=main(['regulatory-fcfe',str(path)])
            self.assertEqual(status,1);self.assertEqual(stdout.getvalue(),'')

if __name__=='__main__':unittest.main()
