"""Finite independent replay and synthetic fault probes. No DB or network."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,importlib.util,json
from ir_agent.adapters.common import canonical_json
from ir_agent.model_inputs import audit_model_inputs
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
PROOF=ROOT/'research/ir-yen-sen-normalization-implementation-2026-10-16'
NOW='2026-10-16T01:00:00+00:00'
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old=load(PROOF/'before/src/ir_agent/disclosed_facts.py','ir_agent._independent_legacy_facts')
new=load(OUT/'inputs/src/ir_agent/disclosed_facts.py','ir_agent._independent_new_facts')
def request(raw='24円75銭',quote=None,unit='JPY-per-share'):
 quote=quote if quote is not None else '2026年度 合成資料、単位円、金額 '+str(raw)+'。'
 return {'company_id':'synthetic-only','source':{'id':'synthetic-source','company_id':'synthetic-only','title':'Synthetic independent probe only','url':'https://example.invalid/never-fetched','source_type':'public_disclosure','published_at':None,'retrieved_at':'2026-10-16T00:00:00+00:00','content':quote,'requires_research':True,'metadata':{'synthetic':True}},'review':{'author':'Independent synthetic reviewer','recorded_at':'2026-10-16T00:30:00+00:00','rationale':'Parser fault probe only; not real company information'},'facts':[{'id':'synthetic-amount','concept':'synthetic_currency_display','kind':'issuer_guidance','raw_value':raw,'raw_value_format':'jpy_yen_sen','raw_unit_label':'円','unit':unit,'raw_period_label':'2026年度','period':{'label':'2026年度'},'basis_quote':quote,'definition':'Synthetic display only, not an EPS forecast','scope':{'synthetic':True,'table_column_meaning_verified':False}}]}
def fact(bundle): return json.loads(bundle['sources'][1]['content'])['facts'][0]
def replay(bundle):return new.reproduce_disclosed_fact_source(bundle['sources'][1],{s['id']:s for s in bundle['sources']})
results=[]
def passed(label,detail):results.append({'id':label,'status':'passed','detail':detail})
# Independent integer-cents oracle, not float or another Decimal implementation.
count=0
for yen in ('0','1','99','1,234','00009'):
 for sen in ('0','01','09','10','75','98','99'):
  for sign in ('','+','-','△','▲'):
   raw=sign+yen+'円'+sen+'銭'; cents=int(yen.replace(',',''))*100+int(sen)
   expected=('' if sign not in ('-','△','▲') or cents==0 else '-')+str(cents//100)+'.'+str(cents%100).zfill(2) if cents else '0'
   value=new.normalize_disclosed_facts(request(raw),now=NOW)
   assert fact(value)['value']==expected,(raw,fact(value)['value'],expected)
   assert replay(value)['status']=='reproduced'
   assert fact(value)['normalization']['raw_numeric_token_verified'] is False
   count+=1
passed('integer_cents_oracle',{'synthetic_combinations':count,'sen_bounds_and_whole_sign_including_signed_zero':True})
# Cases not limited to producer's table, including sen boundary overflow and malformed commas.
invalid=['0円-0銭','0円+00銭','1,234,56円0銭','1,234円0,1銭','1円01.0銭','1円０1銭','1円²銭','1円999銭','1円0\u202f銭','1円\x00銭','1円01銭\n','\u30001円01銭','1 円\r01 銭','1円\u200901銭']
for raw in invalid:
 try:new.normalize_disclosed_facts(request(raw),now=NOW)
 except ValueError:pass
 else:raise AssertionError(('invalid accepted',raw))
passed('additional_invalid_displays',{'synthetic_cases':len(invalid)})
for leading in ('9','９','+','-','△','▲','−','＋','－','円','銭'):
 for quote in ('2026年度 円 '+leading+'1円01銭。','2026年度 円 1円01銭'+leading+'。'):
  try:new.normalize_disclosed_facts(request('1円01銭',quote=quote),now=NOW)
  except ValueError:pass
  else:raise AssertionError(('larger display slice accepted',quote))
passed('whole_display_boundaries',{'synthetic_cases':22,'scope':'Immediate adjacent characters only, not correct table-column interpretation'})
base=new.normalize_disclosed_facts(request(),now=NOW)
for name in ('true_display_flag','component_multiplier','extra_component','semantic_certification','derived_certification','version_float','remove_format','erase_components'):
 damaged=deepcopy(base);d=damaged['sources'][1];content=json.loads(d['content']);f=content['facts'][0]
 if name=='true_display_flag':f['normalization']['raw_display_verified']=False
 elif name=='component_multiplier':f['normalization']['components']['sen']['unit_multiplier_to_JPY']='1'
 elif name=='extra_component':f['normalization']['components']['invented']={'raw_token':'1'}
 elif name=='semantic_certification':f['financial_inputs_verified']=True
 elif name=='derived_certification':d['metadata']['financial_inputs_verified']=True
 elif name=='version_float':d['metadata']['normalization_version']=2.0
 elif name=='remove_format':f.pop('raw_value_format')
 else:f['normalization']['components']=None
 d['content']=canonical_json(content)
 assert replay(damaged)['status']=='needs_review',name
passed('additional_replay_tamper',{'synthetic_cases':8,'including_unearned_financial_certification':True})
# Version1 must not silently accept even an unknown opt-in field when content was tampered.
legacy=request('1');legacy['facts'][0].pop('raw_value_format');lb=old.normalize_disclosed_facts(legacy,now=NOW)
for fmt in ('jpy_yen_sen',None,''):
 damaged=deepcopy(lb);c=json.loads(damaged['sources'][1]['content']);c['facts'][0]['raw_value_format']=fmt;damaged['sources'][1]['content']=canonical_json(c)
 assert replay(damaged)['status']=='needs_review'
passed('version1_feature_smuggling',{'synthetic_cases':3})
# Existing model consumer must propagate a composite reproduction failure even if both numbers match.
bundle=new.normalize_disclosed_facts(request(),now=NOW)
attr={'reference':'Synthetic only','author':'Synthetic reviewer','recorded_at':'2026-10-16T01:10:00+00:00','rationale':'Numeric match is not meaning verification'}
model={'synthetic':True,'company_id':'synthetic-only','as_of':'2026-10-16T02:00:00+00:00','sources':bundle['sources'],'valuation':{'aggregation':'unweighted','scenarios':[{'name':'synthetic','method':'eps_multiple','inputs':{'eps_jpy':'24.75','pe':'1'}}]},'provenance':{'scenarios.synthetic.inputs.eps_jpy':{**attr,'kind':'issuer_guidance','source_id':bundle['sources'][1]['id'],'value_path':['content','facts',0,'value'],'unit':'JPY-per-share','period':'Synthetic only'},'scenarios.synthetic.inputs.pe':{**attr,'kind':'synthetic_example'}}}
rows=audit_model_inputs(model)
assert rows['financial_inputs_verified'] is False and rows['expected_value_available'] is False
assert rows['meaning_review_required'] is True
for mode in ('cent_multiplier','missing_original','kind'):
 v=deepcopy(model)
 if mode=='missing_original':v['sources']=v['sources'][1:]
 elif mode=='kind':v['provenance']['scenarios.synthetic.inputs.eps_jpy']['kind']='reported_fact'
 else:
  c=json.loads(v['sources'][1]['content']);c['facts'][0]['normalization']['components']['sen']['unit_multiplier_to_JPY']='1';v['sources'][1]['content']=canonical_json(c)
 row=next(r for r in audit_model_inputs(v)['inputs'] if r['path'].endswith('eps_jpy'))
 assert row['status']=='needs_review' and row['reason_codes'],mode
passed('unchanged_model_consumer_hold',{'synthetic_corruptions':3,'base_numeric_match_does_not_verify_meaning':True})
# Rebuild whole captured report with BOTH old frozen and new independently frozen modules.
sources=json.loads((PROOF/'frozen-sources.json').read_bytes())
reports=json.loads((PROOF/'before-whole-report.json').read_bytes())
assert len(sources)==171 and len(reports)==33
old_report=[];new_report=[];facts=0
for item in reports:
 sid=item['source_id'];saved=sources[sid]
 request_value=item['request']; facts+=len(request_value['facts'])
 origin=sources[saved['metadata']['original_source_id']]
 assert request_value['source']['content']==origin['content']
 for module,destination in ((old,old_report),(new,new_report)):
  req=deepcopy(request_value);bundle=module.normalize_disclosed_facts(req,now=item['now']);assert req==request_value
  check=module.reproduce_disclosed_fact_source(saved,sources)
  assert bundle['sources'][1]==saved and check['status']=='reproduced'
  destination.append({'source_id':sid,'request':request_value,'request_sha256':sha(canonical_json(request_value).encode()),'now':item['now'],'producer_bundle':bundle,'reproduction_report':check})
assert facts==143
old_bytes=(canonical_json(old_report)+'\n').encode();new_bytes=(canonical_json(new_report)+'\n').encode()
assert old_bytes==new_bytes==(PROOF/'before-whole-report.json').read_bytes()==(PROOF/'after-whole-report.json').read_bytes()
passed('legacy_whole_report_independent_reexecution',{'original_frozen_objects':171,'normalized_sources':33,'facts':facts,'old_new_and_producer_reports_byte_identical':True,'whole_report_sha256':sha(new_bytes),'request_source_content_equals_frozen_origin':True,'whole_derived_source_objects_equal_saved':True,'DB_connections':0})
# No research real-fact output regenerated/saved; numerical production above was comparisons in memory only.
(OUT/'probe-results.json').write_text(json.dumps({'recorded_at':datetime.now(timezone.utc).isoformat(),'synthetic':True,'checks':results,'findings':[],'new_real_numeric_facts_saved':0,'old_derived_replays_in_memory':33,'normalizer_synthetic_grid_cases':count,'DB_connections':0,'GETs':0},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'passed','groups':len(results),'synthetic_grid_cases':count,'whole_report_sha256':sha(new_bytes),'DB_connections':0,'GETs':0}))
