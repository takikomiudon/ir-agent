"""Finite public capture: no retries, auto redirects, JS, alternate routes or XJ requests."""
import hashlib,json,sys,time
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
 roboturl=f'{urlsplit(url).scheme}://{host}/robots.txt'
 robots_rows=[r for r in manifest['GETs'] if r['url']==roboturl]
 # One explicitly issued same-origin robots redirect may be followed as a separate counted GET.
 robots_redirect=bool(robots_rows and robots_rows[-1]['status'] in [301,302,303,307,308] and robots_rows[-1].get('headers',{}).get('location')==url and urlsplit(url).path.endswith('/robots.txt'))
 if url!=roboturl and not robots_redirect:
  if not robots_rows:raise ValueError('Robots must be checked first')
  row=robots_rows[-1]
  if row['status'] in [301,302,303,307,308]:
   explicit=[r for r in manifest['GETs'] if r['url']==row.get('headers',{}).get('location')]
   if not explicit:raise ValueError('Robots redirect has not been separately checked')
   row=explicit[-1]
  if row['status']==200:
   raw=(FOLDER/row['raw_file']).read_bytes();rp=RobotFileParser(row['url']);rp.parse(raw.decode('utf-8').splitlines())
   if not rp.can_fetch(UA,url):raise ValueError('Robots disallows requested URL')
  elif row['status'] not in [404,410]:raise ValueError('Robots not available with unambiguous absent status; stop')
 if manifest['GETs']:
  elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(manifest['GETs'][-1]['dispatched_at'])).total_seconds();time.sleep(max(0,2-elapsed))
 n=len(manifest['GETs'])+1;row={'sequence':n,'url':url,'dispatched_at':datetime.now(timezone.utc).isoformat(),'method':'GET','status':None,'error':None};manifest['GETs'].append(row)
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
