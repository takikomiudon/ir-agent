"""Finite public primary-document capture; 4 total distinct URLs, no retry."""
import hashlib,json,sys,subprocess
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import research_ir_universe as r
B=Path(__file__).parent
p=B/'retrievals.json'
records=json.loads(p.read_text()) if p.exists() else []
for url in sys.argv[1:]:
 if len(records)>=4 or any(x['url']==url for x in records):raise SystemExit('Finite GET/unique URL limit reached')
 record={'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'method':'GET','attempt':1,'redirects_followed':False,'published_at':None,'submitted':False}
 try:
  response=requests.get(url,timeout=(8,20),allow_redirects=False)
  record.update(http_status=response.status_code,response_received_at=datetime.now(timezone.utc).isoformat(),content_type=response.headers.get('Content-Type'),location=response.headers.get('Location'))
  raw=response.content
  sha=hashlib.sha256(raw).hexdigest();record.update(sha256=sha,byte_count=len(raw),raw_file=f'raw/{sha}')
  (B/'raw').mkdir(exist_ok=True);(B/record['raw_file']).write_bytes(raw)
  if response.status_code==200:
   if raw.startswith(b'%PDF-'):
    outfile=f'{len(records)+1:02}.txt';subprocess.run(['pdftotext','-layout',str(B/record['raw_file']),str(B/outfile)],check=True)
    record.update(text_file=outfile,extraction_method='pdftotext -layout; PDF pages split by form-feed')
   elif 'html' in response.headers.get('Content-Type',''):
    parser=r.Page();parser.feed(raw.decode(response.encoding or 'utf-8',errors='replace'));page=parser.extract(url)
    outfile=f'{len(records)+1:02}.txt';(B/outfile).write_text(page['text']);record.update(text_file=outfile,extraction_method='Saved visible HTML text; existing research.Page parser',title=page.get('title'))
    (B/f'{len(records)+1:02}-page.json').write_text(json.dumps(page,ensure_ascii=False,indent=2))
 except (requests.RequestException,ValueError,subprocess.CalledProcessError) as e:record.update(error=type(e).__name__)
 records.append(record);p.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record,ensure_ascii=False),flush=True)
