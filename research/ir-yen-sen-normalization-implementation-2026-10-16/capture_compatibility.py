"""Offline whole legacy API report; real DB is opened mode=ro only at baseline."""
from contextlib import closing
from copy import deepcopy
from pathlib import Path
import datetime,hashlib,json,platform,sqlite3,sys
from ir_agent.adapters.common import canonical_json
from ir_agent.disclosed_facts import normalize_disclosed_facts,reproduce_disclosed_fact_source,_REQUIRED,_OPTIONAL
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(name,obj):
 b=(canonical_json(obj)+'\n').encode();(OUT/name).write_bytes(b);return sha(b)
def original_for(derived,original):
 candidates=[original]
 for c in list(candidates):
  if c.get('requires_research') is True:
   c=deepcopy(c);c.pop('requires_research');candidates.append(c)
 for c in list(candidates):
  if c.get('metadata')=={}:
   c=deepcopy(c);c.pop('metadata');candidates.append(c)
 return next((c for c in candidates if sha(canonical_json(c).encode())==derived['metadata']['original_source_snapshot_sha256']),original)
phase=sys.argv[1]
if phase=='before':
 paths=['src/ir_agent/disclosed_facts.py','src/ir_agent/model_inputs.py',*['tests/'+x for x in ['test_disclosed_facts.py','test_disclosed_fact_reproduction.py','test_fact_model_pipeline.py','test_oku_yen_facts.py','test_external_estimate_facts.py','test_disclosed_share_units.py','test_model_inputs.py']]]
 pins={}
 for rel in paths:
  p=ROOT/rel;copy=OUT/'before'/rel;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes());pins[rel]=sha(p.read_bytes())
 db=ROOT/'data/ir-research-2026-10-15.sqlite3'
 with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)) as conn:
  raw_rows=conn.execute('SELECT id,company_id,content_hash,data FROM sources ORDER BY id').fetchall()
 sources={r[0]:json.loads(r[3])for r in raw_rows};assert len(sources)==171
 write('frozen-source-rows.json',raw_rows);write('frozen-sources.json',sources)
 write('before-pins.json',{'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'code_and_tests':pins,'actual_DB_URI_mode':'ro','sources_count':len(sources),'all_source_rows_sha256':sha(canonical_json(raw_rows).encode()),'frozen_sources_sha256':sha((OUT/'frozen-sources.json').read_bytes()),'DB_Store_writes':0})
else:sources=json.loads((OUT/'frozen-sources.json').read_bytes())
report=[];facts_count=0
for sid,s in sorted(sources.items()):
 if s.get('metadata',{}).get('provider')!='project_disclosed_fact_normalization':continue
 original=original_for(s,sources[s['metadata']['original_source_id']]);saved=json.loads(s['content']);decl=[{k:deepcopy(v)for k,v in f.items()if k in _REQUIRED|_OPTIONAL}for f in saved['facts']];facts_count+=len(decl)
 request={'source':original,'company_id':s['company_id'],'review':saved['review'],'facts':decl}
 bundle=normalize_disclosed_facts(request,now=s['retrieved_at']);replay=reproduce_disclosed_fact_source(s,sources);assert replay['status']=='reproduced',(sid,replay)
 assert bundle['sources'][1]==s,(sid,'producer not whole-object exact to saved')
 report.append({'source_id':sid,'request':request,'request_sha256':sha(canonical_json(request).encode()),'now':s['retrieved_at'],'producer_bundle':bundle,'reproduction_report':replay})
assert len(report)==33 and facts_count==143,(len(report),facts_count)
rhash=write(phase+'-whole-report.json',report)
oldbundle=ROOT/'research/ir-case-studies-2026-10-15/1904/disclosed-facts-2026-10-16/normalized-bundle.json';assert sha(oldbundle.read_bytes())=='07e79894f6727dba572e63852bf7093e3fe805547742c832e48168e14efd0ea0'
summary={'phase':phase,'normalized_sources':len(report),'facts':facts_count,'whole_report_sha256':rhash,'old1904six_bundle_sha256':sha(oldbundle.read_bytes()),'all33_producer_derived_objects_exact_to_saved':True,'new_real_numeric_facts_created':0}
if phase=='after':
 summary['before_after_whole_report_bytes_identical']=(OUT/'before-whole-report.json').read_bytes()==(OUT/'after-whole-report.json').read_bytes();assert summary['before_after_whole_report_bytes_identical']
write(phase+'-summary.json',summary);print(json.dumps(summary))
