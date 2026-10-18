"""Two isolated CLI probes; never opens the actual research database."""
from contextlib import contextmanager,redirect_stdout,redirect_stderr
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
import json,sqlite3,os,sys,io
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'src'))
from ir_agent.cli import main

@contextmanager
def cwd(path):
 old=Path.cwd();os.chdir(path)
 try:yield
 finally:os.chdir(old)

def invoke(folder):
 stdout,stderr=io.StringIO(),io.StringIO()
 with cwd(folder),redirect_stdout(stdout),redirect_stderr(stderr):
  code=main(['normalize-facts',str(R/'examples/disclosed-facts.json')])
 return code,stdout.getvalue(),stderr.getvalue()

def run():
 records=[]
 with TemporaryDirectory(prefix='ir-pure-cli-newdb-')as tmp:
  folder=Path(tmp);database=folder/'data/ir-agent.sqlite3';assert not database.exists()
  code,output,error=invoke(folder);assert code==0 and error=='' and database.exists()
  result=json.loads(output)
  with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)as c:
   tables=[r[0]for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
   counts={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0]for t in ['sources','theses','companies']}
   schema=c.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
  records.append({'case':'valid_normalize_facts_creates_default_database','CLI_arguments':['normalize-facts','<repo>/examples/disclosed-facts.json'],'before_default_DB_exists':False,'exit_code':code,'stderr':error,'after_default_DB_exists':True,'default_DB_relative_path':'data/ir-agent.sqlite3','DB_bytes':database.stat().st_size,'schema_version':schema,'tables_created':tables,'table_count':len(tables),'core_domain_row_counts':counts,'normalized_bundle_sources':len(result['sources']),'financial_input_adoption':False,'temporary_directory_removed_after_probe':True})
 with TemporaryDirectory(prefix='ir-pure-cli-blockeddb-')as tmp:
  folder=Path(tmp);blocker=folder/'data';blocker.write_bytes(b'synthetic data-directory blocker');before=sha256(blocker.read_bytes()).hexdigest()
  code,output,error=invoke(folder);assert code==1 and output=='' and 'Traceback'not in error and sha256(blocker.read_bytes()).hexdigest()==before
  records.append({'case':'same_valid_normalization_fails_before_calculation_when_default_DB_parent_is_a_file','CLI_arguments':['normalize-facts','<repo>/examples/disclosed-facts.json'],'exit_code':code,'stdout_empty':True,'stderr':error.replace(str(folder),'<temporary_cwd>'),'default_DB_created':False,'blocker_bytes_unchanged':True,'type_of_failure':'Default database parent data is a regular file; mkdir raises FileExistsError. This is a deterministic path nonwritability/collision, not a tested chmod/EACCES scenario.','same_valid_fixture_as_success_case':True,'temporary_directory_removed_after_probe':True})
 return {'schema_version':1,'status':'one_CLI_DB_side_effect_reproduced_in_two_isolated_cases','cases':records,'execution':{'temporary_case_count':2,'actual_DB_accesses':0,'network_GETs':0,'production_test_or_old_file_changes':0,'full_suite_runs':0,'financial_decision_or_IR':0}}
if __name__=='__main__':
 result=run();out=Path(sys.argv[1])if len(sys.argv)>1 else Path('/tmp/ir-pure-cli-db-reproduction.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
