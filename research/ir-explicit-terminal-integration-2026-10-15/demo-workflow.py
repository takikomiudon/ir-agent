from pathlib import Path
from copy import deepcopy
from datetime import datetime
import json,sys
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'src'),str(root/'tests')]
from ir_agent.harness import Harness
from ir_agent.store import Store
from ir_agent.models import json_text
from test_explicit_terminal_integration import explicit_plan

value=explicit_plan()
bundle=json.loads((root/'examples/demo.json').read_bytes())
bundle['theses']=[value['thesis']];bundle['sources'].append(value['sources'][1])
store=Store(':memory:');h=Harness(store)
h.ingest(bundle,now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
h.register_decision_policy(value['policy'],now=datetime.fromisoformat('2026-10-09T10:00:00+09:00'))
q=value['question'];q['decision_contract']={'policy_id':value['policy']['id'],'policy_version':1,
 'quote':value['quote'],'synthetic':True,'synthetic_position':{'held':True,'observed_at':'2026-10-09T09:59:00+09:00'}}
h.add_question(q,now=datetime.fromisoformat('2026-10-09T10:01:00+09:00'))
old_thesis=json_text(store.thesis('demo-services'));old_question=store.connection.execute('SELECT data FROM questions WHERE id=?',(q['id'],)).fetchone()[0]
h.mark_sent(q['id'],'2026-10-09T10:05:00+09:00',now=datetime.fromisoformat('2026-10-09T10:06:00+09:00'))
h.add_reply(json.loads((root/'examples/reply.json').read_bytes()),now=datetime.fromisoformat('2026-10-09T16:00:00+09:00'))
price=deepcopy(value['sources'][1]);price.update(id='synthetic-explicit-terminal-reply-price',retrieved_at='2026-10-09T16:59:00+09:00')
price['metadata'].update(price_jpy='1600',observed_at=price['retrieved_at'])
h.ingest({'schema_version':1,'sources':[price]},now=datetime.fromisoformat('2026-10-09T16:59:00+09:00'))
quote=deepcopy(value['quote']);quote.update(source_id=price['id'],price_jpy='1600',observed_at=price['retrieved_at'],retrieved_at=price['retrieved_at'])
evaluation=json.loads((root/'examples/reply-evaluation.json').read_bytes());evaluation.update(expected_thesis_version=1,decision_quote=quote)
result=h.evaluate_reply(evaluation,now=datetime.fromisoformat('2026-10-09T17:00:00+09:00'))
assert result['applied'] is True and result['action']=='exit_review'
current=store.thesis('demo-services');assert current['version']==2
assert all(s['method']=='dcf_explicit_terminal' for s in current['valuation']['scenarios'])
assert json_text(json.loads(store.connection.execute('SELECT data FROM theses WHERE company_id=? AND version=1',('demo-services',)).fetchone()[0]))==old_thesis
# mark-sent changes lifecycle columns, not the frozen question data.
assert store.connection.execute('SELECT data FROM questions WHERE id=?',(q['id'],)).fetchone()[0]==old_question
report={'synthetic':True,'database':':memory:','external_send_performed':False,'orders':0,
 'workflow':'synthetic precommit, recorded fictional send, synthetic reply, fresh synthetic quote, atomic evaluation',
 'applied':result['applied'],'action':result['action'],'thesis_version':current['version'],
 'methods':sorted({s['method'] for s in current['valuation']['scenarios']}),
 'old_thesis_version_unchanged':True,'old_question_data_unchanged':True,'saved_review_thesis_version':store.decision_review(result['decision_review_id'])['thesis_version'],
 'author_numeric_policy_adopted_for_actual_company':False}
assert report['saved_review_thesis_version']==2
print(json.dumps(report,ensure_ascii=False,indent=2))
