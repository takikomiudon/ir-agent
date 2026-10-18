from pathlib import Path
import json,hashlib,sys
R=Path('/workspace/ir-agent');O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from ir_agent.disclosed_facts import normalize_disclosed_facts,reproduce_disclosed_fact_source
a=json.loads((O/'audit.json').read_bytes());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in a['input_pins'].items())
r=json.loads((O/'normalization-input.json').read_bytes());b=json.loads((O/'normalized-bundle.json').read_bytes());assert normalize_disclosed_facts(r,now=a['derived_retrieved_at_execution_time'])==b
x=reproduce_disclosed_fact_source(b['sources'][1],{s['id']:s for s in b['sources']});assert x['status']=='reproduced'
print(json.dumps({'whole_bundle_replay_exact':True,'facts':1,'value':'171.36','derived_id':b['sources'][1]['id'],'reproducer':x,'DB_Store_GET_CLI':0},ensure_ascii=False,indent=2))
