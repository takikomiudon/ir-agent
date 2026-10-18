"""Offline extraction only. --check compares deterministic outputs without rewriting."""
from pathlib import Path
import csv,hashlib,io,json,re,sys
P=Path(__file__).resolve().parent
raw=(P/'constituents-full.txt').read_bytes();text=raw.decode('utf-8');pages=text.split('\f');assert len(pages)==3 and not pages[-1].strip()
cap=json.loads((P/'capture.json').read_bytes());src=cap['GETs'][0]
pattern=re.compile(r'(?<!\S)([0-9A-Z]{4})\s+([PSG])\s+')
rows=[];page_start=0;page_counts=[]
def span(a,b):return {'unicode_start':a,'unicode_end':b,'utf8_start':len(text[:a].encode()),'utf8_end':len(text[:b].encode())}
for page_no,page in enumerate(pages[:-1],1):
 page_rows=[];line_offset=0;table_line=0
 for line in page.splitlines(keepends=True):
  matches=list(pattern.finditer(line))
  if matches:
   assert len(matches)==2,(page_no,repr(line));table_line+=1
   assert not line[:matches[0].start()].strip()
   for col,m in enumerate(matches,1):
    end=matches[col].start() if col<len(matches) else len(line.rstrip('\r\n'))
    a=m.end();b=end
    while a<b and line[a].isspace():a+=1
    while b>a and line[b-1].isspace():b-=1
    name=line[a:b];assert name and not pattern.search(name)
    base=page_start+line_offset
    record={'physical_page':page_no,'table_column':col,'table_row':table_line,'code':m.group(1),'market_code':m.group(2),'name':name,'source_spans':{'code':span(base+m.start(1),base+m.end(1)),'market_code':span(base+m.start(2),base+m.end(2)),'name':span(base+a,base+b)}}
    page_rows.append(record)
  line_offset+=len(line)
 # Preserve PDF presentation order: page1left thenright, page2left thenright.
 page_rows.sort(key=lambda x:(x['table_column'],x['table_row']));page_counts.append(len(page_rows));rows.extend(page_rows);page_start+=len(page)+1
assert page_counts==[140,60],page_counts
assert len(rows)==200 and len({r['code'] for r in rows})==200
assert rows[-1]['code']=='166A' and rows[-1]['name']=='タスキホールディングス'
for i,r in enumerate(rows,1):
 r['display_ordinal']=i
 for key,s in r['source_spans'].items():
  assert s['unicode_end']>s['unicode_start'] and text[s['unicode_start']:s['unicode_end']]==r[key]
  assert raw[s['utf8_start']:s['utf8_end']].decode()==r[key]
out={'source_url':src['url'],'raw_entity_sha256':src['raw_sha256'],'text_file':'constituents-full.txt','text_sha256':hashlib.sha256(raw).hexdigest(),'printed_publication_date':'2026-08-07','printed_application_date':'2026-08-31','application_status_in_document':'scheduled','actual_application_verified':False,'membership_as_of_retrieval_verified':False,'retrieved_at':src['http_get_completed_at'],'published_at_exact_time':None,'actual_database_first_save':None,'published_member_count':200,'extracted_member_count':len(rows),'unique_code_count':len({r['code'] for r in rows}),'page_row_counts':page_counts,'code_type':'string; four ASCII alphanumeric characters; no integer conversion','name_normalization':'No Unicode normalization, width conversion, corporate-name correction or internal whitespace changes; only surrounding table-layout whitespace removed.','order':'PDF page then left/right column then vertical row; author list ends in166A; not investment rank','offset_semantics':'Zero-based half-open Unicode characters and UTF-8 bytes in complete pinned text, preserving form feeds.','rows':rows}
outputs={'constituents.json':(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode()}
s=io.StringIO(newline='');w=csv.writer(s,lineterminator='\n');w.writerow(['code','market_code','name','physical_page','table_column','table_row','display_ordinal'])
for r in rows:w.writerow([r[k] for k in ['code','market_code','name','physical_page','table_column','table_row','display_ordinal']])
outputs['constituents.csv']=s.getvalue().encode('utf-8')
check='--check' in sys.argv
for n,b in outputs.items():
 if check:assert (P/n).read_bytes()==b,n
 else:(P/n).write_bytes(b)
print(json.dumps({'mode':'check' if check else 'extract','rows':len(rows),'unique_codes':len({r['code'] for r in rows}),'page_rows':page_counts,'alphanumeric_codes':[r['code'] for r in rows if not r['code'].isdigit()],'market_code_counts':{v:sum(r['market_code']==v for r in rows) for v in ['P','S','G']},'outputs':{k:hashlib.sha256(v).hexdigest() for k,v in outputs.items()}},ensure_ascii=False))
