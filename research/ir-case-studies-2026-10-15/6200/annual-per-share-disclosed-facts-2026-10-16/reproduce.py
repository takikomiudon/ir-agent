"""Offline direct normalizer reproduction; no CLI/valuation/DB/network."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/ir_agent').is_dir())
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.disclosed_facts import normalize_disclosed_facts,reproduce_disclosed_fact_source
from ir_agent.models import json_text

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pins=json.loads((HERE/'input-pins.json').read_bytes());assert all(sha(ROOT/p)==h for p,h in pins['files'].items())
 request=json.loads((HERE/'normalization-input.json').read_bytes());bundle=json.loads((HERE/'normalized-bundle.json').read_bytes());original,derived=bundle['sources'];rebuilt=normalize_disclosed_facts(request,now=pins['normalization_now']);assert rebuilt==bundle
 assert (json.dumps(rebuilt,ensure_ascii=False,indent=2)+'\n').encode()==(HERE/'normalized-bundle.json').read_bytes()
 sourcepath=ROOT/'research/ir-case-studies-2026-10-15/6200/annual-accounting-input-discovery-2026-10-16/source-candidates.json';assert original==request['source']==json.loads(sourcepath.read_bytes())['sources'][0]
 repro=reproduce_disclosed_fact_source(derived,{original['id']:original,derived['id']:derived});assert repro['status']=='reproduced' and not repro['reason_codes'];assert repro==json.loads((HERE/'reproduction.json').read_bytes())
 facts=json.loads(derived['content'])['facts'];assert len(facts)==2 and [f['value'] for f in facts]==['49.20','148.70'];assert derived['metadata']['normalization_version']==1
 for f in facts:
  loc=f['location'];text=original['content'];a,b=loc['source_character_start'],loc['source_character_end'];assert text[a:b]==f['basis_quote'];assert text.encode()[loc['source_UTF8_byte_start']:loc['source_UTF8_byte_end']].decode()==f['basis_quote'];a,b=loc['raw_token_source_character_start'],loc['raw_token_source_character_end'];assert text[a:b]==f['raw_value'];assert text.encode()[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode()==f['raw_value'];assert Decimal(f['value'])==Decimal(f['raw_value']);assert f['raw_unit_label'] in f['basis_quote'] and f['raw_period_label'] in f['basis_quote'];assert not f['financial_inputs_verified'] and f['meaning_review_required']
  for ref in f['scope']['source_context_references']:
   assert sha(ROOT/ref['path'])==ref['sha256'];quotes=json.loads((ROOT/ref['path']).read_bytes())['quotes'];q=next(x for x in quotes if x['id']==ref['quote_id']);assert text[q['full_text_span']['start']:q['full_text_span']['end']]==q['quote']
 assert facts[0]['period']['start_date']=='2024-10-01' and facts[0]['period']['end_date']=='2025-09-30';assert facts[1]['period']['period_kind']=='instant' and facts[1]['period']['as_of_date']=='2025-09-30';assert facts[1]['scope']['BPS_detailed_denominator_explicitly_verified'] is False
 audit=json.loads((HERE/'model-input-audit-request.json').read_bytes());assert audit['sources']==bundle['sources']
 for i,key in enumerate(['eps_jpy','book_value_per_share_jpy']):
  p=audit['provenance']['scenarios.reported_annual_reference.inputs.'+key];assert p['source_id']==derived['id'] and p['value_path']==['content','facts',i,'value'];assert audit['valuation']['scenarios'][0]['inputs'][key]==facts[i]['value']
 print(json.dumps({'status':'reproduced','wholebundle_bytes_exact':True,'facts':2,'original_wholeobject_unchanged':True,'core_SHA256':sha(ROOT/'src/ir_agent/disclosed_facts.py'),'valuation_audit_DB_CLI_GET':0},ensure_ascii=False))
if __name__=='__main__':main()
