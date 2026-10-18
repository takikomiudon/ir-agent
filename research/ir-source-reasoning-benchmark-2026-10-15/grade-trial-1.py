"""Grade this fixed research exercise, without changing keys or any database."""
import hashlib
from datetime import datetime,timezone
from pathlib import Path
from ir_agent.models import parse_json

base=Path(__file__).resolve().parent
def read(name):return parse_json((base/name).read_bytes().decode('utf-8'))
def sha(name):return hashlib.sha256((base/name).read_bytes()).hexdigest()
freeze=read('root-pretrial-freeze.json')
assert sha('input-cases.json')==freeze['input_sha256']
assert sha('answer-key.json')==freeze['answer_key_sha256']
inputs=read('input-cases.json');key=read('answer-key.json')
answers=read('trial-1-answers.json');execution=read('trial-1-execution.json')
expected={c['case_id']:c for c in key['cases']}
cases={c['case_id']:c for c in inputs['cases']}
assert len(expected)==len(cases)==8 and expected.keys()==cases.keys()
assert isinstance(answers,dict) and set(answers)=={'answers'}
assert isinstance(answers['answers'],list) and len(answers['answers'])==8
assert execution['input_sha256']==freeze['input_sha256']
assert datetime.fromisoformat(freeze['recorded_at'])<=datetime.fromisoformat(execution['started_at'])<=datetime.fromisoformat(execution['finished_at'])<=datetime.now(timezone.utc)
assert not execution['answer_key_or_other_research_files_read']
assert not execution['prior_root_chat_received']
assert execution['external_get_count']==execution['database_operation_count']==execution['investment_decision_count']==0
confusion={x:{y:0 for y in inputs['verdict_enum']} for x in inputs['verdict_enum']}
rows=[];seen=set()
for answer in answers['answers']:
    assert set(answer)=={'case_id','verdict','reason','excerpt_ids'}
    cid=answer['case_id'];assert cid in cases and cid not in seen;seen.add(cid)
    verdict=answer['verdict'];assert verdict in inputs['verdict_enum']
    assert isinstance(answer['reason'],str) and answer['reason'].strip()
    citations=answer['excerpt_ids'];allowed={e['id'] for e in cases[cid]['excerpts']}
    assert isinstance(citations,list) and citations and all(isinstance(x,str) for x in citations)
    assert len(citations)==len(set(citations)) and set(citations)<=allowed
    sufficient=any(set(group)<=set(citations) for group in expected[cid]['sufficient_excerpt_id_sets'])
    correct=verdict==expected[cid]['verdict']
    confusion[expected[cid]['verdict']][verdict]+=1
    rows.append({'case_id':cid,'expected_verdict':expected[cid]['verdict'],'actual_verdict':verdict,
      'verdict_matches_fixed_key':correct,'all_cited_excerpt_ids_exist_in_case':True,
      'contains_key_sufficient_excerpt_set':sufficient})
assert seen==expected.keys()
result={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
 'status':'fixed_eight_case_skill_enabled_regression_only','case_count':8,
 'exact_verdict_matches':sum(x['verdict_matches_fixed_key'] for x in rows),
 'case_local_citation_checks_passed':8,'sufficient_citation_set_matches':sum(x['contains_key_sufficient_excerpt_set'] for x in rows),
 'rows':rows,'confusion_counts':confusion,
 'artifact_SHA256':{n:sha(n) for n in ['input-cases.json','answer-key.json','root-pretrial-freeze.json','trial-1-answers.json','trial-1-execution.json','independent-key-review.json']},
 'grading_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'key_unchanged_from_before_trial':True,'execution_scope_self_reported':True,
 'related_operational_example_exposure':execution['possible_related_example_exposure'],
 'generalization_holdout_or_model_performance_verified':False,
 'financial_forecast_accuracy_calibration_or_investment_performance_verified':False,
 'new_GETs':0,'DB_access':0,'key_changes':0,'investment_actions':0}
destination=base/'trial-1-grade.json';assert not destination.exists()
import json
destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['case_count','exact_verdict_matches','case_local_citation_checks_passed','sufficient_citation_set_matches','key_unchanged_from_before_trial']}))
