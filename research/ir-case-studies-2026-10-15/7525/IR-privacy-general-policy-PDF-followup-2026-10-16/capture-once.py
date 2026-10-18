"""One budgeted GET preserving encoded response entity; no retries or automatic redirects."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import hashlib,json,sys,time,fcntl,signal,gzip,zlib
import requests
ROOT=Path('/workspace/ir-agent');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'));import research_ir_universe as repo
now=lambda:datetime.now(timezone.utc).isoformat();H=lambda b:hashlib.sha256(b).hexdigest();load=lambda p:json.loads(p.read_bytes())
def save(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
g=load(OUT/'guard.json');role=sys.argv[1];opts=[x for x in g['allowed_requests'] if x['role']==role];assert len(opts)==1;url=opts[0]['url'];UA=g['fixed_UA'];assert urlsplit(url).hostname not in g['held_exact_hosts']
cap=load(OUT/'capture.json') if (OUT/'capture.json').exists() else {'company_id':'jp:7525','maximum_GETs':1,'GETs':[],'new_GETs':0,'retries':0,'automatic_redirects':0}
assert len(cap['GETs'])<1 and url not in [x['url'] for x in cap['GETs']]
if role!='issuer_robots':
 decision=g['robots_reviews']['www.rix.co.jp'];assert decision['proceed'];raw=ROOT/decision['raw_file'];assert H(raw.read_bytes())==decision['raw_SHA256'];rp=RobotFileParser();rp.parse(raw.read_bytes().decode('utf-8').splitlines()) if decision['branch']=='complete_robots200' else setattr(rp,'allow_all',True);assert repo.robots_can_fetch(rp,UA,url)
with open('/tmp/ir-public-get-global-rate.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);clock=Path('/tmp/ir-public-get-global-rate.last');delay=max(0,2-(time.time()-float(clock.read_text()))) if clock.exists() else 0
 if delay:time.sleep(delay)
 clock.write_text(str(time.time()));fcntl.flock(lock,fcntl.LOCK_UN)
r={'sequence':len(cap['GETs'])+1,'role':role,'url':url,'method':'GET','HTTP_status':None,'HTTP_started_at':now(),'headers_received_at':None,'HTTP_completed_at':None,'raw_saved_at':None,'complete_body':False,'error':None,'prepared_UA':None,'configured_UA':UA,'TLS_verify':True,'proxy_CA_inherited':True,'automatic_redirects':False,'retries':0,'timeout_seconds':40,'max_entity_bytes':4194304,'response_headers':{},'shared_wait_seconds':delay};cap['GETs'].append(r);save('capture.json',cap);buf=bytearray()
def alarm(s,f):raise TimeoutError('bounded_40_second_deadline')
prev=signal.signal(signal.SIGALRM,alarm);signal.alarm(40)
try:
 with requests.get(url,headers={'User-Agent':UA},timeout=(10,40),stream=True,allow_redirects=False) as resp:
  r.update(HTTP_status=resp.status_code,response_url=resp.url,headers_received_at=now(),prepared_UA=resp.request.headers.get('User-Agent'),response_headers={k.lower():v for k,v in resp.headers.items() if k.lower() in ['content-type','content-encoding','content-length','date','last-modified','etag','location']})
  ln=resp.headers.get('Content-Length');assert ln is None or int(ln)<=4194304
  while True:
   chunk=resp.raw.read(65536,decode_content=False)
   if not chunk:break
   if len(buf)+len(chunk)>4194304:raise ValueError('over_4MiB_entity')
   buf.extend(chunk)
  r['complete_body']=True
except (requests.RequestException,ValueError,TimeoutError,AssertionError,OSError) as exc:r['error']=type(exc).__name__+': '+str(exc)
finally:signal.alarm(0);signal.signal(signal.SIGALRM,prev)
r['HTTP_completed_at']=now();encoded=bytes(buf);r.update(raw_SHA256=H(encoded),raw_file='raw/'+H(encoded),raw_byte_count=len(encoded),raw_semantics='HTTP response entity bytes before Content-Encoding decoding; transfer framing/TLS/wire not captured.');(OUT/r['raw_file']).write_bytes(encoded);r['raw_saved_at']=now()
if r['complete_body'] and not r['error']:
 try:
  ce=r['response_headers'].get('content-encoding','').lower().strip();decoded=encoded
  if ce=='br':
   import brotli
   decoded=brotli.decompress(encoded)
  elif ce=='gzip':decoded=gzip.decompress(encoded)
  elif ce=='deflate':decoded=zlib.decompress(encoded)
  elif ce not in ['', 'identity']:raise ValueError('unsupported_content_encoding')
  if len(decoded)>4194304:raise ValueError('over_4MiB_decoded_entity')
  r.update(decoded_SHA256=H(decoded),decoded_byte_count=len(decoded),decoded_file='decoded/'+H(decoded),local_content_decoding=ce or 'identity');(OUT/r['decoded_file']).write_bytes(decoded)
  if role=='issuer_robots':txt=decoded.decode('utf-8');r['text_kind']='robots_response_not_automatically_rules'
  elif r['HTTP_status']==200 and 'html' in r['response_headers'].get('content-type','').lower():
   html=decoded.decode('utf-8');p=repo.Page();p.feed(html);r['html_visible_text']=p.extract(url);txt=r['html_visible_text']['text'];r['text_kind']='html_visible_text'
  else:txt=None
  if txt is not None:r.update(text_file=f'text/{r["sequence"]:02}.txt',text_SHA256=H(txt.encode()));(OUT/r['text_file']).write_bytes(txt.encode())
 except Exception as exc:r['local_decode_or_parse_error']=type(exc).__name__+': '+str(exc)
cap['new_GETs']=len(cap['GETs']);save('capture.json',cap);print(json.dumps({k:r.get(k) for k in ['sequence','role','HTTP_status','complete_body','error','local_decode_or_parse_error','raw_byte_count','raw_SHA256','decoded_byte_count','decoded_SHA256','HTTP_completed_at']},ensure_ascii=False))
