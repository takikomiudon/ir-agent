"""Finite official-public GET capture: <=5 URLs, one attempt each, no redirects/retry/form entry."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,urldefrag
from urllib.robotparser import RobotFileParser
import hashlib,json,subprocess,sys,time,re
from urllib.parse import urljoin
import requests
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scripts'))
import research_ir_universe as research
B=Path(__file__).parent
BASE='https://vrain.co.jp/'
manifest_file=B/'manifest.json'
manifest=json.loads(manifest_file.read_text()) if manifest_file.exists() else []
for url in sys.argv[1:]:
 url=urldefrag(url)[0]
 if len(manifest)>=5:raise SystemExit('5-URL limit')
 if any(r['requested_url']==url for r in manifest):raise SystemExit('No repeat GET')
 if urlsplit(url).scheme!='https' or urlsplit(url).netloc!='vrain.co.jp':raise SystemExit('Outside exact official host')
 if manifest and any(r.get('http_status') in (401,403,429) or (r.get('http_status') or 0)>=500 or r.get('error') for r in manifest):raise SystemExit('Prior access/transport failure: stop, no expansion')
 if url not in (BASE,BASE+'robots.txt'):
  known={link['url'] for row in manifest for link in json.loads((B/row['snapshot']).read_text()).get('links',[])}
  for row in manifest:
   old=json.loads((B/row['snapshot']).read_text())
   if old.get('raw_file') and 'html' in old.get('content_type',''):
    html=(B/old['raw_file']).read_text(errors='replace')
    known.update(urljoin(old['url'],match) for match in re.findall(r'<script[^>]+src=[\"\']([^\"\']+)',html,re.I))
  if url not in known:raise SystemExit('URL not linked in captured official page')
 if url!=BASE+'robots.txt':
  rr=next((r for r in manifest if r['requested_url']==BASE+'robots.txt'),None)
  if rr is None:raise SystemExit('robots must be first')
  robots=json.loads((B/rr['snapshot']).read_text())
  if robots.get('http_status')==200:
   parser=RobotFileParser();parser.parse(robots.get('text','').splitlines())
   if not research.robots_can_fetch(parser,research.USER_AGENT,url):raise SystemExit('robots disallowed; no GET')
   delay=parser.crawl_delay(research.USER_AGENT)
   if delay and delay>60:raise SystemExit('robots crawl-delay beyond finite task')
   time.sleep(max(0,float(delay or 0.5)))
  elif rr.get('http_status') not in (404,410):raise SystemExit('robots unresolved; no GET')
 r={'source_id':f'vrain135a-{len(manifest)+1:02d}','requested_url':url,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'published_at':None,'http_status':None,'error':None,'http_get_attempted':True,'submitted':False,'redirects_followed':0,'complete_body':False,'max_bytes':8*1024*1024,'extraction_method':None}
 raw=b''
 try:
  with requests.get(url,stream=True,allow_redirects=False,timeout=(8,18),headers={'User-Agent':research.USER_AGENT}) as response:
   r.update(http_status=response.status_code,content_type=response.headers.get('Content-Type',''),response_headers={k.lower():v for k,v in response.headers.items() if k.lower() in ('content-type','content-length','date','last-modified','location','retry-after')})
   if response.headers.get('Content-Length','').isdigit() and int(response.headers['Content-Length'])>r['max_bytes']:raise ValueError('declared_body_exceeds_8MiB')
   chunks=[];size=0
   for chunk in response.iter_content(65536):
    size+=len(chunk)
    if size>r['max_bytes']:raise ValueError('stream_body_exceeds_8MiB')
    chunks.append(chunk)
   raw=b''.join(chunks);r['complete_body']=True
   if 'application/pdf' in r['content_type']:
    r['extraction_method']='pdftotext -layout; form-feed separates one-based PDF pages'
   else:
    encoding=response.encoding if response.encoding and response.encoding.lower()!='iso-8859-1' else 'utf-8'
    decoded=raw.decode(encoding,errors='replace')
    if 'html' in r['content_type']:
     parser=research.Page();parser.feed(decoded);r.update(parser.extract(url));r['extraction_method']='existing research_ir_universe.Page visible HTML text/links, no scripts or submission'
    else:r.update(text=decoded,links=[],title='',extraction_method='decoded plain-text response')
 except (requests.RequestException,ValueError) as exc:r['error']=type(exc).__name__+': '+str(exc)[:150]
 if raw:
  sha=hashlib.sha256(raw).hexdigest();(B/'raw').mkdir(exist_ok=True);(B/'raw'/sha).write_bytes(raw);r.update(raw_file='raw/'+sha,sha256=sha,byte_count=len(raw))
  if r['complete_body'] and r['http_status']==200 and 'application/pdf' in r.get('content_type',''):
   txt=f'{len(manifest)+1:02d}.txt';subprocess.run(['pdftotext','-layout',str(B/r['raw_file']),str(B/txt)],check=True);r.update(text_file=txt,text=(B/txt).read_text(),title=urlsplit(url).path.rsplit('/',1)[-1],links=[])
 snapshot=f'{len(manifest)+1:02d}.json';(B/snapshot).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 row={k:r.get(k) for k in ('source_id','requested_url','url','retrieved_at','http_status','error','title','content_type','raw_file','sha256','byte_count','text_file','complete_body')};row['snapshot']=snapshot;manifest.append(row);manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({**row,'text_preview':r.get('text','')[:500],'links':[x for x in r.get('links',[]) if x['url'].lower().endswith('.pdf') or '/investors/' in x['url']][:60]},ensure_ascii=False),flush=True)
