"""Finite public GET evidence capture; never enters or submits the IR form."""
import hashlib,json,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import collect_ir_followups as c
B=Path(__file__).parent
f=c.BoundedFetcher(20,0.5)
f.allowed_hosts.add('piolax.co.jp')
original=f._dispatch_get
allowed_pdfs={x['url'] for x in json.loads((B/'01.json').read_text()).get('links',[]) if x['url'].startswith('https://www.piolax.co.jp/') and x['url'].endswith('.pdf')} if (B/'01.json').exists() else set()
raws={}
def dispatch(url,origin,result):
 if url in allowed_pdfs:
  if f.http_get_attempt_count >= f.max_gets: raise ValueError('GET limit')
  response=c.research.Fetcher._dispatch_get(f,url,origin,result)
 else:
  response=original(url,origin,result)
 if response is not None:
  iterator=response.iter_content
  def chunks(*args,**kwargs):
   blocks=[]
   try:
    for block in iterator(*args,**kwargs):
     blocks.append(block)
     yield block
   finally:
    raw=b''.join(blocks)
    if raw:
     digest=hashlib.sha256(raw).hexdigest()
     (B/'raw').mkdir(exist_ok=True)
     (B/'raw'/digest).write_bytes(raw)
     raws[url]={'raw_file':'raw/'+digest,'sha256':digest,'byte_count':len(raw)}
  response.iter_content=chunks
 return response
f._dispatch_get=dispatch
manifest_path=B/'manifest.json'
manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
for url in sys.argv[1:]:
 if url not in {x['requested_url'] for x in manifest} and len({x['requested_url'] for x in manifest})>=8: raise SystemExit('8-document capture limit reached')
 for previous in manifest:
  if previous['requested_url']==url:
   old=json.loads((B/previous['snapshot']).read_text())
   if old.get('http_get_attempted') or old.get('error')!='unsafe_followup_url': raise SystemExit('Already attempted; no retry')
 page=f.capture(url)
 page['capture_files']=raws.copy()
 if 'application/pdf' in page.get('content_type','') and not page.get('error'):
  raw=raws[page.get('url',url)]['raw_file']
  textfile=f'{len(manifest)+1:02d}.txt'
  subprocess.run(['pdftotext','-layout',str(B/raw),str(B/textfile)],check=True)
  page['text_file']=textfile
  page['text']=(B/textfile).read_text()
  page['extraction_method']='pdftotext -layout; form-feed separates 1-based PDF pages'
 snapshot=f'{len(manifest)+1:02d}.json'
 (B/snapshot).write_text(json.dumps(page,ensure_ascii=False,indent=2))
 row={k:page.get(k) for k in ['requested_url','url','http_status','error','retrieved_at','content_type','title','text_file']}
 row['snapshot']=snapshot
 manifest.append(row)
 manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print(json.dumps({**row,'links':page.get('links',[])},ensure_ascii=False),flush=True)
