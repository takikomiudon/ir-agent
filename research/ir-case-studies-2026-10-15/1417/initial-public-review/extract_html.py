"""Offline HTML text/href extraction; script/style bodies skipped, no JS execution."""
import json,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.hidden=0;self.parts=[];self.links=[];self.anchor=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag in ['script','style']:self.hidden+=1
  if tag=='a' and 'href' in attrs:self.anchor={'href':attrs['href'],'label_parts':[]}
  if tag=='img' and self.anchor is not None and attrs.get('alt'):self.anchor['label_parts'].append(attrs['alt'])
 def handle_endtag(self,tag):
  if tag=='a' and self.anchor is not None:
   a=self.anchor;self.links.append({'href':a['href'],'label':' '.join(a['label_parts'])});self.anchor=None
  if tag in ['script','style']:self.hidden=max(0,self.hidden-1)
 def handle_data(self,data):
  if not self.hidden and data.strip():
   text=' '.join(data.split());self.parts.append(text)
   if self.anchor is not None:self.anchor['label_parts'].append(text)
def main():
 b=Path(__file__).resolve().parent;seq=sys.argv[1];c=json.loads((b/f'{seq}.json').read_text());raw=(b/c['raw_file']).read_bytes();match=re.search(rb'charset=["\s]*([\w-]+)',raw[:4096],re.I);encoding=match.group(1).decode() if match else 'utf-8';parser=Parser();parser.feed(raw.decode(encoding));text='\n'.join(parser.parts)+'\n';(b/f'{seq}.html.txt').write_text(text)
 for link in parser.links:link['resolved_url']=urljoin(c['url'],link['href'])
 (b/f'{seq}.links.json').write_text(json.dumps({'source_url':c['url'],'source_capture':f'{seq}.json','decode_encoding':encoding,'extraction':'Python HTMLParser; entity decode; whitespace within text nodes collapsed; nodes newline-separated; script/style omitted; anchor labels include image alt','links':parser.links},ensure_ascii=False,indent=2)+'\n')
 for i,l in enumerate(parser.links):
  if any(w in l['label']+' '+l['href'] for w in ['決算','短信','library','result','.pdf','事業']):print(json.dumps({'index':i,**l},ensure_ascii=False))
 print('TEXT',text[:8000])
if __name__=='__main__':main()
