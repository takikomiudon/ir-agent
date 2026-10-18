"""One-time limited documentation integration from frozen before bytes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
files=['README.md','research/ir-case-studies-2026-10-15/README.md','docs/research-stage-monitoring.md']
for path in files:
 assert (ROOT/path).read_bytes()==(HERE/'before'/path).read_bytes(),path
p=ROOT/files[0]; text=p.read_text(); old=next(x for x in text.split('\n\n') if x.startswith('現在の実台帳は'))
new='現在の実台帳は窓口1,819社のうち公開資料あり36社・財務内容あり31社、210資料（公開209・市場1）・分類209。全117job完了（intake96・定性21）、attempt114/event228/request receipt114・pending/leased0、source来歴はlegacy28/trusted182。native監視は26case・48版・149既読、内部管理日はJan15が12case・Jan16が14case。[公表数値索引v37](research/ir-case-studies-2026-10-15/disclosed-fact-index-v37.json)は28社226項目・41親entry・43派生source・会社/原典34組で、実台帳には219項目を派生41件として保存した。対象外8331/9702の2派生7項目はfile-only。'
text=text.replace(old,new,1)
marker='2163の[公式スポンサーindex]'
addition='''[アルバイトタイムスの原短信と派生12値](research/ir-2341-disclosed-facts-intake-2026-10-16/parent-acceptance.json)を保存・分類し、[native v1・既読2](research/ir-case-studies-2026-10-15/2341/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。公開注記で商品認識売上/ARR、セグメント・全社費用/OP、特益/親会社利益予想、消却/自己株処分・cash・平均株数を分け、[公開既答と残余](research/ir-case-studies-2026-10-15/2341/question-residual-review-2026-10-16/parent-acceptance.json)へ整理した。正常利益や現在EPSは作らず、金融入力・質問は未採用。公開KPI入口の別補足はfile-only。

キャリアデザインセンターは原短信・10/1通知・10/15結果・公開QAと派生12値の5sourceを保存・分類し、[native v1・既読5](research/ir-case-studies-2026-10-15/2410/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。[会社公表のPrime継続結果](research/ir-2410-listing-result-intake-2026-10-16/parent-acceptance.json)と[QA/12値](research/ir-2410-facts-with-qa-intake-2026-10-16/parent-acceptance.json)は公開既答へ移したが、独立した取下完了・取引保証とは分ける。非連結Q3/終了年度向け7月会社予想、普通/特別配当、内定承諾と辞退取消の認識を区別し、会社3,000円目標を投資家の評価額にしない。[v37受入](research/ir-case-studies-2026-10-15/2410/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)の210資料・25case/47版/144既読は登録前の歴史snapshotで、現在の26caseと混同しない。具体的な著者予測・評価法/売買閾値は未採用、正式質問・送信は0。

'''
assert marker in text;text=text.replace(marker,addition+marker,1)
oldpara=next(x for x in text.split('\n\n') if x.startswith('2163の[公式スポンサーindex]'))
text=text.replace(oldpara,oldpara+' [同原本の追加2頁](research/ir-case-studies-2026-10-15/2163/actionlearning-authorship-saved-pages-2026-10-16/parent-acceptance.json)で著者の事実整理という目的と会社中計の転載帰属を確認した補足もfile-onlyで、外部独自予測や売買規則にはしない。',1)
marker='日揮HDの[概要p6/8追補]'
extra='[2327の静的入口](research/ir-case-studies-2026-10-15/2327/initial-public-review-2026-10-16/parent-acceptance.json)は本文未確認のfile-only、[2445の初回](research/ir-case-studies-2026-10-15/2445/initial-public-review-2026-10-16/parent-acceptance.json)はrobots HTTP302で規則未確認のため1GET停止・財務source0。資料不存在や投資除外を意味せず、実210資料へ加算していない。2459の新資料候補もfile-only・DB外で未算入。\n\n'
assert marker in text;text=text.replace(marker,extra+marker,1);p.write_text(text)
p=ROOT/files[1]; text=p.read_text(); old=next(x for x in text.split('\n\n') if x.startswith('現在は実DB'))
new='現在は実DB210資料（公開209・市場1）・公開資料あり36社・財務内容あり31社、分類209。全117job完了（intake96・定性21）、attempt114/event228/request receipt114、pending/leased0。source来歴はlegacy28/trusted182、native監視26case/48版/149既読、内部管理Jan15が12case・Jan16が14case。[構造化v37](disclosed-fact-index-v37.json)は28社226fact・41親entry・43派生source・会社/原典34組で、41source/219factを実台帳へ保存・分類した。[v37受入時の210資料・25case/47版/144既読](2410/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)は2410 native登録前の歴史snapshotで、現在の26caseと分ける。対象外8331/9702の2source/7factはfile-only。1950旧85fe…代替版も未投入。[歴史ROICの参考計算](../ir-historical-roic-role-reproduction-2026-10-16/README.md)は明示した研究mappingに限る。金融入力・実policy・正式IRは未採用。個社記録内の旧件数と未確認は各時点の履歴として保持する。'
text=text.replace(old,new,1)
oldpara=next(x for x in text.split('\n\n') if x.startswith('2163の[公式スポンサー一覧]'))
text=text.replace(oldpara,oldpara+' [追加p2/11](2163/actionlearning-authorship-saved-pages-2026-10-16/parent-acceptance.json)では事実整理という作者説明と会社中計の転載帰属を確認したが、全冊読了や外部独自予測の認定にはしていない。追加も同原本のfile-only補足である。',1)
text=text.replace('現在の203資料へ未算入。','現在の210資料へ未算入。[2445](2445/initial-public-review-2026-10-16/parent-acceptance.json)はrobots HTTP302で規則未確認となり1GET停止・財務source0。転送先や本文は取得せず、投資除外とはしない。2459の候補もfile-only・DB外で未算入。',1)
marker='|---|---|---|\n'
rows='''| [キャリアデザインセンター 2410](2410/question-residual-review-2026-10-16/parent-acceptance.json) | 非連結Q3/当時FY会社予想、事業別経常利益/全社OP、CF非作成、自己株処分を分離。10/15通知による会社公表のPrime継続結果とQAの普通配当方針・内定承諾/辞退取消認識は既答。会社3,000円目標は投資家評価額でない。 | 原4＋派生1source/12値を保存・分類。[native v1・3条件・既読5](2410/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)、初回queue0。終了年度向けJuly guideを現予想/実績へ移さず、160円の普通140＋特別20を恒久配当へしない。著者method/basis不足、金融未採用・IR価値未立証・正式質問0。 |
| [アルバイトタイムス 2341](2341/question-residual-review-2026-10-16/parent-acceptance.json) | 商品認識売上/ARR、セグメント全社費用/OP、特益/親会社利益予想、消却・cash・株数定義を公開で分離。中間実績/当時FY会社予想・千円/百万円、年間DPS合計列を保持。 | 原1＋派生1source/12値を保存・分類。[native v1・3条件・既読2](2341/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)、初回queue0。正常OP/CF・現在EPSを作らず、著者method/basis不足・金融未採用・IR価値未立証・質問0。別KPI入口補足はfile-only。 |
'''
assert text.count(marker)==1;text=text.replace(marker,marker+rows,1);p.write_text(text)
p=ROOT/files[2]; text=p.read_text(); text+='''
## 現在の登録済み監視（2026-10-16）

[現在値のRO点検](../research/ir-2410-native-current-state-integration-2026-10-16/readonly-verification.json)では210source（公開209・市場1）/209分類、公開資料36社・財務内容31社、全117job完了（intake96・定性21）、attempt114/event228/request receipt114・pending/leased0。来歴はlegacy28/trusted182、26case/48版/149既読である。管理日はJan15が12case・Jan16が14caseの内部研究日で、会社予定や売却期限ではない。

[2341のnative v1](../research/ir-case-studies-2026-10-15/2341/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)は原短信/派生12値の2既読、[2410のnative v1](../research/ir-case-studies-2026-10-15/2410/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)は原短信・10/1通知・10/15結果・公開QA・派生12値の5既読で、どちらも初回queue0。2341は商品売上/ARR・特益/利益予想・株数定義、2410は非連結Q3/終了年度向け7月予想・普通/特別配当・取消認識を分ける。2410の会社公表Prime継続結果を未確認へ戻さず、独立した取下完了や取引保証とも区別する。

[索引v37の受入](../research/ir-case-studies-2026-10-15/2410/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)は28社226fact（実41派生/219fact、対象外2派生/7factはfile-only）。その210source・25case/47版/144既読は2410登録前の歴史snapshotで、現在値へ書き換えない。同原本の追加読解や[2163の帰属確認](../research/ir-case-studies-2026-10-15/2163/actionlearning-authorship-saved-pages-2026-10-16/parent-acceptance.json)、[2327の静的入口](../research/ir-case-studies-2026-10-15/2327/initial-public-review-2026-10-16/parent-acceptance.json)はfile-only補足。[2445](../research/ir-case-studies-2026-10-15/2445/initial-public-review-2026-10-16/parent-acceptance.json)はrobots302で規則未確認・1GET停止/source0であり資料不存在や投資除外ではない。2459候補もfile-only・DB外で実台帳へ加算しない。

具体的な著者予測・評価法/売買閾値は未採用で、金融thesis・policy・position・正式質問・返信・送信・注文は0。外部schedulerは未設置。[最新1,558テストの受入](../research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json)と従前1,534件のチェックポイントは維持し、今回のdocs更新でコードやテストを変更していない。
''';p.write_text(text)
