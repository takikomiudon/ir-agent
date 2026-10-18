"""Finite current-state verification. SQLite mode=ro; no Store/network."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
DB=ROOT/'data/ir-research-2026-10-15.sqlite3'
EXPECTED='cbf81671f41ec320a4b08c96df53520e5300ffffbc5530e10bcba1d88f60b7a8'
digest=lambda p:sha256(p.read_bytes()).hexdigest()
assert digest(DB)==EXPECTED
codefile=ROOT/'research/ir-public-information-review-binding-integration-2026-10-16/fixed-code-under-test-pins.json'
codepins=json.loads(codefile.read_bytes())
assert len(codepins)==44 and all(digest(ROOT/p)==s for p,s in codepins.items())
with closing(sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)) as c:
 c.execute('PRAGMA query_only=ON'); assert c.execute('PRAGMA query_only').fetchone()[0]==1
 c.execute('BEGIN')
 tables=['companies','sources','record_availability','source_classifications','jobs','job_attempts','job_attempt_events','job_request_receipts','qualitative_case_versions','theses','decision_policies','position_declarations','questions','replies','research_decision_reviews']
 counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
 types=c.execute("SELECT json_extract(data,'$.source_type'),count(*),count(DISTINCT company_id) FROM sources GROUP BY json_extract(data,'$.source_type')").fetchall()
 financial=c.execute("SELECT count(DISTINCT s.company_id) FROM sources s JOIN source_classifications a ON a.source_id=s.id JOIN (SELECT source_id,max(version) version FROM source_classifications GROUP BY source_id)b ON a.source_id=b.source_id AND a.version=b.version WHERE json_extract(a.data,'$.financial_content')=1").fetchone()[0]
 jobs=c.execute("SELECT json_extract(packet,'$.kind'),status,count(*) FROM jobs GROUP BY json_extract(packet,'$.kind'),status").fetchall()
 bases=c.execute("SELECT basis,count(*) FROM record_availability WHERE entity_type='source' GROUP BY basis").fetchall()
 heads=[json.loads(r[0]) for r in c.execute('SELECT a.data FROM qualitative_case_versions a JOIN (SELECT case_id,max(version) version FROM qualitative_case_versions GROUP BY case_id)b ON a.case_id=b.case_id AND a.version=b.version')]
 dates={}
 for row in heads:
  m=row['management_review']; key=m['date']+' '+m['timezone']; dates[key]=dates.get(key,0)+1
 natives={}
 for code,n in [('2341',2),('2410',5)]:
  f=ROOT/f'research/ir-case-studies-2026-10-15/{code}/native-case-setup-2026-10-16/actual-inputs/actual-case.json'
  saved=json.loads(f.read_bytes()); native=saved['record']
  assert next(row for row in heads if row['company_id']=='jp:'+code)==native
  assert saved['version']==1 and saved['config_revision']==1 and len(native['reviewed_sources'])==n
  source_count=c.execute('SELECT count(*) FROM sources WHERE company_id=?',('jp:'+code,)).fetchone()[0]
  assert source_count==n
  natives[code]={'saved_actual_path':str(f.relative_to(ROOT)),'saved_actual_sha256':digest(f),'whole_current_record_equals_saved_actual':True,'version':1,'config_revision':1,'reviewed_sources':n,'actual_sources':source_count}
 pending=c.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0]
 c.rollback()
assert counts==dict(companies=1819,sources=210,record_availability=210,source_classifications=209,jobs=117,job_attempts=114,job_attempt_events=228,job_request_receipts=114,qualitative_case_versions=48,theses=0,decision_policies=0,position_declarations=0,questions=0,replies=0,research_decision_reviews=0)
assert types==[('market_data',1,1),('public_disclosure',209,36)] and financial==31
assert jobs==[('intake','completed',96),('qualitative_review','completed',21)]
assert bases==[('legacy_presence',28),('trusted_insert',182)]
assert len(heads)==26 and sum(len(r['reviewed_sources']) for r in heads)==149
assert dates=={'2027-01-15 Asia/Tokyo':12,'2027-01-16 Asia/Tokyo':14} and pending==0
assert digest(DB)==EXPECTED
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'connection':'sqlite mode=ro/query_only/contextlib.closing; no Store','actual_DB_SHA_before':EXPECTED,'actual_DB_SHA_after':digest(DB),'counts':counts,'source_types':types,'financial_content_companies':financial,'job_kind_status_counts':jobs,'availability_bases':bases,'case_heads':len(heads),'reviewed_sources':sum(len(r['reviewed_sources']) for r in heads),'management_date_counts':dates,'native_current_whole_checks':natives,'pending_leased':pending,'fixed_code_under_test_pin_count':44,'all44_current_code_SHA_match':True,'code_pins_file_sha256':digest(codefile),'DB_writes':0,'GET':0,'tests_rerun':0}
(HERE/'readonly-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
