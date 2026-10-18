# ニッスイ（1332）：未着手台帳1社の初期公開調査

**実DBに公開source未登録だった先頭1社を調べ、公式補足資料と公開決算Q&Aを保存した。投資先選定・評価・送信は行っていない。** この1社で今回の作業を区切る。

## 抽出と現在状態

1,819社の確認済み窓口台帳 `research/ir-recovery-2026-10-13/contact-candidates.csv` と実DB `data/ir-research-2026-10-15.sqlite3` をread-onlyで照合。観測時は公開sourceが3774/5480/5988にだけあり、未登録1,816社を証券コード昇順にした先頭は1332ニッスイ。選定日時・台帳SHA・既存会社snapshot・件数を [selection.json](selection.json) に保存した。

既存会社は `jp:1332`、watch・非保有。会社ID/コードは既存台帳・実DBに結び、今回の公式IR本文には「株式会社ニッスイ」の社名と公式rootからの導線を確認。新しい会社を作成せず、status・保有・実DBを変更していない。過去確認窓口は台帳上のフォームURLで、個人受付はnot_stated。現在の受付・沈黙期間・送信適格性は再確認していない。

## 5 GETの取得範囲

| capture ID | 公式URL/資料 | HTTP | 初回取得UTC |
|---|---|---|---|
| nissui1332-01 | [robots.txt](https://www.nissui.co.jp/robots.txt) | 200 | `2026-10-15T04:15:18.559955+00:00` |
| nissui1332-02 | [ニッスイ公式サイト](https://www.nissui.co.jp/) | 200 | `2026-10-15T04:15:20.530444+00:00` |
| nissui1332-03 | [IR情報 | ニッスイ](https://www.nissui.co.jp/ir/index.html) | 200 | `2026-10-15T04:15:39.781699+00:00` |
| nissui1332-04 | [2027-1q_supplemental-documents.pdf](https://www.nissui.co.jp/ir/download/business_report/2027-1q_supplemental-documents.pdf) | 200 | `2026-10-15T04:16:03.351033+00:00` |
| nissui1332-05 | [2027年3月期第1四半期決算 決算IR説明会Q&A要旨 | 決算短信・決算説明会資料 | IR情報 | ニッスイ](https://www.nissui.co.jp/ir/ir_library/qa/2026_1q/index.html) | 200 | `2026-10-15T04:16:05.758398+00:00` |

公式rootは既存台帳の確認済みURL。robotsを1回確認し、以後は取得公式ページの明示リンクだけを各1回たどった。再試行・リダイレクト・URL/endpoint推測・接続診断・script実行なし。全件200。公式IR入口の最新欄は2027年3月期1Q・2026年8月6日発表で、同一hostのスクリプト付き決算補足PDFと当決算のQ&A要旨を取得した。

次回発表予定はIRカレンダーの存在/URLまで確認し、本文日付は未取得のためnull。補足資料は会社表示の四半期として扱い、正確な期首期末/会計基準/連結範囲は未取得の決算短信本文へ一般知識から補わない。公開Q&Aの開催日と公開日時を混同しない。

原raw・snapshot・本文、すべてのSHAと出典/引用は [sources.json](sources.json) / [manifest.json](manifest.json)。[source-bundle.json](source-bundle.json) は既存source契約の5資料、companies/thesesは空。初回取得日時を維持し、全sourceでfinancial_inputs_verified=false。日付だけのPDFはpublished_at=null＋metadata.publication_date=2026-08-06。Q&Aは開催日2026-08-06のみ記録し、公開日は未確認。

## 事業と公開説明

補足資料のセグメントは水産、食品、ファインケミカル、物流等。漁業・養殖/加工商事、食品工場、医薬品・機能性原料を扱う説明がある。会社は魚価、原材料/飼料・魚粉魚油、為替、生残率・魚体重、工場投資・償却・運転資本の影響を説明する。四半期の好調をそのまま持続利益とせず、投資回収/新規連結/評価損益の区分を確認する必要がある。

## 公開Q&Aで既に解ける点

- 南米養殖のSA社/Yadran社を分け、事業損益と在池魚評価を別に説明。補足PDF27頁にはIFRS在池魚評価・未実現利益調整の定義と、前年SA社/当年SA社・Yadran社という比較範囲の差もある。
- Yadranの改善遅延・黒字化時期、魚病/低酸素について会社は公開回答済み。ただし4Q以降黒字化は会社目標で、達成実績ではない。
- 最終設備能力に対する約25%の稼働率と、導入済みラインほぼフル稼働は分母が違うと回答済み。25%を単純な4倍増収余地にしない。
- エルニーニョ/魚粉魚油価格から漁業・調達・飼料コストへの影響、四半期CF悪化の会社説明は公開済み。会社説明を独自の価格/損益感応度や持続CF予測へ変換しない。

同じ説明を未解決IR質問として送る必要はない。今回の質問草案は0件。回答後にどのモデル入力・判断が変わるかを未定義のまま質問準備済みとしない。

## モデル適合と次の不足

Anthropicのearnings-preview/thesis-trackerの公開資料先行・企業固有指標・反証/変更なしの記録を参照し、Damodaranの既存routingに沿って点検を整理した。書式/点検項目はproject適応で、著者がこの銘柄を選んだという意味ではない。

| 点検 | status | 確認内容/不足 |
|---|---|---|
| business_and_composition | supported | 当期資料に水産/食品/ファインケミカル/物流/その他の区分。水産の漁業・養殖/加工商事、食品工場、医薬品・機能性原料を扱う説明あり。 |
| latest_linked_results_and_qa | supported | 取得時IR入口の最新決算欄は2027年3月期1Q（2026年8月6日発表）。スクリプト付き補足資料と当該公開Q&A本文を取得。 |
| scheduled_dates | needs_data | 公式IRカレンダーへの明示リンクは保存した。 |
| cyclical_and_commodity_review | review_warranted | 会社は魚価/飼料原料/原材料/為替/漁獲・生残率/価格改定を説明。公表四半期には事業損益と在池魚評価も含まれる。 |
| reinvestment_scale_and_funding | needs_data | 工場投資・償却増、買収関連返済/運転資本・借入の当四半期説明と、最終能力/導入済みラインの分母区分は公表済み。 |
| financial_equity_regulated_capital_route | unknown | 金融仲介/規制資本を使うモデルの該当性を事業実態/規制資料で別途点検。水産・農林業というタグだけで否定も肯定もしない。 |
| young_loss_route | unknown | Yadran子会社の黒字化計画があることと、企業全体をyoung-loss企業に分類することは別。 |
| ordinary_model_suitability | needs_data | 正規化する利益/在庫評価とCFの関係、セグメント混合・新規連結、税/非支配持分/株数の整合、明示的な将来入力。1四半期の実績からEPS×PER/DCFの妥当性を自動認定しない。 |

次は既に保存した公式リンクからカレンダー、正式事業説明、決算短信/有報注記を確認する余地があるが、今回の5 GETでは行わない。周期全体を含む比較可能な履歴、現在規模・新規連結、在池魚評価とCF、維持/成長投資、資金条件・税/非支配/株数が不足。景気/商品価格の点検根拠があるため研究上cyclical reviewを残すが、現在局面・固定正常化年数・正常利益率はnull。業種タグや子会社の赤字だけで会社全体を除外/young-lossへ分類しない。

株価・確率・閾値・評価額・モデル予想・売買判断の作成、実DB登録・intake完了・質問登録・IR送信なし。

## 代表引用

### latest-release-links

`case-public:a2928ac60cba83157b384e9dcc145660407823ce06d3d32cc9128d302840da87`、公式IR入口が最新として示す決算・補足資料・Q&A。HTMLの文字位置 `2822:2943`。対象期: `{"label": "2027年3月期第1四半期（会社表示）", "start_date": null, "end_date": null, "note": "This supplement labels the reporting quarter; exact financial statement boundary dates must be confirmed from the linked uncollected earnings release"}`。

> 最新決算資料 2027年3月期 第１四半期決算（2026年8月6日発表） 決算短信 決算短信（PDF）835KB 決算短信補足資料（PDF）1.6MB 動画配信 決算短信補足資料（スクリプト付き）（PDF）1.4MB Q&A要旨（HTML） 

### qa-fish-input-risk

`case-public:4d94dab44227e9323c57efba272a030a4b27d10be2bfaacb66a5e37b3d46d329`、公開Q&A：漁獲/飼料コスト・調達・価格転嫁の会社見方。HTMLの文字位置 `3310:3701`。対象期: `{"event_date": "2026-08-06", "as_stated": "今年度/2027年度以降という会社見通し"}`。

> エルニーニョによる水産事業への影響をどのように見ているか。 水温変化による漁業・養殖への影響に加え、魚粉・魚油の原料魚の漁獲減少による価格上昇や調達面への影響を想定している。長期在庫の確保や調達先の多様化などを進めており、通常のエルニーニョの期間であれば対応可能と考えている。 魚粉・魚油価格の上昇は、養殖事業へどのような影響を与えるか。 魚粉・魚油価格の上昇は、飼料価格を通じて養殖事業のコスト増要因となる。今年度の影響は限定的と見ているが、価格上昇が継続した場合は、2027年度以降の養殖コスト上昇につながる可能性がある。 魚粉・魚油価格の上昇を踏まえ、養殖事業はコストをどのように吸収していく考えか。 飼料配合や原料使用の最適化、生産性改善などによりコスト上昇の抑制を図る。あわせて、海外養殖事業のノウハウ活用や必要に応じた価格改定を進め、中長期的な収益性の維持に取り組む。 

### qa-fish-profit-split

`case-public:4d94dab44227e9323c57efba272a030a4b27d10be2bfaacb66a5e37b3d46d329`、公開Q&A：SAとYadran、事業損益と在池魚評価を分ける説明。HTMLの文字位置 `4015:4167`。対象期: `{"label": "2027年3月期第1四半期（会社表示）", "start_date": null, "end_date": null, "note": "This supplement labels the reporting quarter; exact financial statement boundary dates must be confirmed from the linked uncollected earnings release"}`。

> 南米養殖事業の減益要因について、Yadran社とSA社を分けて具体的に教えてほしい。 SA社は前年同期比で事業損益は増益だが、在池魚評価がマイナスとなった。Yadran社は計画比で事業損益・在池魚評価ともに計画を下回っており、南米養殖事業全体ではYadran社のマイナス影響が相対的に大きくなっている。 

### qa-target-not-result

`case-public:4d94dab44227e9323c57efba272a030a4b27d10be2bfaacb66a5e37b3d46d329`、公開Q&A：黒字化約3か月遅延・局所要因・単一原因未特定という会社説明。HTMLの文字位置 `4167:4663`。対象期: `{"label": "2027年3月期会社予想/施策。実績と区別", "start_date": null, "end_date": null}`。

> Yadran社の収益改善の進捗はどうか。 Yadran社の収益改善は進んでいるものの、当初計画に対して遅れが生じている。下半期から見込んでいた単月黒字化は約3か月後ろ倒しとなる見込みであり、魚病や低酸素など生産面・環境面の課題への対応を進め、第4四半期以降の黒字化を目指している。 Yadran社の収益改善の遅れの要因となっている魚病・低酸素は、SA社にも影響が及ぶような地域全体の問題と捉えてよいか。 Yadran社の収益改善の遅れは、一部の生け簀における成育状況や環境要因などによるもので、地域全体で深刻な問題が発生しているとは認識していない。SA社については生残率や養殖成績が前年を上回っており、現時点で同様の影響は確認していない。 Yadran社における収益改善の遅れについて、デューデリジェンス時点との違いの要因を教えてほしい。 デューデリジェンス時点では可能な範囲で魚の状態などを確認していたが、その後の育成過程で当初想定していた成育状況に至らないことが判明した。養殖事業では魚の将来の成育状況を事前に完全に把握することは難しく、現時点でも単一の原因を特定するには至っていない。 

### qa-utilization-denominator

`case-public:4d94dab44227e9323c57efba272a030a4b27d10be2bfaacb66a5e37b3d46d329`、公開Q&A：最終設備能力約25%と導入済みラインほぼフル稼働は異なる分母。HTMLの文字位置 `5157:5296`。対象期: `{"event_date": "2026-08-06", "future_target": "2028年頃という会社見方。独自予測ではない"}`。

> 新設・増設した海外食品工場の稼働状況はどうか。 新工場は最終設備能力に対して約25％の稼働率となっているが、現時点ではすべてのラインを導入しているわけではない。導入済みのラインはほぼフル稼働しており、今後順次ラインを増設し、2028年頃までに設備全体のフル稼働を目指している。 

## 親による実台帳の取り込み

[実分類記録](actual-intake.json)に、親が5raw/text/snapshot SHAと13引用の位置を照合した結果を保存した。5資料を追加し、kindはrobots=other、公式home/IR入口=index_only、補足=earnings_presentation、公開決算Q&A=qaとして分類。旧29sourceと既存会社のwatch/非保有は不変。実台帳は4社の34source/34分類、完了intake5件となった。新1件のlease/event/要求receiptを記録したが、過去の取得・分析全体のactive時間や会社処理能力は計測していない。金融入力・評価額・実送信は追加していない。
