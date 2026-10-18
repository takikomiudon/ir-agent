from pathlib import Path
import json, hashlib, sys
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/ir_agent').is_dir())
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.disclosed_facts import normalize_disclosed_facts
from ir_agent.models import json_text, validate_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 request=json.loads((HERE/'normalization-input.json').read_bytes())
 output=json.loads((HERE/'normalizer-output.json').read_bytes())
 final=json.loads((HERE/'normalized-bundle.json').read_bytes())
 derived=output['sources'][1]
 rebuilt=normalize_disclosed_facts(request,now=derived['retrieved_at'])
 assert rebuilt==output
 assert (json.dumps(rebuilt,ensure_ascii=False,indent=2)+'\n').encode()==(HERE/'normalizer-output.json').read_bytes()
 pins=json.loads((HERE/'input-pins.json').read_bytes())
 assert all(sha(ROOT/p)==h for p,h in pins['files'].items())
 original=json.loads((ROOT/'research/ir-case-studies-2026-10-15/2929/annual-accounting-input-discovery-2026-10-16/original-annual-followup/source-only-bundle.json').read_bytes())['sources'][0]
 correction=json.loads((ROOT/'research/ir-case-studies-2026-10-15/2929/annual-accounting-input-discovery-2026-10-16/source-only-bundle.json').read_bytes())['sources'][0]
 assert output['sources'][0]==original==request['source']
 assert final=={**output,'sources':[original,correction,derived]}
 assert all(validate_source(s)==s for s in final['sources'])
 facts=json.loads(derived['content'])['facts'];assert len(facts)==2
 assert [f['value'] for f in facts]==['68.61','453.35']
 for f in facts:
  assert f['kind']=='reported_fact' and f['unit']=='JPY-per-share'
  assert f['financial_inputs_verified'] is False and f['meaning_review_required'] is True
  assert f['scope']['known_correction']['source_id']==correction['id']
  assert f['scope']['known_correction']['source_bundle_SHA256']==sha(ROOT/f['scope']['known_correction']['source_bundle_path'])
  text=original['content'];loc=f['location'];a,b=loc['source_character_start'],loc['source_character_end']
  assert text[a:b]==f['basis_quote']
  assert text.encode()[loc['source_UTF8_byte_start']:loc['source_UTF8_byte_end']]==f['basis_quote'].encode()
  a,b=loc['raw_token_source_character_start'],loc['raw_token_source_character_end'];assert text[a:b]==f['raw_value']
  assert text.encode()[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']]==f['raw_value'].encode()
  assert '円 銭' in f['basis_quote'] and f['raw_period_label'] in f['basis_quote']
 assert correction['id'] in derived['metadata']['review']['rationale']
 audit=json.loads((HERE/'model-input-audit-request.json').read_bytes())
 assert audit['sources']==final['sources']
 for i,key in enumerate(['eps_jpy','book_value_per_share_jpy']):
  p=audit['provenance']['scenarios.reported_annual_reference.inputs.'+key]
  assert p['source_id']==derived['id'] and p['value_path']==['content','facts',i,'value']
 # Shape/value references only; audit_model_inputs is intentionally NOT called:
 # it invokes calculate_valuation internally. No calculation or DB access.
 print(json.dumps({'status':'matched_file_only','facts':2,'sources':3,'pure_normalizer_reproduction_bytes_exact':True,'source_original_and_correction_wholeobjects_unchanged':True,'model_input_audit_executed':False,'DB_Store_GET_calculation':0},ensure_ascii=False))
if __name__=='__main__':main()
