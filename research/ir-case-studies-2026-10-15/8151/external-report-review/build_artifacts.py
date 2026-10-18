"""Offline extraction/reproduction of the four saved public responses; no GET/DB."""
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
from urllib.robotparser import RobotFileParser

REPO=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(REPO/'src'))
from ir_agent.adapters.common import canonical_json, stable_source_id
from ir_agent.models import parse_json, json_text, validate_source

ROOT=Path(__file__).resolve().parent
CASE=ROOT.relative_to(REPO).as_posix()
def digest(raw):return sha256(raw).hexdigest()
def write(name,value):
 (ROOT/name).write_text(json_text(value)+'\n',encoding='utf-8')
def sha(path):return digest(path.read_bytes())
class Extract(HTMLParser):
 def __init__(self):super().__init__();self.text=[];self.skip=0;self.links=[];self.a=None;self.payloads=[];self.json_text=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag in ('script','style'):self.skip+=1
  if tag=='script' and attrs.get('type')=='application/json':self.json_text=''
  if tag=='a':self.a={'href':attrs.get('href'),'label':''}
  if tag in ('p','div','li','h1','h2','h3','br','tr'):self.text.append('\n')
 def handle_endtag(self,tag):
  if tag=='script' and self.json_text is not None:
   self.payloads.append(parse_json(self.json_text));self.json_text=None
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
  if tag=='a' and self.a is not None:self.links.append(self.a);self.a=None
  if tag in ('p','div','li','h1','h2','h3','tr'):self.text.append('\n')
 def handle_data(self,data):
  if self.json_text is not None:self.json_text+=data
  if not self.skip:
   self.text.append(data)
   if self.a is not None:self.a['label']+=data
 def visible(self):return '\n'.join(' '.join(s.split()) for s in ''.join(self.text).splitlines() if s.strip())+'\n'

