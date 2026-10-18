"""Synthetic SQLite :memory: reproduction; no real DB, GET, or production edits.

Expected assertions describe the reviewed pre-fix checkpoint, not desired behavior.
Uses the existing synthetic numerical fixture without inventing policy thresholds.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime
import sys, json, hashlib
ROOT=Path('/workspace/ir-agent')
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_decision import plan
from ir_agent.harness import Harness
from ir_agent.store import Store
from ir_agent.information_review import add_assessment, source_assessments
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.models import json_text

stamp=lambda s:datetime.fromisoformat(s)
load=lambda p:json.loads((ROOT/p).read_bytes())
sha=lambda x:hashlib.sha256(x).hexdigest()

def run_case(mode):
    value=plan();s=Store(':memory:');h=Harness(s)
    def snapshot():return '\n'.join(s.connection.iterdump())
    def quote(name,t):
        source=deepcopy(value['sources'][1]);source.update(id=name,retrieved_at=t)
        source['metadata'].update(observed_at=t)
        h.ingest({'schema_version':1,'sources':[source]},now=stamp(t))
        q=deepcopy(value['quote']);q.update(source_id=name,observed_at=t,retrieved_at=t)
        return q
    bundle=load('examples/demo.json');bundle['theses']=[value['thesis']];bundle['sources'].append(value['sources'][1])
    h.ingest(bundle,now=stamp('2026-10-09T10:00:00+09:00'))
    h.register_decision_policy(value['policy'],now=stamp('2026-10-09T10:00:00+09:00'))
    q1=deepcopy(value['question'])
    q1['decision_contract']={'policy_id':value['policy']['id'],'policy_version':1,'quote':value['quote'],'synthetic':True,
      'synthetic_position':{'held':True,'observed_at':'2026-10-09T09:59:00+09:00'}}
    h.add_question(q1,now=stamp('2026-10-09T10:01:00+09:00'))
    h.mark_sent(q1['id'],'2026-10-09T10:05:00+09:00',now=stamp('2026-10-09T10:05:00+09:00'))
    reply1=load('examples/reply.json');h.add_reply(reply1,now=stamp(reply1['received_at']))
    quote1=quote('price-first-application','2026-10-09T17:00:00+09:00')
    e1=load('examples/reply-evaluation.json');e1.update(expected_thesis_version=1,decision_quote=quote1)
    applied1=h.evaluate_reply(e1,now=stamp('2026-10-09T17:01:00+09:00'))
    assert applied1['applied'] and s.thesis('demo-services')['version']==2
    original_thesis=deepcopy(s.thesis('demo-services'));original_reply_source=deepcopy(s.source('reply:'+reply1['id']))
    correction={'reply_id':reply1['id'],'expected_version':0,'information_status':'unclear',
      'basis_quote':reply1['raw_text'][:10],'rationale':'Synthetic public-basis review withdrawn; no private text or new financial assumption.',
      'recorded_at':'2026-10-09T17:02:00+09:00'}
    add_assessment(s,correction,now='2026-10-09T17:02:00+09:00')
    quote2=quote('price-second-question','2026-10-09T17:05:00+09:00')
    q2=deepcopy(q1);q2.update(id='second-question',topic='second-synthetic-review',thesis_version=2,
      created_at='2026-10-09T17:06:00+09:00',evidence_ids=original_thesis['evidence_ids'])
    q2['decision_contract']['quote']=quote2
    before_plan=snapshot();saved=h.add_question(q2,now=stamp('2026-10-09T17:06:00+09:00'))
    assert saved['decision_contract']['preflight']['question_value']=='decision_distinguishing'
    rows=source_assessments(s,[x['id'] for x in DecisionLifecycle(s).sources_for(original_thesis,quote2)],as_of=q2['created_at'])
    assert rows[reply1['id']]['information_status']=='unclear'
    sent=h.mark_sent(q2['id'],'2026-10-09T17:07:00+09:00',now=stamp('2026-10-09T17:07:00+09:00'))
    assert sent['status']=='awaiting_reply'
    reply2=deepcopy(reply1);reply2.update(id='second-reply',question_id=q2['id'],received_at='2026-10-09T17:08:00+09:00')
    h.add_reply(reply2,now=stamp(reply2['received_at']))
    if mode=='own_reply_correction_control':
        own=deepcopy(correction);own.update(reply_id=reply2['id'],recorded_at='2026-10-09T17:09:00+09:00')
        add_assessment(s,own,now='2026-10-09T17:09:00+09:00')
    e2=deepcopy(e1);e2.update(reply_id=reply2['id'],branch_id='persistent',basis_quote='人件費は継続的な費用です。',
      recorded_at='2026-10-09T17:10:00+09:00',expected_thesis_version=2,decision_quote=quote2,
      rationale='Synthetic application of the existing persistent branch; no new threshold or real investment assumption.')
    if mode=='unknown_quote_rollback_control':e2['decision_quote']={'source_id':'not-ingested'}
    before=snapshot();before_source=deepcopy(s.source('reply:'+reply1['id']));before_count=h.status();caught=None
    try:result=h.evaluate_reply(e2,now=stamp(e2['recorded_at']))
    except ValueError as error:caught=str(error);result=None
    after=snapshot();latest=s.thesis('demo-services')
    assert s.source('reply:'+reply1['id'])==before_source==original_reply_source
    assert s.reply(reply1['id'])==reply1
    assert s.connection.execute('SELECT data FROM theses WHERE company_id=? AND version=2',('demo-services',)).fetchone()[0]==json_text(original_thesis)
    base=lambda t:next(x for x in t['valuation']['scenarios'] if x['name']=='base')['inputs']['eps_jpy']
    summary={'mode':mode,'old_dependency_latest_status':rows[reply1['id']]['information_status'],
       'second_question_preflight':saved['decision_contract']['preflight']['question_value'],
       'second_question_mark_sent_status':sent['status'],'before_thesis_version':original_thesis['version'],
       'after_thesis_version':latest['version'],'before_base_eps_jpy':base(original_thesis),'after_base_eps_jpy':base(latest),
       'old_source_and_thesis_version_immutable':True,'old_reply_immutable':True,
       'original_reply_information_status':reply1['information_status'],
       'new_reply_declared_information_status':reply2['information_status'],
       'second_evaluation_request':e2,'dependent_information_reviews':rows,'exception':caught,
       'before_after_db_dump_equal':before==after,'before_counts':before_count,'after_counts':h.status()}
    if mode=='dependent_reply_correction':
        assert result['applied'] is True and result['information_status']=='public_clarification'
        assert latest['version']==3 and base(latest)=='40' and base(original_thesis)=='70'
        assert result['action']=='unresolved'
        assert 'reply_information_corrected' in result['decision_review']['result']['reason_codes']
        assert result['decision_review']['result']['information_reviews'][reply1['id']]['information_status']=='unclear'
        summary['actual_result']=result
        summary['reproduced_defect']='Current decision is held correctly, but a new persisted financial-thesis version is already written from a question sent over a held dependency.'
    elif mode=='own_reply_correction_control':
        assert result['applied'] is False and result['status']=='held_for_review'
        assert result['information_status']=='unclear' and latest==original_thesis
        summary['actual_result']=result
    else:
        assert caught and 'Unknown source' in caught
        assert before==after and latest==original_thesis
        summary['correct_atomic_rollback']=True
    s.close();return summary

if __name__=='__main__':
 out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/ir_reply_runtime_gap_repro.json')
 data={'schema_version':1,'status':'one_dependency_classification_connection_gap_reproduced',
   'scope':'Three synthetic :memory: cases only; no real DB or network.',
   'cases':[run_case(m) for m in ['dependent_reply_correction','own_reply_correction_control','unknown_quote_rollback_control']]}
 out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':data['status'],'cases':[{'mode':c['mode'],'preflight':c['second_question_preflight'],
  'sent':c['second_question_mark_sent_status'],'before_version':c['before_thesis_version'],'after_version':c['after_thesis_version'],
  'base_eps':[c['before_base_eps_jpy'],c['after_base_eps_jpy']],'exception':c['exception']} for c in data['cases']]},ensure_ascii=False))
