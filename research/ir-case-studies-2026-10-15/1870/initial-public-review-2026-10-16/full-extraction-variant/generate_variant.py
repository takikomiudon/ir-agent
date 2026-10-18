"""Offline full PDF text variants via existing shared source builder; no network or DB."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,shutil,subprocess,sys
ROOT=Path('/workspace/ir-agent');sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'src'))
from build_case_source_bundle import build_case_source_bundle
from ir_agent.adapters.common import stable_source_id
from ir_agent.models import validate_source
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(code):
 old=ROOT/f'research/ir-case-studies-2026-10-15/{code}/initial-public-review-2026-10-16';out=old/'full-extraction-variant';out.mkdir(exist_ok=False);(out/'raw').mkdir();(out/'text').mkdir();(out/'snapshots').mkdir()
 def save(n,d):(out/n).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 before={p.relative_to(old).as_posix():sha(p) for p in old.rglob('*') if p.is_file() and not p.is_relative_to(out)};save('original-artifact-pins.json',before)
 source_old=json.loads((old/'source-bundle.json').read_bytes());qs=json.loads((old/'source-quotes.json').read_bytes());pdfs=[s for s in source_old['sources'] if s['metadata']['extraction']['kind']=='pdf_text'];entries=[];manifests=[];adaptations=[];full_by_key={}
 for ix,s in enumerate(pdfs):
  meta=s['metadata'];source_raw=old/meta['original_raw_file'];assert sha(source_raw)==meta['original_raw_sha256'];raw_rel='raw/'+meta['original_raw_sha256'];shutil.copyfile(source_raw,out/raw_rel)
  original_cap=old/meta['original_transport_snapshot'];cap=json.loads(original_cap.read_bytes());assert sha(original_cap)==meta['original_transport_snapshot_sha256'];key=f'{code}-pdf-{ix+1}';text_rel=f'text/{key}-full.txt';subprocess.run(['pdftotext','-layout',str(out/raw_rel),str(out/text_rel)],check=True)
  info=subprocess.run(['pdfinfo',str(out/raw_rel)],capture_output=True,check=True).stdout;(out/f'text/{key}-pdfinfo.txt').write_bytes(info);page_count=int(next(x.split(':',1)[1] for x in info.decode().splitlines() if x.startswith('Pages:')));full=(out/text_rel).read_bytes().decode();assert full.count('\f')==page_count
  assert page_count==({'1866':[11],'1870':[14,29]}[code][ix]);full_by_key[key]=(s,full,page_count)
  adapted={'url':s['url'],'sha256':meta['original_raw_sha256'],'http_status':cap['HTTP_status'],'error':cap['error'],'retrieved_at':s['retrieved_at'],'publication_time':s['published_at'],'content_type':cap['response_headers']['content-type'],'text':None,'original_transport_capture':deepcopy(cap),'adapter_note':'Key-name/structure bridge for shared saved-source builder; exact complete original capture embedded. No HTTP performed; retrieved_at is original completion time, not extraction time.'};snapshot_rel=f'snapshots/{key}.json';save(snapshot_rel,adapted)
  mf={'id':s['id'],'url':s['url'],'sha256':meta['original_raw_sha256'],'http_status':cap['HTTP_status'],'error':cap['error'],'retrieved_at':s['retrieved_at'],'published_at':s['published_at'],'publication_date':meta.get('publication_date'),'publication_note':'Issuer printed publication day; exact clock unknown. Preserve original source metadata date and published_at precision.'};manifests.append(mf)
  entries.append({'key':key,'company_id':s['company_id'],'manifest':{'document':'source-manifest-adapter.json','path':['sources',ix]},'snapshot':snapshot_rel,'snapshot_sha256':sha(out/snapshot_rel),'raw_file':raw_rel,'raw_sha256':meta['original_raw_sha256'],'content_kind':'pdf_text','content_file':text_rel,'content_sha256':sha(out/text_rel),'document_kind':meta['document_kind'],'title':s['title']})
  adaptations.append({'source_key':key,'original_source_id':s['id'],'original_snapshot':str(original_cap.relative_to(ROOT)),'original_snapshot_sha256':sha(original_cap),'original_raw_file':str(source_raw.relative_to(ROOT)),'raw_copy_sha256_matches':True,'adapter_snapshot':snapshot_rel,'adapter_snapshot_sha256':sha(out/snapshot_rel),'page_count':page_count,'extracted_pages':list(range(1,page_count+1)),'semantic_review_pages_unchanged':meta['extraction']['semantic_image_reviewed_pages']})
 save('source-manifest-adapter.json',{'sources':manifests});save('snapshot-adaptation.json',adaptations)
 company=json.loads((old/'selection.json').read_bytes())['DB']['company_snapshot'];mapping={'schema_version':1,'purpose':'Full computational PDF text extraction variant; original interpretation scope and chronology unchanged; no financial-input adoption.','companies':[company],'sources':entries,'citations':[]};save('source-map.json',mapping)
 built=build_case_source_bundle(out/'source-map.json');save('shared-builder-output.json',built)
 new_by_old={};maps=[]
 for entry,new in zip(entries,built['sources']):
  old_s,full,npages=full_by_key[entry['key']];old_meta=old_s['metadata'];meta=new['metadata'];meta.update(original_author=deepcopy(old_meta['original_author']),extraction_author=old_meta['extraction_author'],financial_content=old_meta['financial_content'],original_raw_byte_count=old_meta['original_raw_byte_count'],generic_byte_verifier='not_run_for_variant; shared builder construction and explicit SHA/offset checks are separate from generic verifier matched status',partial_source_lineage={'source_id':old_s['id'],'bundle_file':str((old/'source-bundle.json').relative_to(ROOT)),'bundle_sha256':sha(old/'source-bundle.json'),'original_metadata_preserved_reference':str((old/'source-bundle.json').relative_to(ROOT))},semantic_review_scope={'pages':deepcopy(old_meta['extraction']['semantic_image_reviewed_pages']),'full_document_read':False,'unchanged_from_partial_variant':True})
  meta['extraction'].update(full_PDF_text_extracted=True,pdf_original_page_numbers_extracted=list(range(1,npages+1)),semantic_image_reviewed_pages=deepcopy(old_meta['extraction']['semantic_image_reviewed_pages']),full_document_semantic_review=False,extraction_recorded_at=datetime.now(timezone.utc).isoformat(),actual_command=['pdftotext','-layout',entry['raw_file'],entry['content_file']],raw_semantic_reextraction_performed=False,raw_computational_reextraction_performed=True)
  new['id']=stable_source_id('case-public',company_id=new['company_id'],url=new['url'],content=new['content'],metadata=meta);validate_source(new);new_by_old[old_s['id']]=new
  maps.append({'old_source_id':old_s['id'],'new_source_id':new['id'],'old_bundle':'../source-bundle.json','old_content_sha256':hashlib.sha256(old_s['content'].encode()).hexdigest(),'new_content_sha256':hashlib.sha256(full.encode()).hexdigest(),'old_partial_exact_prefix_of_full':full.startswith(old_s['content']),'old_partial_characters':len(old_s['content']),'new_full_characters':len(full),'raw_SHA_URL_retrieved_at_published_at_unchanged':all(new[k]==old_s[k] for k in ['url','retrieved_at','published_at']) and meta['original_raw_sha256']==old_meta['original_raw_sha256'],'publication_date_and_precision_preserved':meta['publication_date']==old_meta['publication_date'] and meta['publication_precision']=='day','semantic_review_pages':old_meta['extraction']['semantic_image_reviewed_pages'],'all_text_extracted_original_pages':list(range(1,npages+1))})
 final_sources=[deepcopy(new_by_old.get(s['id'],s)) for s in source_old['sources']];save('source-bundle.json',{'schema_version':1,'companies':[],'sources':final_sources,'theses':[]});rebound=[]
 for oldq in qs:
  new=new_by_old[oldq['source_id']];full=new['content'];same=full[oldq['character_start']:oldq['character_end']]==oldq['quote'];a=oldq['character_start']
  if not same:
   parts=full.split('\f');page=oldq['pdf_page'];a=sum(len(p)+1 for p in parts[:page-1])+parts[page-1].index(oldq['quote'])
  assert full[a:a+len(oldq['quote'])]==oldq['quote'];q=deepcopy(oldq);q.update(source_id=new['id'],source_content_sha256=hashlib.sha256(full.encode()).hexdigest(),source_content_path=new['metadata']['extraction']['saved_file'],character_start=a,character_end=a+len(oldq['quote']),old_source_id=oldq['source_id'],old_character_start=oldq['character_start'],old_character_end=oldq['character_end'],old_offset_exact_match=same,rebound_performed=not same);rebound.append(q)
 save('source-id-and-prefix-mapping.json',maps);save('source-quotes.json',rebound)
 for rel,pin in before.items():assert sha(old/rel)==pin
 assert len(rebound)==7;assert all(m['old_partial_exact_prefix_of_full'] for m in maps)
 # Existing six display tokens stay at exactly the same positions, without interpretation or additional values.
 for f in json.loads((old/'financial-observations.json').read_bytes())['facts']:
  q=next(x for x in rebound if x['id']==f['quote_reference']);s=new_by_old[q['old_source_id']];assert s['content'][f['raw_value_character_start']:f['raw_value_character_end']]==f['raw_value']
 save('validation.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'new_GETs':0,'DB_accesses':0,'original_files_unchanged':len(before),'shared_builder':'scripts/build_case_source_bundle.py build_case_source_bundle','shared_builder_sha256':sha(ROOT/'scripts/build_case_source_bundle.py'),'raw_copies_SHA_verified':len(pdfs),'source_contracts':len(final_sources),'PDF_full_formfeed_page_counts':[x['page_count'] for x in adaptations],'all_partial_contents_exact_prefix':True,'all_7_existing_quotes_same_offsets':all(x['old_offset_exact_match'] for x in rebound),'existing_6_display_tokens_same_offsets':True,'new_financial_observations_or_interpretations':0,'generic_byte_verifier':'not_run; no matched claim','findings':[]})
 shutil.copyfile('/tmp/full_variant_pair.py',out/'generate_variant.py')
 return out
if __name__=='__main__':
 for code in ['1866','1870']:
  out=run(code);print(code,'bundle',sha(out/'source-bundle.json'),'validation',sha(out/'validation.json'))
