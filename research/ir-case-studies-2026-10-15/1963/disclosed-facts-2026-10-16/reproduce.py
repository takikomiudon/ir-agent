"""Reproduce the frozen bundle and independently check all nine cited Decimal values."""
from contextlib import ExitStack
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(p):return json.loads(p.read_bytes())
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 request=load(HERE/'normalization-input.json');bundle=load(HERE/'normalized-bundle.json');record=load(HERE/'generation.log');pins=load(HERE/'source-reference.json')['old_input_pins']
 assert digest(ROOT/'src/ir_agent/disclosed_facts.py')==record['normalizer_sha256']
 assert digest(HERE/'normalization-input.json')==record['input_sha256'] and digest(HERE/'normalized-bundle.json')==record['bundle_sha256']
 with ExitStack()as stack:
  stack.enter_context(patch('sqlite3.connect',side_effect=AssertionError('DB forbidden')))
  stack.enter_context(patch('socket.create_connection',side_effect=AssertionError('Network forbidden')))
  regenerated=normalize_disclosed_facts(request,now=record['generation_now'])
  check=reproduce_disclosed_fact_source(bundle['sources'][1],{s['id']:s for s in bundle['sources']})
 assert regenerated==bundle and check['status']=='reproduced' and check['original_snapshot_sha256_status']=='matched_supplied_snapshot'
 original=bundle['sources'][0];derived=bundle['sources'][1];facts=json.loads(derived['content'])['facts'];assert len(facts)==9
 assert original==request['source'] and original['published_at'] is None and original['metadata']['publication_date']=='2026-08-07'
 expected=['159299000000','12355000000','11617000000','670000000000','40000000000','46000000000','48.03','190.25','52.00'];locations=load(HERE/'quotes.json')['per_fact_raw_token_locations'];rows=[]
 with localcontext(Context(prec=80)):
  for i,(fact,loc,want)in enumerate(zip(facts,locations,expected)):
   a,z=loc['raw_token_source_character_start'],loc['raw_token_source_character_end'];quote=fact['basis_quote'];raw=fact['raw_value']
   assert original['content'][a:z]==raw and original['content'].encode()[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode()==raw
   assert quote==original['content'][loc['source_character_start']:loc['source_character_end']]
   result=Decimal(raw.replace(',',''))*Decimal('1000000' if i<6 else '1')
   assert result==Decimal(want)==Decimal(fact['value']) and fact['value']==want
   assert fact['normalization']['explicit_unit_multiplier']==('1000000'if i<6 else'1')
   assert fact['kind']==('reported_fact'if i in [0,1,2,6]else'issuer_guidance')
   assert not fact['financial_inputs_verified'] and fact['meaning_review_required']
   assert fact['raw_unit_label']in quote and fact['raw_period_label']in quote
   assert 'raw_value_format'not in fact
   for qid,ref in fact['scope']['source_context_references'].items():
    assert 'basis_quote'not in ref
    assert digest(ROOT/ref['path'])==ref['file_sha256']
    source_quotes=load(ROOT/ref['path']);q=next(q for q in source_quotes if q['id']==qid)
    assert q['quote']==original['content'][ref['character_start']:ref['character_end']]
    assert q['pdf_physical_page']==ref['pdf_page']
   rows.append({'fact_index':i,'fact_id':fact['id'],'raw_value':raw,'unit':fact['unit'],'value':fact['value'],'independent_Decimal_exact':True,'raw_token_character_and_UTF8_offsets_exact':True})
 assert derived['metadata']['normalization_version']==1
 assert all(facts[8]['period'][k]is None for k in ['start_date','end_date','dividend_record_date'])
 assert facts[8]['scope']['accounting_basis']is None and facts[8]['scope']['consolidation_scope']is None
 assert facts[6]['scope']['EPS_basis'].startswith('basic') and facts[6]['value']=='48.03'
 assert all(digest(ROOT/p)==h for p,h in pins.items())
 result={'status':'pass_file_only_reproduction_no_financial_adoption','regenerated_whole_bundle_equal':True,'normalization_reproducer':check,'normalization_version':1,'facts':rows,'source_original_whole_object_equal':True,'old_files_unchanged':len(pins),'fixed_reference_count':sum(len(f['scope']['source_context_references'])for f in facts),'basis_quotes_retained':True,'DPS_label_only_nulls_preserved':True,'basic_not_diluted_EPS':True,'DB_connections':0,'GETs':0,'financial_inputs_adopted':False}
 with(HERE/'reproduction.json').open('x',encoding='utf-8')as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'facts':len(rows),'whole_bundle_equal':True,'old_files_unchanged':len(pins),'reproducer_status':check['status']}))
if __name__=='__main__':main()
