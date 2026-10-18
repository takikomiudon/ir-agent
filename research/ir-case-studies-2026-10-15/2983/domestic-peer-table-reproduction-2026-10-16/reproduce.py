"""One saved page: literal domestic-peer PER extraction and display arithmetic.
No network, database, normalization, EPS multiplication, or investment rule.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
BASE=Path('research/ir-case-studies-2026-10-15/2983/first-author-report')
IMPORTED=Path('research/ir-case-studies-2026-10-15/2983/actual-author-import')
sha=lambda p:sha256(p.read_bytes()).hexdigest()
source=json.loads((ROOT/BASE/'source-bundle.json').read_bytes())['sources'][0]
SID='case-public:cc1056ccbd3204206ab15aceab33c1b05c85f4dace3f235e12f454bd7169b328'
assert source['id']==SID
text=(ROOT/BASE/'text/02.txt').read_text();assert text==source['content']
assert sha(ROOT/BASE/'text/02.txt')=='861065412a3063fb067f361a4d7ab25f574cdd58cd236c9c0c0f48f11168000a'
assert sha(ROOT/BASE/'images/page-7.png')=='94f59cf9bf080d0daca9135584bb290a728fd19f2dc394ac15d1b67d6a67f01b'
imported=json.loads((ROOT/IMPORTED/'source-only-bundle.json').read_bytes())['sources']
assert next(s for s in imported if s['id']==SID)==source
receipt=json.loads((ROOT/IMPORTED/'actual-import.json').read_bytes())
av=next(r for r in receipt['new_source_first_save_receipts'] if r['entity_id']==SID)
canonical=json.dumps(source,ensure_ascii=False,sort_keys=True,allow_nan=False)
source_sha=sha256(canonical.encode()).hexdigest();assert source_sha==av['snapshot_sha256']
pages=text.split('\f');page=pages[6];start=sum(len(p)+1 for p in pages[:6]);assert text[start:start+len(page)]==page

def quote(sub):
 a=page.index(sub)+start;b=a+len(sub)
 return {'basis_quote':sub,'source_id':SID,'source_snapshot_sha256':source_sha,
   'character_start':a,'character_end_exclusive':b,'UTF8_start':len(text[:a].encode()),
   'UTF8_end_exclusive':len(text[:b].encode()),'physical_page':7,'printed_page':7}
lines=page.splitlines();header=page[page.index('ティッカー'):page.index('2983 JP')].rstrip()
rows=[]
codes=['1431','3465','8904','8917','2981','8860','1419','3291','3288','1911']
expected=['144.2','4.7','18.8','10.8','6.6','6.1','21.0','8.2','6.5','8.2']
for code,token in zip(codes+['2983'],expected+['6.1']):
 line=next(l for l in lines if l.startswith(code+' JP'))
 match=list(re.finditer(r'(?<!\S)\d+(?:,\d{3})*(?:\.\d+)?(?!\S)',line))[-2]
 assert match.group()==token
 q=quote(line);a=q['character_start']+match.start();b=a+len(token)
 rows.append({'code':code,'market_suffix_as_printed':'JP','PER_12month_forward_display_token':token,
  'PER_unit':'multiple','row_reference':q,'PER_value_location':{'character_start':a,'character_end_exclusive':b,
  'UTF8_start':len(text[:a].encode()),'UTF8_end_exclusive':len(text[:b].encode())}})
average_line=next(l for l in lines if l.startswith('平均'))
assert average_line.split()[-2]=='23.5'
with localcontext() as c:
 c.prec=40
 values=[Decimal(r['PER_12month_forward_display_token']) for r in rows[:10]]
 total=sum(values,Decimal(0));mean=total/Decimal(len(values));display=mean.quantize(Decimal('.1'),rounding=ROUND_HALF_UP)
 ordered=sorted(values);median=(ordered[4]+ordered[5])/Decimal(2)
 assert total==Decimal('235.1') and mean==Decimal('23.51') and display==Decimal('23.5') and median==Decimal('8.2')
result={'purpose':'Reproduce the author-selected domestic peer table and displayed average, not choose fair PE',
 'source':{'id':SID,'source_snapshot_sha256':source_sha,'bundle_file':str(BASE/'source-bundle.json'),
  'bundle_sha256':sha(ROOT/BASE/'source-bundle.json'),'text_file':str(BASE/'text/02.txt'),'text_sha256':sha(ROOT/BASE/'text/02.txt'),
  'raw_file':str(BASE/source['metadata']['original_raw_file']),'raw_sha256':source['metadata']['original_raw_sha256'],
  'image_file':str(BASE/'images/page-7.png'),'image_sha256':sha(ROOT/BASE/'images/page-7.png'),'image_visually_reviewed_this_task':True,
  'report_publication_date_as_saved':source['metadata']['publication_date'],'published_at':source['published_at'],
  'HTTP_completed_retrieved_at':source['retrieved_at'],'historical_firstsave_receipt':av,
  'saved_actual_import_bundle_source_whole_equal':True,'actual_import_receipt_file':str(IMPORTED/'actual-import.json'),
  'actual_import_receipt_sha256':sha(ROOT/IMPORTED/'actual-import.json'),'new_DB_connection':False},
 'column':{'label_read_from_image':'PER12か月フォワード(倍)','header_quote':quote(header),
  'data_provider_footer':quote('出所：ファクトセット、ブルームバーグ、アストリス・アドバイザリー'),
  'individual_observation_time':None,'forward_EPS_provider_vintage_or_roll_method':None},
 'domestic_peers':rows[:10],'subject_company_separate_not_in_peer_mean':rows[10],
 'displayed_domestic_average':{'PER_token':'23.5','row_quote':quote(average_line)},
 'Decimal_reproduction':{'n':10,'sum_of_displayed_peer_tokens':str(total),'unrounded_arithmetic_mean_of_displayed_tokens':str(mean),
  'local_display_rounding':'quantize .1 ROUND_HALF_UP; author rounding algorithm not asserted','local_rounded_mean':str(display),
  'matches_displayed_author_average':True,'author_underlying_full_precision_or_weighting_method_verified':False,
  'median_of_displayed_tokens_descriptive_only':str(median),'excluded_or_trimmed_peer_count':0,
  '144_2_retained_without_capping':True,'subject_2983_not_added_to_peer_cohort':True},
 'scope':{'one_page_only':7,'overseas_rows_analyzed':False,'old_EPS_identification_or_cancellation_ticket_reopened':False,
  'cohort_is_author_selected_not_new_project_selection':True,'fair_PE_or_current_October_price_or_target_or_probability':False,
  'multiplied_by_company_EPS':False,'normalizer_new_numeric_fact_or_index_registration':False,'financial_inputs_adopted':False,
  'author_relative_discount_claim_independently_valued':False,'GET_DB_Store_external_IR':0}}
print(json.dumps(result,ensure_ascii=False,indent=2))
