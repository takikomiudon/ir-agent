from pathlib import Path
import json,hashlib,sys
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/ir_agent').is_dir())
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.disclosed_facts import normalize_disclosed_facts
from ir_agent.models import json_text,validate_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pins=json.loads((HERE/'input-pins.json').read_bytes())
 assert all(sha(ROOT/p)==h for p,h in pins['files'].items())
 assert sha(ROOT/'src/ir_agent/disclosed_facts.py')=='d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51'
 request=json.loads((HERE/'normalization-input.json').read_bytes())
 saved=json.loads((HERE/'normalized-bundle.json').read_bytes())
 rebuilt=normalize_disclosed_facts(request,now=pins['normalizer_frozen_now'])
 assert rebuilt==saved
 assert (json.dumps(rebuilt,ensure_ascii=False,indent=2)+'\n').encode()==(HERE/'normalized-bundle.json').read_bytes()
 original=json.loads((ROOT/'research/ir-case-studies-2026-10-15/6814/annual-accounting-input-discovery-2026-10-16/source-only-bundle.json').read_bytes())['sources'][0]
 assert request['source']==original==saved['sources'][0]
 assert len(saved['sources'])==2 and saved['companies']==[] and saved['theses']==[]
 assert all(validate_source(s)==s for s in saved['sources'])
 facts=json.loads(saved['sources'][1]['content'])['facts'];assert len(facts)==2
 assert [f['value'] for f in facts]==['529.53','2826.61']
 for f in facts:
  assert f['kind']=='reported_fact' and f['unit']=='JPY-per-share'
  assert f['financial_inputs_verified'] is False and f['meaning_review_required'] is True
  text=original['content'];l=f['location']
  assert text[l['source_character_start']:l['source_character_end']]==f['basis_quote']
  assert text.encode()[l['source_UTF8_byte_start']:l['source_UTF8_byte_end']]==f['basis_quote'].encode()
  assert text[l['raw_token_source_character_start']:l['raw_token_source_character_end']]==f['raw_value']
  assert text.encode()[l['raw_token_UTF8_byte_start']:l['raw_token_UTF8_byte_end']]==f['raw_value'].encode()
  assert '円 銭' in f['basis_quote'] and f['raw_period_label'] in f['basis_quote']
 audit=json.loads((HERE/'model-input-audit-request.json').read_bytes());assert audit['sources']==saved['sources']
 assert all(p['value_path']==['content','facts',i,'value'] for i,p in enumerate(audit['provenance'].values()))
 print(json.dumps({'status':'matched_file_only','facts':2,'pure_function_frozen_now_bytes_exact':True,'original_wholeobject_unchanged':True,'input8pins_unchanged':True,'modelaudit_executed':False,'calculation_DB_Store_GET':0}))
if __name__=='__main__':main()
