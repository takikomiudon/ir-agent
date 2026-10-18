from pathlib import Path
from datetime import datetime, timezone
from urllib.robotparser import RobotFileParser
import json, hashlib, sys, time, fcntl, signal, requests, subprocess
ROOT=Path('/workspace/ir-agent');OUT=ROOT/'research/ir-case-studies-2026-10-15/5831/regulatory-capital-followup'
sys.path.insert(0,str(ROOT/'scripts'));import research_ir_universe as repo
UA='Codex-IR-Research/0.1';now=lambda:datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(n,j):(OUT/n).write_bytes((json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode())
g=load(OUT/'guard.json');role=sys.argv[1];matches=[r for r in g['allowed_requests'] if r['role']==role];assert len(matches)==1;url=matches[0]['url']
cp=OUT/'capture.json';cap=load(cp) if cp.exists() else {'company_id':'jp:5831','maximum_GETs':2,'GETs':[],'new_GETs':0,'retries':0,'automatic_redirects':0}
assert len(cap['GETs'])<g['maximum_GETs'] and url not in [r['url'] for r in cap['GETs']]
if not role.endswith('robots'):
 assert g['cached_robots_review']['same_session_fixed_UA_and_exact_host'] is True
 pin=g['cached_robots_review'];assert sha(ROOT/pin['capture_path'])==pin['capture_sha256']
 from urllib.parse import urlparse
 decision=g['robots_reviews'][urlparse(url).netloc];assert decision['proceed'] is True
 raw=ROOT/decision['raw_file'];assert sha(raw)==decision['raw_sha256'];rp=RobotFileParser()
 if decision['branch']=='fresh_robots200':rp.parse(raw.read_bytes().decode('utf-8').splitlines())
 else:assert decision['branch']=='complete404_missingrobots';rp.allow_all=True
 assert repo.robots_can_fetch(rp,UA,url)
with open('/tmp/ir-public-get-global-rate.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);clock=Path('/tmp/ir-public-get-global-rate.last');delay=max(0,2-(time.time()-float(clock.read_text()))) if clock.exists() else 0
 if delay:time.sleep(delay)
 clock.write_text(str(time.time()));fcntl.flock(lock,fcntl.LOCK_UN)
c={'sequence':len(cap['GETs'])+1,'role':role,'url':url,'method':'GET','http_get_started_at':now(),'headers_received_at':None,'http_get_completed_at':None,'raw_saved_at':None,'HTTP_status':None,'complete_body':False,'error':None,'configured_UA':UA,'prepared_request_UA':None,'proxy_CA_inherited':True,'TLSverify':True,'automatic_redirects':False,'retries':0,'timeout_seconds':40,'max_entity_bytes':10485760,'shared_wait_seconds':delay,'response_headers':{}};cap['GETs'].append(c);save('capture.json',cap);data=bytearray()
def alarm(sig,frame):raise TimeoutError('bounded_40_second_deadline')
previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(40)
try:
 with requests.get(url,headers={'User-Agent':UA},stream=True,timeout=(10,40),allow_redirects=False) as resp:
  c.update(HTTP_status=resp.status_code,response_url=resp.url,prepared_request_UA=resp.request.headers.get('User-Agent'),headers_received_at=now(),response_headers={k.lower():v for k,v in resp.headers.items() if k.lower() in ['content-type','content-length','content-encoding','date','last-modified','etag','location']})
  length=resp.headers.get('Content-Length')
  if length and int(length)>10485760:raise ValueError('Content-Length_over_10MiB')
  for chunk in resp.iter_content(65536):
   if len(data)+len(chunk)>10485760:raise ValueError('entity_stream_over_10MiB')
   data.extend(chunk)
  c['complete_body']=True
except (requests.RequestException,ValueError,TimeoutError) as e:c['error']=type(e).__name__+': '+str(e)
finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
c['http_get_completed_at']=now();h=hashlib.sha256(data).hexdigest();c.update(byte_count=len(data),raw_sha256=h,raw_file='raw/'+h);(OUT/c['raw_file']).write_bytes(data);c['raw_saved_at']=now();c['entity_byte_semantics']='Response entity bytes, possibly Content-Encoding decoded; not wire capture.'
if c['complete_body'] and not c['error']:
 text=None
 if role.endswith('robots'):text=bytes(data).decode('utf-8',errors='replace');c['text_kind']='robots_response_text_not_necessarily_rules'
 elif c['HTTP_status']==200:
  if bytes(data).startswith(b'%PDF-') and 'application/pdf' in c['response_headers'].get('content-type','').lower():text=subprocess.run(['pdftotext','-layout',str(OUT/c['raw_file']),'-'],capture_output=True,check=True).stdout.decode();c['text_kind']='pdf_text';c['PDF_magic']=True
  elif 'html' in c['response_headers'].get('content-type','').lower():p=repo.Page();p.feed(bytes(data).decode('utf-8',errors='replace'));c['html_visible_text']=p.extract(url);text=c['html_visible_text']['text'];c['text_kind']='html_visible_text'
 if text is not None:c['text_file']=f'text/{c["sequence"]:02}.txt';(OUT/c['text_file']).write_bytes(text.encode());c['text_sha256']=sha(OUT/c['text_file'])
cap['new_GETs']=len(cap['GETs']);save('capture.json',cap);print(json.dumps({k:c[k] for k in ['sequence','role','HTTP_status','complete_body','error','byte_count','raw_sha256','http_get_completed_at']},ensure_ascii=False))
