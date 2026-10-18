from pathlib import Path
from datetime import datetime,timezone
import ctypes,ctypes.util,json,hashlib,sys
R=Path('/workspace/ir-agent');O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'));import research_ir_universe as repo
c=json.loads((O/'capture.json').read_bytes())['GETs'][1];raw=(O/c['raw_file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==c['raw_sha256'];assert c['response_headers']['content-encoding']=='br'
libname=ctypes.util.find_library('brotlidec');assert libname
lib=ctypes.CDLL(libname);decode=lib.BrotliDecoderDecompress;decode.argtypes=[ctypes.c_size_t,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p];decode.restype=ctypes.c_int
buf=ctypes.create_string_buffer(10485760);size=ctypes.c_size_t(len(buf));src=ctypes.create_string_buffer(raw)
assert decode(len(raw),src,ctypes.byref(size),buf)==1
body=buf.raw[:size.value];text=body.decode('utf-8');assert '<html' in text.lower();p=repo.Page();p.feed(text);ex=p.extract(c['url'])
(O/'decoded').mkdir(exist_ok=True);(O/'decoded/02.html').write_bytes(body);(O/'text/02-decoded.txt').write_bytes(ex['text'].encode())
a={'decoded_at':datetime.now(timezone.utc).isoformat(),'method':'Existing system libbrotlidec BrotliDecoderDecompress of saved HTTP Content-Encoding br bytes; no request/retry/config/dependency changes.','system_library':libname,'original_GET_pointer':'capture.json $.GETs[1]','original_raw_SHA256':c['raw_sha256'],'original_raw_bytes':len(raw),'body_completed_at':c['http_get_completed_at'],'decoded_file':'decoded/02.html','decoded_SHA256':hashlib.sha256(body).hexdigest(),'decoded_bytes':len(body),'decoding_complete':True,'UTF8_strict':True,'initial_capture_visible_text':'Invalid because br bytes were initially decoded as UTF8; kept unmodified as extraction history, not usable literal source.','html_visible_text':ex}
(O/'decoded-root.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'decoded_bytes':len(body),'links':ex['links']},ensure_ascii=False))
