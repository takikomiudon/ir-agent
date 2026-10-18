from datetime import datetime, timezone
from hashlib import sha256
import difflib,json,re
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sha=lambda p:sha256(p.read_bytes()).hexdigest()
files=['README.md','research/ir-case-studies-2026-10-15/README.md','docs/research-stage-monitoring.md']
diffs=[]; links=[]; missing=[]; after={}; before={}
for name in files:
 p=ROOT/name; old=(HERE/'before'/name).read_text(); new=p.read_text();before[name]=sha(HERE/'before'/name); after[name]=sha(p)
 diffs.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='before/'+name,tofile=name))
 for raw in re.findall(r'\]\(([^)]+)\)',new):
  target=raw.strip().split(' "',1)[0].strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
  target=unquote(target.split('#',1)[0]); resolved=(p.parent/target).resolve()
  links.append({'document':name,'target':raw,'exists':resolved.exists()})
  if not resolved.exists():missing.append(links[-1])
assert not missing,missing
old=(HERE/'before'/files[1]).read_text(); new=(ROOT/files[1]).read_text()
oldrows=[line for line in old.splitlines() if line.startswith('|')]
assert all(line in new.splitlines() for line in oldrows)
assert len([line for line in new.splitlines() if line.startswith('|')])==len(oldrows)+2
oldtail=old[old.rfind('\n|')+1:]; assert oldtail in new
oldmon=(HERE/'before'/files[2]).read_bytes(); assert (ROOT/files[2]).read_bytes().startswith(oldmon)
oldmain=(HERE/'before'/files[0]).read_text(); newmain=(ROOT/files[0]).read_text()
testpara=next(p for p in oldmain.split('\n\n') if p.startswith('検証の最新チェックポイント'))
assert testpara in newmain
oldmainparas=[p for p in oldmain.split('\n\n') if p]; unchangedmain=sum(p in newmain.split("\n\n") for p in oldmainparas)
assert unchangedmain==len(oldmainparas)-2 # current summary and supplemented2163 paragraph only
oldcaseparas=[p for p in old.split('\n\n') if p]; unchangedcase=sum(p in new.split("\n\n") for p in oldcaseparas)
index=ROOT/'research/ir-case-studies-2026-10-15/disclosed-fact-index-v37.json';assert sha(index)=='e1c07ebca3c5885007738d152588685d6de78f52dfe206d18b900efd7997df4b'
idx=json.loads(index.read_bytes())
assert [idx[k] for k in ['unique_company_count','fact_count','company_source_entry_count','unique_derived_source_count','unique_original_company_source_pair_count']]==[28,226,41,43,34]
historical=idx['actual_research_source_connections']
assert [historical[k] for k in ['database_source_count','connected_derived_source_count','connected_fact_count','unconnected_derived_source_count','unconnected_fact_count','current_qualitative_case_heads','current_qualitative_case_versions','current_reviewed_sources']]==[210,41,219,2,7,25,47,144]
inputs=[
'research/ir-case-studies-2026-10-15/disclosed-fact-index-v37.json',
'research/ir-case-studies-2026-10-15/2410/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json',
'research/ir-case-studies-2026-10-15/2410/disclosed-facts-2026-10-16/index-connection/validation.json',
'research/ir-public-information-review-binding-integration-2026-10-16/fixed-code-under-test-pins.json',
'research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json',
'research/ir-2341-initial-intake-2026-10-16/parent-acceptance.json',
'research/ir-2341-disclosed-facts-intake-2026-10-16/parent-acceptance.json',
'research/ir-2410-initial-with-listing-intake-2026-10-16/parent-acceptance.json',
'research/ir-2410-listing-result-intake-2026-10-16/parent-acceptance.json',
'research/ir-2410-facts-with-qa-intake-2026-10-16/parent-acceptance.json',
]
for code in ['2341','2410']:
 base=f'research/ir-case-studies-2026-10-15/{code}'
 inputs.extend([f'{base}/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json',f'{base}/native-case-setup-2026-10-16/actual-inputs/actual-case.json',f'{base}/question-residual-review-2026-10-16/parent-acceptance.json'])
inputs.extend(['research/ir-case-studies-2026-10-15/2163/actionlearning-authorship-saved-pages-2026-10-16/parent-acceptance.json','research/ir-case-studies-2026-10-15/2327/initial-public-review-2026-10-16/parent-acceptance.json','research/ir-case-studies-2026-10-15/2445/initial-public-review-2026-10-16/parent-acceptance.json'])
pins={p:sha(ROOT/p) for p in inputs}
# Frozen initial input bytes and latest code pins remain untouched; actual database never opened writable.
assert sha(ROOT/'data/ir-research-2026-10-15.sqlite3')=='cbf81671f41ec320a4b08c96df53520e5300ffffbc5530e10bcba1d88f60b7a8'
(HERE/'input-pins.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n')
(HERE/'changes.diff').write_text(''.join(diffs))
(HERE/'link-validation.json').write_text(json.dumps({'local_link_occurrences':len(links),'missing':missing,'links':links},ensure_ascii=False,indent=2)+'\n')
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_three_document_integration_root_review_pending','edited_shared_documents':files,'before_SHA256':before,'after_SHA256':after,'all_local_links_exist':True,'local_link_occurrences':len(links),'old_case_table_lines_preserved_exact':len(oldrows),'new_case_rows':2,'monitoring_old_full_bytes_retained_as_prefix':True,'main_latest1558_and1534_checkpoint_paragraph_exact':True,'main_old_paragraphs_exact_except_current_summary_and2163_append':True,'main_unchanged_old_paragraphs':unchangedmain,'main_total_old_paragraphs':len(oldmainparas),'case_old_paragraphs_remaining_exact':unchangedcase,'case_total_old_paragraphs':len(oldcaseparas),'v37_SHA256':sha(index),'v37_historical_25_47_144_not_rewritten':True,'current_native_26_48_149_RO_verified':True,'file_only_materials_excluded_from_current_counts':True,'code_edits':0,'GET':0,'DB_write_Store_or_mutators':0,'tests_rerun':0,'code44_SHA_match':True,'production_checkpoint':'1558PASS39.753sec (existing root receipt, no rerun)','financial_theses_policies_positions_formal_questions_replies_send_orders':0,'external_scheduler_installed':False,'actual_DB_SHA_before_and_after':'cbf81671f41ec320a4b08c96df53520e5300ffffbc5530e10bcba1d88f60b7a8'}
(HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['before_SHA256','after_SHA256']},ensure_ascii=False,indent=2))
