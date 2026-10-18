"""Reproduce one published example and coefficient-only analytical sensitivities.
No company valuation, data acquisition, database, production imports, or defaults.
"""
from decimal import Decimal, localcontext, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=Path('research/ir-damodaran-regional-regression-discovery-2026-10-16')
PINS={
 'parent-acceptance.json':'6337439bea8cd81fabc239f9163d1789714890036a3d2f2718f0f12abca33aea',
 'capture.json':'a9ffc3fbae87adea25e8f02b94afbcdddfcac2709d34f0e2c7971fb83541dd3c',
 'text/04.txt':'8126c4c37499f6d5e99705f102ce1d7f8212c4f17720a8b5614ae617cd3f49aa',
 'japan-PE-table.json':'3c9b1ba5396cb682e6e3d8c9caee030c3793dc1a3b27b995e2483772d6d81985',
}
for path,pin in PINS.items():
 assert sha256((ROOT/BASE/path).read_bytes()).hexdigest()==pin,path
text=(ROOT/BASE/'text/04.txt').read_text()
table=json.loads((ROOT/BASE/'japan-PE-table.json').read_bytes())

def ref(label,needle):
 start=text.index(needle);end=start+len(needle)
 return {'label':label,'file':str(BASE/'text/04.txt'),'file_sha256':PINS['text/04.txt'],
         'character_start':start,'character_end_exclusive':end,
         'UTF8_start':len(text[:start].encode()),'UTF8_end_exclusive':len(text[:end].encode()),
         'substring_sha256':sha256(needle.encode()).hexdigest()}

references=[
 ref('Current table heading; not the Disney example year','Market Regressions January 2026'),
 ref('Old illustrative US PBV example; source span contains original inputs and formula',
     'As an example, assume that you are looking at Disney in January 2022'+text.split('As an example, assume that you are looking at Disney in January 2022',1)[1].split('At its actual price',1)[0]),
 ref('Ratios are decimal inputs','(25% gets entered as 0.25)'),
 ref('Japan PE table region and formula',
     'Market-wide Regressions of Multiples – Japanese companies in January 2026 T statistics in brackets below coefficients Regression R Squared PE = 4.51 + 4.28 Beta + 42.26 g EPS + 10.46 Payout'),
]
assert table['display']['formula']=='PE = 4.51 + 4.28 Beta + 42.26 gEPS + 10.46 Payout'
D=Decimal
with localcontext() as ctx:
 ctx.prec=40
 inputs={'g_EPS':'0.12','Payout':'0.20','ROE':'0.162','Beta':'1.10'}
 coefficients={'constant':'2.10','g_EPS':'6.07','Beta':'0.69','ROE':'5.09','Payout':'-0.33'}
 terms={'constant':D(coefficients['constant'])}
 for k in ['g_EPS','Beta','ROE','Payout']:terms[k]=D(coefficients[k])*D(inputs[k])
 value=sum(terms.values(),D('0'));assert value==D('4.34598')
 display=value.quantize(D('0.01'),rounding=ROUND_HALF_UP);assert display==D('4.35')
 japan={'g_EPS':D('42.26'),'Payout':D('10.46'),'Beta':D('4.28')}
 sensitivities=[{'variable':k,'coefficient':str(v),'change': '0.01' if k!='Beta' else '1',
    'change_definition':'one percentage point in decimal ratio' if k!='Beta' else 'one unit of Beta, not one percentage point',
    'change_in_regression_PE_multiple':str(v*(D('0.01') if k!='Beta' else D('1')))} for k,v in japan.items()]
result={
 'purpose':'Published example arithmetic and coefficient-only sensitivities; not financial adoption',
 'source_pins':{str(BASE/k):v for k,v in PINS.items()},'source_references':references,
 'Disney_US_PBV_January2022_example':{
  'author_formula':'2.10 + 6.07*g_EPS + 0.69*Beta + 5.09*ROE - 0.33*Payout',
  'original_displayed_inputs_decimal':inputs,'displayed_coefficients':coefficients,
  'exact_terms_from_displayed_tokens':{k:str(v) for k,v in terms.items()},
  'exact_sum_from_displayed_tokens':str(value),'author_display':'4.35',
  'local_display_check':{'operation':'quantize 0.01 ROUND_HALF_UP','result':str(display),'matches_author_display':True,
   'rounding_rule_author_specified':False},
  'precision_scope':'Exact Decimal arithmetic on printed decimal tokens, not independently verified underlying unrounded coefficients or Disney fundamentals',
  'author_historical_valuation_conclusion_reassessed':False},
 'Japan_PE_January2026_coefficient_only':{
  'formula_inventory':table['display']['formula'],'constant':'4.51',
  'analytical_partials':{k:str(v) for k,v in japan.items()},'separate_ceteris_paribus_changes':sensitivities,
  'scope':'Algebraic coefficient products only; other variables held fixed, no baseline/company input or predicted PE computed',
  'Disney_inputs_or_coefficients_transferred':False,
  'table_timing':'January 2026 label; not independently certified as current at October 2026',
  'unresolved_before_company_use':table['unresolved_before_2983_use']},
 'limits':{'company2983_inputs_used':False,'company_valuation_price_IR_decision':False,'new_forecast':False,
  'financial_inputs_adopted':False,'source_document_or_docs_modified':False,'GET':0,'DB_Store':0,
  'not_a_new_policy_or_production_feature':True,'author_return_probability_or_investment_validation':False},
 'verification':{'all_four_source_pins_match':True,'source_reference_offsets':'Unicode characters and UTF8 bytes; half-open; text/04.txt exact substrings','Decimal_precision':40,
 'request_unverified_candidate_4_34698_used':False,'request_candidate_is_not_an_original_source_value':True}}
print(json.dumps(result,ensure_ascii=False,indent=2))
