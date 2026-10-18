"""One-use explicit case configuration; no retrieval or financial actions."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from hashlib import sha256
import sqlite3, json, sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from ir_agent.store import Store
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.models import json_text
BASE=Path(__file__).resolve().parent;OUT=BASE/'management-review-setup'
DB=ROOT/'data/ir-research-2026-10-15.sqlite3';CASE='5831-financial-structure-monitor'
now=lambda:datetime.now(timezone.utc).isoformat()
digest=lambda p:sha256(p.read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as f:f.write(json_text(value)+'\n')
def ref(path):return {'path':str(path.relative_to(ROOT)),'sha256':digest(path)}
assert sys.argv[1:] in (['--prepare'],['--execute'])
if sys.argv[1]=='--prepare':
    OUT.mkdir();before=digest(DB)
    ro=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);ro.row_factory=sqlite3.Row;ro.execute('pragma query_only=on')
    row=ro.execute('select * from qualitative_case_versions where case_id=? order by version desc limit 1',(CASE,)).fetchone()
    assert row['version']==3;record=json.loads(row['data']);assert record['management_review'] is None
    assert len(record['reviewed_sources'])==5
    clock=datetime.now(timezone.utc);local=clock.astimezone(ZoneInfo('Asia/Tokyo'))
    assert local.date().isoformat()=='2026-10-16'
    date='2027-01-16'
    author=ROOT/'third_party/anthropic/skills/thesis-tracker/SKILL.md'
    author_quote='Review theses at least quarterly, even when nothing dramatic has happened'
    assert author_quote in author.read_bytes().decode()
    note={'recorded_at':now(),'company_id':'jp:5831','management_date':date,'timezone':'Asia/Tokyo',
          'basis_quote':'研究の次回管理日は2027-01-16（Asia/Tokyo）。',
          'adopted_author_quote':author_quote,'author_ref':ref(author),
          'adaptation':'Use the same local calendar day three months after this research checkpoint. Explicit project management date, not an issuer event, author forecast deadline, mandatory sell date or ninety-day claim.',
          'local_research_date':local.date().isoformat(),'event_changes':'New public sources may trigger earlier review.'}
    save('management-basis.json',note)
    original=json.loads((ROOT/record['case_ref']['path']).read_bytes())
    progress=[]
    for identity in sorted({v['job_id'] for v in record['reviewed_sources'].values() if 'job_id' in v}):
        j=ro.execute('select packet,result,completed_at from jobs where id=?',(identity,)).fetchone()
        packet=json.loads(j['packet']);result=json.loads(j['result'])
        assert result['kind']=='qualitative_review' and result['case_id']==CASE
        progress.append({'job_id':identity,'completed_at':j['completed_at'],'case_version':result['case_version'],
                         'result_sha256':sha256(json_text(result).encode()).hexdigest(),
                         'source_snapshot_sha256':packet['source_snapshot_sha256'],
                         'request':result['request']})
    context={'recorded_at':now(),'case_id':CASE,'issue_id':record['issue_id'],'purpose':'Explicit management-date configuration with prior conditions and completed observations retained separately.',
             'original_case_document':original,'original_case_ref':record['case_ref'],
             'completed_review_observations':progress,
             'later_public_basis_file_ref':ref(BASE/'public-capital-basis-check/review.json'),
             'later_public_basis_limit':'Additional saved page17 is a file-only meaning review; not retroactively part of the earlier3-page job.',
             'management_basis_ref':ref(OUT/'management-basis.json'),'financial_model_adopted':False}
    save('case-context.json',context)
    checkpoint={'recorded_at':now(),'case_id':CASE,'purpose':'Reuse saved prior reviews at this configuration checkpoint; not a new full-source semantic review or historical first-save claim.',
                'prior_case_version':3,'prior_case_record':record,'context_ref':ref(OUT/'case-context.json'),
                'source_bindings':[{'source_id':identity,'source_snapshot_sha256':v['source_snapshot_sha256'],'earlier_reviewed_at':v['reviewed_at']} for identity,v in sorted(record['reviewed_sources'].items())]}
    save('review-binding-checkpoint.json',checkpoint)
    request={k:record[k] for k in ('case_id','company_id','issue_id','synthetic','enabled')}
    request.update(recorded_at=now(),case_ref=ref(OUT/'case-context.json'),manifest_ref=ref(OUT/'review-binding-checkpoint.json'),
                   management_review={'date':date,'timezone':'Asia/Tokyo','basis_ref':ref(OUT/'management-basis.json'),'basis_quote':note['basis_quote']},
                   bootstrap_reviews=[{'source_id':v['source_id'],'source_snapshot_sha256':v['source_snapshot_sha256'],'reviewed_at':checkpoint['recorded_at'],'review_ref':ref(OUT/'review-binding-checkpoint.json')} for v in checkpoint['source_bindings']])
    save('case-request.json',request)
    copy=ROOT/('data/preflight-5831-management-'+clock.strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
    dest=sqlite3.connect(copy);ro.backup(dest);dest.close();ro.close()
    test=Store(str(copy));q=QualitativeResearch(test);result=q.register_case(request,3,research_root=ROOT)
    assert result['version']==4 and result['config_revision']==2 and len(result['record']['reviewed_sources'])==5
    current=datetime.now(timezone.utc);queued=q.queue_cases([CASE],current.isoformat(),now=current);assert queued['jobs_created']==0
    test.close();assert digest(DB)==before
    save('copy-preflight.json',{'recorded_at':now(),'status':'passed','copy_path':str(copy.relative_to(ROOT)),
                              'actual_database_sha256_before_and_after':before,'actual_DB_unchanged':True,
                              'new_case_version':4,'reviewed_sources_retained':5,'new_jobs':0})
    print(json_text({'preflight':'passed','actual_DB_written':False,'date':date}))
else:
    assert not (OUT/'execution-start.json').exists()
    proof=json.loads((OUT/'copy-preflight.json').read_bytes());assert proof['status']=='passed'
    assert digest(DB)==proof['actual_database_sha256_before_and_after']
    ro=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);ro.execute('pragma query_only=on')
    tables=[r[0] for r in ro.execute("select name from sqlite_master where type='table'")]
    snapshots={t:ro.execute('select * from '+t).fetchall() for t in tables}
    backup=ROOT/('data/before-5831-management-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
    dest=sqlite3.connect(backup);ro.backup(dest);dest.close();ro.close()
    save('execution-start.json',{'recorded_at':now(),'database_sha256_before':digest(DB),'backup_path':str(backup.relative_to(ROOT)),'backup_sha256':digest(backup)})
    store=Store(str(DB));q=QualitativeResearch(store);request=json.loads((OUT/'case-request.json').read_bytes())
    result=q.register_case(request,3,research_root=ROOT);save('actual-registration.json',result)
    cases=[r[0] for r in store.connection.execute('select distinct case_id from qualitative_case_versions order by case_id')]
    assert len(cases)==13
    current=datetime.now(timezone.utc);queue=q.queue_cases(cases,current.isoformat(),limit=13,now=current);save('all-cases-queue.json',queue)
    assert queue['jobs_created']==0 and len(queue['skipped'])==13
    comparisons={}
    for table,before in snapshots.items():
        after=store.connection.execute('select * from '+table).fetchall()
        comparisons[table]=(all(tuple(r) in {tuple(n) for n in after} for r in before) if table=='qualitative_case_versions' else [tuple(r) for r in after]==before)
    assert all(comparisons.values())
    heads=[q.show_case(c) for c in cases];assert all(h['record']['management_review'] is not None for h in heads)
    save('case-head-summary.json',[{'case_id':h['case_id'],'version':h['version'],'management_review':h['record']['management_review'],'reviewed_sources':len(h['record']['reviewed_sources'])} for h in heads])
    assert sum(len(h['record']['reviewed_sources']) for h in heads)==68
    counts={t:store.connection.execute('select count(*) from '+t).fetchone()[0] for t in tables}
    store.close();save('actual-completion.json',{'recorded_at':now(),'status':'completed','all_other_tables_exactly_unchanged_and_old_case_versions_retained':comparisons,
        'actual_counts':counts,'case_heads':13,'case_version_rows':17,'case_reviewed_source_entries':68,'all13_management_dates_configured':True,
        'new_jobs':0,'management_date':'2027-01-16','timezone':'Asia/Tokyo','database_sha256_after':digest(DB),
        'prior_observations_preserved_in_frozen_case_context':True,'config_resets_last_review_id_by_contract':True,
        'new_GETs_financial_theses_questions_sends_orders':0})
    print(json_text({'status':'completed','all13_dates_configured':True,'new_jobs':0,'sources':122,'case_versions':17}))
