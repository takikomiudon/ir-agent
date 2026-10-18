"""One bounded explicit public URL; fixed UA, shared 0.5rps lock, no retry/redirect."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import fcntl
import json
import sys
import time
import requests

root=Path(__file__).resolve().parent
url=sys.argv[1]
assert url.startswith('https://')
manifest_path=root/'capture.json'
manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {
 'maximum_GETs':4,'GETs':[],'retries':0,'automatic_redirects':0,'JavaScript_execution':0,
 'global_rps_target':0.5,'shared_rate_lock':'/tmp/ir-public-get-global-rate.lock',
 'shared_rate_clock':'/tmp/ir-public-get-global-rate.last','user_agent':'Codex-IR-Research/0.1',
 'TLS_verification':True,'inherited_proxy_and_CA':True}
assert len(manifest['GETs'])<4 and url not in [r['url'] for r in manifest['GETs']]
row={'sequence':len(manifest['GETs'])+1,'method':'GET','url':url,'http_status':None,'error':None,'complete_body':False}
manifest['GETs'].append(row)
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
raw=bytearray()
with open('/tmp/ir-public-get-global-rate.lock','a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 rate=Path('/tmp/ir-public-get-global-rate.last')
 last=float(rate.read_text()) if rate.exists() else 0
 remaining=2.0-(time.time()-last)
 if remaining>0:time.sleep(remaining)
 rate.write_text(str(time.time()))
 row['http_get_started_at']=datetime.now(timezone.utc).isoformat()
 try:
  with requests.get(url,headers={'User-Agent':'Codex-IR-Research/0.1'},timeout=(10,25),allow_redirects=False,stream=True) as response:
   row['http_status']=response.status_code
   row['headers_received_at']=datetime.now(timezone.utc).isoformat()
   row['response_headers']={k:v for k,v in response.headers.items() if k.lower() in {'content-type','content-length','location','last-modified','content-encoding','date'}}
   for chunk in response.iter_content(65536):
    raw.extend(chunk)
    if len(raw)>16*1024*1024:raise ValueError('Response exceeds bounded 16MiB body limit')
   row['complete_body']=True
 except (requests.RequestException,ValueError) as error:
  row['error']=type(error).__name__+': '+str(error)
 row['http_get_completed_at']=datetime.now(timezone.utc).isoformat()
 fcntl.flock(lock,fcntl.LOCK_UN)
digest=sha256(raw).hexdigest();(root/'raw'/digest).write_bytes(raw)
row.update(raw_file='raw/'+digest,raw_sha256=digest,byte_count=len(raw),
 body_byte_semantics='Saved response entity bytes; requests may decode HTTP content encoding; not wire capture')
(root/f'{row["sequence"]:02d}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(row,ensure_ascii=False))