def main():
 official_path=REPO/'research/ir-contacts-universe-2026-10-11/evidence/8151/20261011T235519303745Z/02.json'
 assert sha(official_path)=='359318f5e32c6446d876d259684c211f832c6e2d0980200907288f838d1e0009'
 official=parse_json(official_path.read_text());link=official['links'][67]
 page_url='https://corporateresearch.astrisadvisory.com/ja/toyo'
 assert link['href']==link['url']==page_url
 capture=parse_json((ROOT/'capture.json').read_text());rows=capture['GETs']
 assert len(rows)==4 and all(r['http_status']==200 and r['complete_body'] and r['error'] is None for r in rows)
 for row in rows:
  raw=(ROOT/row['raw_file']).read_bytes();assert digest(raw)==row['raw_sha256'] and len(raw)==row['byte_count']
 html=(ROOT/rows[1]['raw_file']).read_bytes().decode('utf-8')
 parser=Extract();parser.feed(html)
 text=parser.visible();assert text==(ROOT/'02.txt').read_bytes().decode('utf-8')
 write('02.links.json',parser.links)
 assert len(parser.payloads)==1
 data=parser.payloads[0];reports=data['hubdb_rows']
 assert len(reports)==5
 latest=max(reports,key=lambda r:r['date'])
 assert latest['date']=='2025.06.03' and latest['file_url']==rows[3]['url']
 write('02.embedded-reports.json',data)
 robots=[]
 for sequence,target in ((1,page_url),(3,rows[3]['url'])):
  row=rows[sequence-1];robot_text=(ROOT/row['raw_file']).read_text()
  rp=RobotFileParser();rp.parse(robot_text.splitlines())
  allowed=rp.can_fetch('Codex-IR-Research/0.1',target)
  assert allowed and 'gptbot' not in robot_text.lower() and 'chatgpt' not in robot_text.lower()
  robots.append({'capture_sequence':sequence,'target':target,'allowed_for_fixed_actual_UA':allowed,
                 'AI_specific_deny_groups_found':False,'raw_sha256':row['raw_sha256']})
 pdf=(ROOT/rows[3]['raw_file']).read_bytes()
 assert pdf.startswith(b'%PDF-') and len(pdf)==835303 and len(pdf)<16*1024*1024
 assert int(rows[3]['response_headers']['content-length'])==len(pdf)
 pdftext=subprocess.run(['pdftotext','-layout',str(ROOT/rows[3]['raw_file']),'-'],check=True,capture_output=True).stdout
 assert pdftext==(ROOT/'04.txt').read_bytes()
 pages=pdftext.decode('utf-8').split('\f');assert len(pages)==12 and not pages[-1].strip()
 sources=[]
 for row,textname,kind,doc_kind in ((rows[1],'02.txt','html_visible_text','external_research_report_index'),
                                   (rows[3],'04.txt','pdf_text','external_research_report')):
  content=(ROOT/textname).read_bytes().decode('utf-8')
  snapshot={**row,'text':content,'extraction_kind':kind}
  snapshot_name=f'{row["sequence"]:02d}.transport.json';write(snapshot_name,snapshot)
  metadata={'provider':'finite_issuer_statement_calendar_followup','saved_case_directory':CASE,
   'original_raw_file':row['raw_file'],'original_raw_sha256':row['raw_sha256'],'original_raw_byte_count':row['byte_count'],
   'original_transport_snapshot':snapshot_name,'original_transport_snapshot_sha256':sha(ROOT/snapshot_name),
   'extraction':{'kind':kind,'saved_file':textname,'sha256':sha(ROOT/textname)},
   'document_kind':doc_kind,'author_organization':'アストリス・アドバイザリー・ジャパン株式会社',
   'individual_author':None,'financial_inputs_verified':False,'meaning_review_required':True,'model_adopted':False,
   'publication_date_label':'2025 年 6 月 3 日' if kind=='pdf_text' else None,
   'publication_timestamp_unknown':True,'commissioned_and_paid_by_subject_company':True if kind=='pdf_text' else None,
   'provider_name_scope':'Metadata provider identifies the saved-byte contract, not issuer authorship or statement status.',
   'original_capture_file':'capture.json','original_capture_sha256':sha(ROOT/'capture.json'),
   'captured_retrieval_basis':'http_get_completed_at after full response body',
   'stale_vintage_not_current_forecast':True}
  if kind=='html_visible_text':
   metadata.update(embedded_report_list_file='02.embedded-reports.json',embedded_report_list_sha256=sha(ROOT/'02.embedded-reports.json'),
    static_json_extraction='HTML script[type=application/json] only; strict parse_json; no JavaScript execution')
  else:metadata['original_source_id']=sources[0]['id']
  identifier=stable_source_id('case-public',company_id='jp:8151',url=row['url'],content=content,metadata=metadata)
  source={'id':identifier,'company_id':'jp:8151','title':'東陽テクニカ(8151) — '+('Astris掲載レポート一覧' if kind=='html_visible_text' else 'Astris 2025年9月期2Q決算アップデート 2025-06-03'),
   'url':row['url'],'source_type':'public_disclosure','published_at':None,'retrieved_at':row['http_get_completed_at'],
   'requires_research':True,'content':content,'metadata':metadata}
  validate_source(source);sources.append(source)
 bundle={'schema_version':1,'companies':[],'sources':sources,'theses':[]}
 write('source-bundle.json',bundle)
 quotes=[]
 def quote(identifier,page,start,end=None):
  content=pages[page-1];begin=content.index(start);finish=content.index(end,begin)+len(end) if end else len(content)
  selected=content[begin:finish]
  offset=sum(len(p)+1 for p in pages[:page-1])+begin
  assert sources[1]['content'][offset:offset+len(selected)]==selected
  quotes.append({'id':identifier,'source_id':sources[1]['id'],'pdf_page':page,'printed_page':page,
   'source_character_start':offset,'source_character_end':offset+len(selected),'quote':selected,
   'offset_unit':'zero-based Unicode characters in saved source.content; end exclusive'})
 quote('report-date-and-identity',1,'東陽テクニカ(8151)','2025 年 9 月期 2Q 決算アップデート')
 quote('author-valuation-market-multiples',1,'• バリュエーション','ると当社ではみている。')
 quote('author-eps-dps-table',1,'年度末','出所：会社データに基づきアストリス・アドバイザリーが作成')
 quote('author-vs-company-plan-and-assumptions',5,'当社の業績予想と主な前提条件')
 quote('delivery-delay-risk-and-order-lead-time',4,'同社は、2025 年 9 月期下期に AD／ADAS','案件は、2026 年 9 月期以降の業績に大きく貢献する見通しである。')
 quote('profitability-investment-and-fcf-premises',6,'•   収益性','はプラスのフリーキャッシュフローを維持できると予測する。')
 quote('commission-disclaimer-and-compensation',11,'免責事項','投資業\n                務を行っておらず、本レポート記載の金融証券は一切保有していません。')
 write('quotes.json',quotes)
 write('provenance.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'official_route':{
  'snapshot_path':official_path.relative_to(REPO).as_posix(),'snapshot_sha256':sha(official_path),'source_url':official['url'],
  'source_retrieved_at':official['retrieved_at'],'link_jsonpath':'$.links[67]','link':link},
  'static_report_list':{'raw_html_file':rows[1]['raw_file'],'raw_html_sha256':rows[1]['raw_sha256'],
   'selector':'script[type=application/json]','payload_count':1,'parsed_json_file':'02.embedded-reports.json',
   'parsed_json_sha256':sha(ROOT/'02.embedded-reports.json'),'latest_listing_jsonpath':'$.hubdb_rows[0]',
   'selected_report':latest,'selection':'maximum displayed date among only five static rows; no 2026 completeness claim',
   'PDF_URL_literal_present_in_received_HTML':latest['file_url'] in html,'JavaScript_executed':False,
   'download_link_not_followed':data['download_link']['href']},'robots':robots,
  'source_snapshots':[{'id':s['id'],'canonical_snapshot_sha256':digest(json_text(s).encode()),'content_sha256':digest(s['content'].encode()),'retrieved_at':s['retrieved_at']} for s in sources],
  'publication_time':'Date-only report label retained; published_at null; HTTP Last-Modified and PDF creation metadata not substituted.',
  'PDF_identity':{'magic_PDF':True,'declared_content_type':rows[3]['response_headers']['content-type'],
   'declared_content_length':rows[3]['response_headers']['content-length'],'actual_response_entity_bytes':len(pdf),
   'pdf_pages':11,'images_visually_reviewed':[{'page':i,'file':f'04-page-{i}.png','sha256':sha(ROOT/f'04-page-{i}.png')} for i in (1,5)],
   'individual_author':'Not identified in checked PDF text/visual front page. PDF Author metadata Tavkel is not accepted as report authorship.'},
  'retrieval_count':4,'external_sends':0,'database_accesses':0,'model_adoption':False})
 print(json_text({'source_ids':[s['id'] for s in sources],'quote_count':len(quotes),'pages':11,'network_calls':0}))

if __name__=='__main__':main()
