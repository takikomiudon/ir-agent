from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json, shutil, sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.models import json_text, validate_source
from ir_agent.store import Store
from ir_agent.harness import Harness
OUT=Path(__file__).resolve().parent
now=lambda:datetime.now(timezone.utc).isoformat()
digest=lambda p:sha256(p.read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as f:f.write(json_text(value)+'\n')
capture=json.loads((OUT/'capture.json').read_bytes());r=capture['GETs'][0]
assert capture['new_GETs']==1 and r['HTTP_status']==200 and r['complete_body'] and r['error'] is None
raw=OUT/r['raw_file'];text=OUT/r['text_file'];content=text.read_bytes().decode()
assert digest(raw)==r['raw_sha256'] and digest(text)==r['text_sha256']
pages=content.split('\f');assert len(pages)-1==29
source={'id':'case-public:'+r['raw_sha256'],'company_id':'jp:5831',
        'title':'2026年度 第1四半期決算の概要（公式説明資料）','url':r['url'],
        'source_type':'public_disclosure','document_kind':'issuer_financial_presentation',
        'published_at':None,'retrieved_at':r['http_get_completed_at'],
        'source_first_saved_at':None,'requires_research':True,'content':content,
        'metadata':{'raw_file':str(raw.relative_to(ROOT)),'raw_sha256':digest(raw),
                    'text_file':str(text.relative_to(ROOT)),'content_sha256':digest(text),
                    'current_raw_saved_at':r['raw_saved_at'],'historical_first_save_unknown':True,
                    'publication_precision':'exact original publication date/time not established in selected pages; Last-Modified is not publication',
                    'semantically_reviewed_pages':[18,19,20],'physical_page_count':29,
                    'other_pages_mechanical_only':True,
                    'source_id_is_local_capture_identifier_not_system_derivation':True}}
assert validate_source(source)==source
save('source-only-bundle.json',{'schema_version':1,'sources':[source]})
images=OUT/'images';images.mkdir(exist_ok=True);quotes=[]
for page,identity in [(18,'policy-equity-holdings-and-valuation-reserve'),(19,'dividends-buybacks-and-EPS-definitions'),(20,'forecast-CET1-and-fully-implemented-basis')]:
    image=images/f'page-{page}.png';shutil.copyfile(f'/tmp/shizuoka-policy-{page}.png',image)
    quote=pages[page-1];start=sum(len(p)+1 for p in pages[:page-1])
    assert content[start:start+len(quote)]==quote
    quotes.append({'id':identity,'source_id':source['id'],'quote':quote,'pdf_physical_page':page,
                   'source_character_start':start,'source_character_end_exclusive':start+len(quote),
                   'source_UTF8_byte_start':len(content[:start].encode()),
                   'source_UTF8_byte_end_exclusive':len(content[:start+len(quote)].encode()),
                   'image_path':str(image.relative_to(ROOT)),'image_sha256':digest(image)})
save('quotes.json',quotes)
review={'recorded_at':now(),'company_id':'jp:5831','source_id':source['id'],
        'semantic_pages_and_images':[18,19,20],'other26_pages':'mechanical extraction only',
        'selection_correction':'Original semantic-selection reason anticipated next-plan CET1 target; actual p20 is annual forecast. No next-plan target is established from these pages; original selection record retained.',
        'publicly_resolved':[
            'p18: valuation reserves are described as capital supporting stable management; their CET1 contribution is guided at about1.5–2%, aiming below2% during the second plan. This is not total CET1 target or a cash distribution.',
            'p19: company intends progressive payout ratio increase to at least50% by FY2027 and maintenance fromFY2028; this is company policy, not an investor return hurdle.',
            'p19: company announced buyback commencement inAugust2026 with ceilings30billionJPY/10million shares; ceilings are not proof of completed purchases.',
            'p19: FY2026 dividend108JPY forecast, payout49.6% and total return75.5% are company estimates with footnotes; not guaranteed future payout or FCFE.',
            'p20: holding-group forecast CET1 is14.29%, or13.56% under fully implemented BaselIII estimate; Q1 actual16.24%, or14.00% under that estimate. Different bases and dates remain separate.',
            'p20: annual parent-attributable NI1150億JPY matches prior statement115000millionJPY by explicit unit conversion; company guidance, not independent evidence or realized earnings.'],
        'unresolved':[
            'A complete same-period annual forward regulatory-capital reinvestment amount and its equity-holder scope.',
            'Chosen capital definition, target/buffers and forward RWA bridge. A ratio alone is not a monetary reinvestment amount.',
            'Whether/where public capital-policy reconciliation makes transitional versus fully implemented basis comparable across the annual endpoints.'],
        'IR_disposition':'Do not re-ask the published payout policy, buyback ceiling, disclosed CET1 ratios or annual NI. Only a definition/location clarification may remain after a finite public basis check; no forecast guarantee requested.',
        'author_principle':'Damodaran: FCFE = NetIncome - ReinvestmentInRegulatoryCapital; company policy does not replace the missing annual reinvestment input.',
        'financial_inputs_verified':False,'model_adopted':False,'FCFE_calculated':False,
        'buy_sell_target_exit_rule':'unset; no invented investor conditions',
        'independent_semantic_review_completed':False,'new_GETs':1,'retries_redirects_URL_guesses_external_sends_orders':0}
save('review.json',review)
memory=Store(':memory:')
result=Harness(memory).ingest({'schema_version':1,'companies':[{'id':'jp:5831','name':'Schema check only'}],'sources':[source]})
assert result['sources_added']==1 and memory.source(source['id'])==source
memory.close()
save('validation.json',{'recorded_at':now(),'source_schema_and_memory_ingest':result,'raw_text_SHA_match':True,
                        'quotes_match_saved_text':True,'images_inspected':[18,19,20],
                        'actual_DB_imported':False,'independent_semantic_review_completed':False})
print(json_text({'sources':1,'quotes':3,'actual_DB_imported':False}))
