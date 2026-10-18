"""Finite public capture: no retries, auto redirects, JS, alternate routes or XJ requests."""
import hashlib,json,sys,time,fcntl
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import requests
FOLDER=Path(__file__).resolve().parent
UA='Codex-IR-Research/0.1'
def main():
 url=sys.argv[1];host=urlsplit(url).netloc
 if host=='contents.xj-storage.jp':raise ValueError('Existing same-day XJ robots denies all; no request permitted')
 manifest_path=FOLDER/'transport-manifest.json'
 manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'maximum_GETs':5,'GETs':[],'retries':0,'automatic_redirects':0,'JavaScript_execution':0,'global_rps':0.5,'proxy_retained':True,'TLS_verification':True,'user_agent':UA}
 if len(manifest['GETs'])>=5 or any(r['url']==url for r in manifest['GETs']):raise ValueError('GET budget exhausted or duplicate URL')
 if urlsplit(url).path!='/robots.txt':
  roboturl=f'{urlsplit(url).scheme}://{host}/robots.txt';rows=[r for r in manifest['GETs'] if r['url']==roboturl]
  if not rows:raise ValueError('Robots must be checked first')
  row=rows[-1]
  if row['status']==200:
   raw=(FOLDER/row['raw_file']).read_bytes();rp=RobotFileParser(roboturl);rp.parse(raw.decode('utf-8').splitlines())
   if not rp.can_fetch(UA,url):raise ValueError('Robots disallows requested URL')
  elif row['status'] not in [404,410]:raise ValueError('Robots not available with unambiguous absent status; stop')
 if manifest['GETs']:
  elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(manifest['GETs'][-1]['dispatched_at'])).total_seconds();time.sleep(max(0,2-elapsed))
 # Shared wallclock dispatch spacing for the parent-authorized concurrent research tasks.
 with open('/tmp/ir-public-get-global-rate.lock','a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  marker=Path('/tmp/ir-public-get-global-rate.last')
  if marker.exists():
   previous=float(marker.read_text());time.sleep(max(0,2-(time.time()-previous)))
  marker.write_text(str(time.time()))
  fcntl.flock(lock,fcntl.LOCK_UN)
 n=len(manifest['GETs'])+1;row={'sequence':n,'url':url,'dispatched_at':datetime.now(timezone.utc).isoformat(),'method':'GET','status':None,'error':None,'response_body_basis':'requests iter_content decoded HTTP content-encoding; saved entity bytes, not compressed wire bytes','shared_rate_lock':'/tmp/ir-public-get-global-rate.lock','shared_rate_marker':'/tmp/ir-public-get-global-rate.last'};manifest['GETs'].append(row)
 manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');raw=bytearray()
 try:
  with requests.get(url,headers={'User-Agent':UA},timeout=(10,25),allow_redirects=False,stream=True) as response:
   row['status']=response.status_code;row['headers']={k:v for k,v in response.headers.items() if k.lower() in {'content-type','content-length','location','last-modified','content-encoding'}}
   for chunk in response.iter_content(65536):
    raw.extend(chunk)
    if len(raw)>16*1024*1024:raise ValueError('Body exceeds16MiB cap')
 except (requests.RequestException,ValueError) as e:row['error']=f'{type(e).__name__}: {e}'
 digest=hashlib.sha256(raw).hexdigest();p=FOLDER/'raw'/digest;p.write_bytes(raw)
 row.update(sha256=digest,byte_count=len(raw),raw_file=str(p.relative_to(FOLDER)),retrieved_at=datetime.now(timezone.utc).isoformat())
 manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(FOLDER/f'{n:02d}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');print(json.dumps(row,ensure_ascii=False))
if __name__=='__main__':main()
