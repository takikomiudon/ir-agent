"""Record the bounded two-page issuer comparison and finish its existing lease."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json, shutil, sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.qualitative_research import QualitativeResearch
HERE = Path(__file__).resolve().parent
def load(n): return json.loads((HERE / n).read_text())
def save(n,v):
    with (HERE / n).open('x') as f: f.write(json_text(v)+'\n')
def now(): return datetime.now(timezone.utc).isoformat()
source = load('source-only-bundle.json')['sources'][0]
job = load('qualitative-job.json'); packet = job['packet']; content = source['content']
pages = content.split('\f'); images = HERE / 'images'; images.mkdir(exist_ok=True)
for page in (1,2): shutil.copyfile('/tmp/daidan-issuer-%02d.png' % page, images / ('page-%d.png' % page))
specs = [('issuer-date-basis',1,0,10), ('issuer-quarter-split-note',1,32,36)]
# Exact blocks are selected from the already-inspected physical pages.
blocks = [
    ('issuer-title-date', 1, pages[0][:pages[0].index('コード番号')]),
    ('issuer-quarter-split-note', 1, pages[0][pages[0].index('（注）当社は'):pages[0].index(' （２）連結財政状態')]),
    ('issuer-annual-plan', 2, pages[1][:pages[1].index('（参考）予想受注工事高')]),
    ('issuer-plan-unrevised', 2, '（注）直近に公表されている業績予想からの修正の有無：無'),
    ('issuer-shares-and-trust-notes', 2, pages[1][pages[1].index('    （４）発行済株式数'):pages[1].index('※    添付される四半期')])]
quotes=[]
for identity,page,quote in blocks:
    start=content.index(quote); image=images/('page-%d.png'%page)
    quotes.append({'id':identity,'source_id':source['id'],'pdf_physical_page':page,
        'quote':quote,'source_character_start':start,'source_character_end':start+len(quote),
        'source_UTF8_byte_start':len(content[:start].encode()),
        'source_UTF8_byte_end':len(content[:start+len(quote)].encode()),
        'offset_unit':'Zero-based Unicode code points and UTF8 bytes, half-open',
        'image_path':str(image.relative_to(ROOT)),'image_sha256':sha256(image.read_bytes()).hexdigest()})
save('quotes.json',quotes)
author_quotes=json.loads((HERE.parent/'first-author-report/quotes.json').read_text())
comparison=[q for q in author_quotes if q['id']=='company-guidance-QUICK-EPS-row-and-note']
assert len(comparison)==1
review={'recorded_at':now(),'company_id':'jp:1980','source_id':source['id'],
    'review_scope':{'physical_pages':[1,2],'images_inspected':[1,2],
        'all_other_11_pages':'mechanically extracted only; not semantically reviewed'},
    'issuer_original':{'published_date_as_printed':'2026-08-05','published_time':None,
        'accounting_basis':'Japanese GAAP consolidated', 'annual_period_start':'2026-04-01',
        'annual_period_end':'2027-03-31','parent_net_income_forecast_million_JPY':27300,
        'EPS_forecast_JPY_per_share':'211.42','forecast_revision_as_printed':'none',
        'forecast_exact_share_denominator':'not explicitly established in these two pages'},
    'external_report_comparison':{'report_date_as_printed':'2026-09-14',
        'source_id':'case-public:4df33a50a3198dfa36142fd1c839f0d28598ff26d911ed83b31fe17d2884645f',
        'parent_net_income_forecast_million_JPY':27300,'EPS_display_JPY_per_share':'210.89',
        'EPS_provenance':'QUICK calculation from company net income forecast; not an independent net-income forecast',
        'previously_reviewed_quote':comparison[0],
        'comparison_limit':'Same displayed annual company NI; differing per-share display. Exact issuer/QUICK denominator and observation-date reconciliation not established. Do not infer an earnings disagreement or forecast skill.'},
    'split_and_share_scope':'Issuer discloses 2026-01-01 1-to-3 split and retrospective quarter EPS/average-share notes. Period-end issued shares include treasury; quarter average shares are not the annual forecast denominator by assumption.',
    'case_observation':'Supports preserving issuer-original EPS and provider-calculated EPS as distinct provenance. No business bull/bear conclusion.',
    'IR_candidate_disposition':'Do not ask the already-public annual NI, annual period, accounting basis, or original EPS. Exact denominator is unresolved but not required for this source-applicability review.',
    'financial_inputs_verified':False,'model_adopted':False,'financial_thesis_created':False,
    'current_price_fair_multiple_target_exit_rule':'not supplied or inferred',
    'independent_code_or_semantic_review_completed':False,
    'new_GETs':2,'external_sends_orders':0}
save('review.json',review)
basis=next(q['quote'] for q in quotes if q['id']=='issuer-annual-plan')
result={'summary':'会社原EPS211.42円とQUICK算出EPS210.89円を出所別に区別した。会社予想純利益はともに273億円。',
    'recorded_at':now(),'source_reviews':[{'source_id':source['id'],
        'snapshot_sha256':packet['source_snapshot_sha256'][source['id']],
        'read_state':'reviewed','outcome':'supports','basis_quote':basis,
        'rationale':'会社原予想の年度・連結日本基準・純利益273億円・EPS211.42円を物理p1/2の本文と画像で確認。外部レポートのQUICK換算EPS210.89円と区別する。全文読了や予想達成を意味しない。'}],
    'case_observation':{'issue_id':'1980-source-EPS-basis','outcome':'supports',
        'rationale':'会社原EPSと外部機関の換算EPSを区別する既存論点を支持する。純利益表示の一致を確認したが、厳密な株数対応は未確定。売買方向・利益予想の優劣は判断しない。',
        'evidence_source_ids':[source['id']]},'management_review_update':{'mode':'retain'}}
save('qualitative-result-input.json',result)
store=Store(str(ROOT/'data/ir-research-2026-10-15.sqlite3'));h=Harness(store);q=QualitativeResearch(store)
assert store.source(source['id'])==source
completed=h.complete(job['id'],'parent-1980-issuer-review',result,expected_attempt=1)
save('qualitative-completed.json',completed);assert completed['status']=='completed'
case=q.show_case(packet['case_id']);save('case-after.json',case)
assert case['version']==2 and len(case['record']['reviewed_sources'])==3
current=datetime.now(timezone.utc);after=q.queue_cases([packet['case_id']],current.isoformat(),now=current)
save('after-review-queue.json',after);assert after['jobs_created']==0
before=load('execution-start.json')['before_table_rows'];unchanged={}
for table in ('companies','sources','source_classifications','qualitative_case_versions'):
    rows={tuple(r) for r in store.connection.execute('SELECT * FROM '+table)}
    unchanged[table]=all(tuple(r) in rows for r in before[table]);assert unchanged[table]
counts={t:store.connection.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in before}
for table in ('theses','questions','replies','decision_policies','position_declarations'):
    assert counts[table]==0
assert store.connection.execute("SELECT count(*) FROM jobs WHERE status<>'completed'").fetchone()[0]==0
availability=dict(store.connection.execute("SELECT basis,count(*) FROM record_availability WHERE entity_type='source' GROUP BY basis"))
receipt=dict(store.connection.execute("SELECT * FROM record_availability WHERE entity_type='source' AND entity_id=?",(source['id'],)).fetchone())
store.close()
save('actual-completion.json',{'recorded_at':now(),'actual_counts':counts,
    'source_availability_counts':availability,'new_source_first_save_receipt':receipt,
    'old_rows_preserved':unchanged,'case_head_version':case['version'],'case_reviewed_sources':3,
    'after_review_new_jobs':0,'qualitative_job_id':job['id'],
    'database_main_sha256_after':sha256((ROOT/'data/ir-research-2026-10-15.sqlite3').read_bytes()).hexdigest(),
    'measurement_scope':'One real intake and one real qualitative review lease; not full research capacity or investment performance.',
    'financial_inputs_verified':False,'model_adopted':False,'external_sends_orders':0})
print(json_text({'completed':job['id'],'case_version':2,'actual_counts':counts}))
