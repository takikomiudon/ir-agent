"""Task-local bounded single-GET capture. No retries or automatic redirects."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlsplit
import json
import sys
import requests

ROOT = Path(__file__).resolve().parent
UA = 'Codex-IR-Research/0.1'

def now():
    return datetime.now(timezone.utc).isoformat()

def capture(url):
    record_path = ROOT / 'capture.json'
    state = json.loads(record_path.read_text()) if record_path.exists() else {'maximum_GETs':4,'GETs':[]}
    if len(state['GETs']) >= 4:
        raise ValueError('Task GET budget exhausted')
    if urlsplit(url).hostname != 'www.tweedymanaged.com' or urlsplit(url).scheme != 'https':
        raise ValueError('Only the literal official managed-account host is in task scope')
    if any(e['requested_url'] == url for e in state['GETs']):
        raise ValueError('Retry is prohibited')
    item = {'sequence':len(state['GETs'])+1,'requested_url':url,'http_get_started_at':now(),
            'prepared_user_agent':UA,'wire_request_headers_independently_verified':False,
            'TLS_verification':True,'proxy_CA':'inherited','retry':False,'automatic_redirects':False,
            'http_status':None,'error':None,'complete_body':False,'published_at':None,
            'first_saved_at_known':False}
    state['GETs'].append(item)
    record_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    try:
        with requests.get(url,headers={'User-Agent':UA},allow_redirects=False,timeout=(10,30),stream=True) as response:
            item.update(http_status=response.status_code,http_response_received_at=now(),
                        response_headers={k:v for k,v in response.headers.items() if k.lower() in
                        ('date','content-type','content-length','content-encoding','location','last-modified')})
            parts=[]; size=0
            for block in response.iter_content(65536):
                size += len(block)
                if size > 16*1024*1024:
                    raise ValueError('Task body limit exceeded')
                parts.append(block)
            body=b''.join(parts)
            item.update(complete_body=True,http_get_completed_at=now(),byte_count=len(body),
                        body_byte_semantics='Saved decoded response entity bytes, not wire bytes')
            digest=sha256(body).hexdigest()
            (ROOT/'raw').mkdir(exist_ok=True)
            (ROOT/'raw'/digest).write_bytes(body)
            item.update(raw_file='raw/'+digest,raw_sha256=digest,retrieved_at=item['http_get_completed_at'])
    except Exception as error:
        item.update(error=type(error).__name__+': '+str(error),http_get_completed_at=now())
    record_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(item,ensure_ascii=False))

if __name__ == '__main__':
    capture(sys.argv[1])
