"""Reproduce exactly three disclosed displays offline; no model calculation."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/ir_agent').is_dir())
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.disclosed_facts import normalize_disclosed_facts,reproduce_disclosed_fact_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pins=json.loads((HERE/'input-pins.json').read_bytes());assert all(sha(ROOT/p)==h for p,h in pins['files'].items())
 request=json.loads((HERE/'normalization-input.json').read_bytes());bundle=json.loads((HERE/'normalized-bundle.json').read_bytes());original,derived=bundle['sources'];rebuilt=normalize_disclosed_facts(request,now=pins['fixed_normalizer_now']);assert rebuilt==bundle
 assert (json.dumps(rebuilt,ensure_ascii=False,indent=2)+'\n').encode()==(HERE/'normalized-bundle.json').read_bytes()
 sourcepath=ROOT/'research/ir-case-studies-2026-10-15/6200/latest-quarter-guidance-public-review-2026-10-16/source-only-bundle.json';assert original==request['source']==json.loads(sourcepath.read_bytes())['sources'][0]
 repro=reproduce_disclosed_fact_source(derived,{s['id']:s for s in bundle['sources']});assert repro['status']=='reproduced' and not repro['reason_codes'];assert repro==json.loads((HERE/'reproduction.json').read_bytes())
 facts=json.loads(derived['content'])['facts'];assert len(facts)==3 and [f['value'] for f in facts]==['36.63','52.39','35.00'];assert [f['kind'] for f in facts]==['reported_fact','issuer_guidance','issuer_guidance'];assert derived['metadata']['normalization_version']==1
 for f in facts:
  loc=f['location'];t=original['content'];a,b=loc['source_character_start'],loc['source_character_end'];assert t[a:b]==f['basis_quote'];assert t.encode()[loc['source_UTF8_byte_start']:loc['source_UTF8_byte_end']].decode()==f['basis_quote'];a,b=loc['raw_token_source_character_start'],loc['raw_token_source_character_end'];assert t[a:b]==f['raw_value'];assert t.encode()[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode()==f['raw_value'];assert Decimal(f['value'])==Decimal(f['raw_value']);assert f['raw_unit_label'] in f['basis_quote'] and f['raw_period_label'] in f['basis_quote'];assert not f['financial_inputs_verified'] and f['meaning_review_required'];assert not f['scope']['model_or_policy_adopted']
  for ref in f['scope']['source_context_references']:
   assert sha(ROOT/ref['path'])==ref['sha256'];quotes=json.loads((ROOT/ref['path']).read_bytes())['quotes'];q=next(x for x in quotes if x['id']==ref['quote_id']);assert t[q['character_start']:q['character_end']]==q['quote']
 assert facts[0]['period']['start_date']=='2025-10-01' and facts[0]['period']['end_date']=='2026-06-30' and facts[0]['period']['period_kind']=='Q3_nine_month_cumulative_reported'
 assert facts[1]['period']['start_date']=='2025-10-01' and facts[1]['period']['end_date']=='2026-09-30';assert facts[1]['scope']['issuer_forecast_revision_flag']=='無'
 f=facts[2];assert f['period']['start_date'] is None and f['period']['end_date'] is None and f['period']['dividend_record_date'] is None;assert f['scope']['composition_is_context_not_additional_numeric_fact'];assert f['location']['raw_token_source_character_start']==f['location']['source_character_start']+f['basis_quote'].rindex('35.00')
 print(json.dumps({'status':'reproduced','wholebundle_bytes_exact':True,'facts':3,'original_wholeobject_unchanged':True,'normalization_version':1,'core_SHA256':sha(ROOT/'src/ir_agent/disclosed_facts.py'),'DPS_total_column_token_verified':True,'DB_Store_GET_CLI_valuation_IR':0},ensure_ascii=False))
if __name__=='__main__':main()
