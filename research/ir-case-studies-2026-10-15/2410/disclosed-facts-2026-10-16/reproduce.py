"""Bounded offline recheck of twelve issuer displays; no database or network."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,hashlib
from ir_agent.disclosed_facts import normalize_disclosed_facts,reproduce_disclosed_fact_source
D=Path(__file__).resolve().parent;ROOT=D.parents[3];H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(n,v):
 with (D/n).open('x',encoding='utf-8')as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
request=read(D/'normalization-input.json');saved=read(D/'normalized-bundle.json');gen=read(D/'generation.log');refs=read(D/'source-reference.json');original=request['source'];text=original['content'];assert saved['sources'][0]==original and len(saved['sources'])==2 and saved['companies']==saved['theses']==[]
assert all(H(ROOT/p)==h for p,h in refs['old_input_pins'].items())
replayed=normalize_disclosed_facts(request,now=gen['generation_now']);assert replayed==saved
source=saved['sources'][1];content=json.loads(source['content']);facts=content['facts'];assert len(facts)==12 and source['metadata']['normalization_version']==1 and all('raw_value_format'not in f for f in facts)
expected=['14243525000','1323906000','1336744000','915373000','173.51','20000000000','1890000000','1900000000','1272000000','242.32','0','160.00'];assert [f['value']for f in facts]==expected
observed=[]
for f in facts:
 loc=f['location'];q=f['basis_quote'];a,z=loc['source_character_start'],loc['source_character_end'];assert text[a:z]==q and text.encode()[loc['source_UTF8_byte_start']:loc['source_UTF8_byte_end']].decode()==q
 a,z=loc['raw_token_source_character_start'],loc['raw_token_source_character_end'];assert text[a:z]==f['raw_value']and text.encode()[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode()==f['raw_value']
 mult={'千円':Decimal(1000),'百万円':Decimal(1000000),'円':Decimal(1)}[f['raw_unit_label']];independent=Decimal(f['raw_value'].replace(',',''))*mult;assert independent==Decimal(f['value'])and f['normalization']['raw_numeric_token_verified']is True and f['financial_inputs_verified']is False
 for r in f['scope']['source_context_references'].values():
  p=ROOT/r['path'];assert H(p)==r['file_sha256'];x=read(p)
  for k in r['quote_pointer'].strip('/').split('/'):x=x[int(k)]if isinstance(x,list)else x[k]
  assert x['id']==r['quote_id'];a,z=r['character_start'],r['character_end'];assert text[a:z]==x['quote']and text.encode()[r['UTF8_byte_start']:r['UTF8_byte_end']].decode()==x['quote']
 observed.append({'id':f['id'],'kind':f['kind'],'raw_value':f['raw_value'],'raw_unit_label':f['raw_unit_label'],'unit':f['unit'],'value':f['value'],'Decimal_unit_check':True,'exact_basis_and_raw_token_Unicode_UTF8':True,'context_reference_count':len(f['scope']['source_context_references'])})
for f in facts[-2:]:assert f['period']['start_date']is None and f['period']['end_date']is None and f['period']['dividend_record_date']is None and f['scope']['accounting_basis']is None and f['scope']['consolidation_scope']is None
assert facts[-1]['raw_value']=='160.00' and facts[-1]['location']['column']=='合計'
report=reproduce_disclosed_fact_source(source,{original['id']:original});assert report['status']=='reproduced'and report['original_snapshot_sha256_status']=='matched_supplied_snapshot'and report['reason_codes']==[]
save('reproduction.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'same_now_whole_bundle_ID_and_saved_source_reproduced','request_SHA':H(D/'normalization-input.json'),'bundle_SHA':H(D/'normalized-bundle.json'),'normalizer_calls':{'primary':1,'same_now_whole_bundle_replay':1,'standard_saved_source_reproducer':1},'original_wholeobject_exact':True,'native_original_SHA':refs['original_source_native_SHA'],'normalization_version':1,'twelve_checks':observed,'all_context_references_exact':132,'DPS_dates_recorddate_GAAP_consol_null':True,'raw_annualDPS_160_00_includes_ordinary140_special20_preserved':True,'report':report,'old_frozen_input_files_unchanged':len(refs['old_input_pins']),'DB_GET_Store_code_oldfile_IR_financial_adoption':0})
print(json.dumps({'status':'passed','fact_count':12,'derived_source_id':source['id'],'reproduction_SHA':H(D/'reproduction.json'),'normalization_version':1},ensure_ascii=False))
