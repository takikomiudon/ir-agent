# Greenblatt公式方法サイト：候補選別方針の限定比較

**価格目標を作らず使う候補選別の比較例は確認できたが、厳密な日本株用公式の入力契約は未確認。** 保存済み資料と中央収集保留を照合後、公式サイトのrobots・ホーム・実リンクの方法説明・FAQを4GETで確認した（404/200/200/200）。追加GET・別サイト探索はしていない。

出典は [Magic Formula Investing公式](https://www.magicformulainvesting.com/)、[How it Works](https://www.magicformulainvesting.com/Home/HowItWorks)、[FAQ](https://www.magicformulainvesting.com/Home/Faqs)。サイトはJoel Greenblattが一部支配するentity所有と記す。これは本人著書の全文/本人署名付きFAQを読んだという意味ではない。取得完了は2026/10/15、公表時刻は不明。

| 確認した既存方針 | 使える比較上の意味 | 未確認・適用しない範囲 |
|---|---|---|
| 低P/Eの安い株、高いreturn on capital、比較のための会計調整、上位順位群からの選択 | 目標株価や独自将来EPSを提示せず候補群を選ぶ方針の例 | **earnings yieldの厳密式、ROC分子/分母、調整項目、二指標の順位合成は、この方法頁/FAQでは未特定**。EBIT/EV等を記憶から補わず、低PEやROEへ代用しない |
| US上場株のみ。金融・utilityを財務会計の独自性で除外 | 会計上の比較可能性を考える除外理由 | 日本株の業種除外に未採用。低値動きや悪い企業だからという説明ではない |
| 最低20銘柄、別FAQで20–30銘柄の分散説明、等金額 | 相対順位に基づくポートフォリオ設計 | 数は取得原文の説明であり、新しい運用最小数/JPY配分を設定していない |
| 約1年保有し、売却後に最新財務/価格で選び直す。数週間後にリスト外でも1年保有想定 | 単一銘柄の目標価格到達ではなく、分散した候補群の入替手順 | IR返答の肯定/否定から個別の買い/売り・利確価格へ変換しない |
| 税後リターンのため利益は1年保有・損失は1年前という説明、戦略全体は少なくとも3年を強く推奨 | **保有1年と戦略継続3年は別** | 日本税制・口座/損益通算に自動適用しない。暦年末の売却日は原文から作らない。利用者の数カ月〜1年と同じ検証窓の採用方針とはしていない |

原文の短い例は “low P/E ratios ("cheap stocks") that also achieve high returns on capital ("good companies")”。同じFAQは “slight accounting adjustments” と述べるが、厳密な調整公式はこの取得範囲で示していない。金融/utilityの理由は “the unique nature of their financial accounting statements”。これらを、著書やログイン後のscreen全実装が再現できたという主張にはしない。

IRとの接点は**会計の定義と比較範囲**に限られる。会社の公開財務項目の区分・連結/内部取引・資本や資産の範囲/再分類は会社側の確認領域だが、どの調整や順位を選ぶかは著者/採用者の領域である。厳密式が未確認のまま、会計質問や数値の回答分岐を新設していない。

現行6社（135A/1518/1721/7525/8151/9765）の既存著者論点は別に残る。顧客数・売上mix・投資損益・事業区分・納入/株基準・人員/受注能力の説明だけで、この方法の調整利益/資本/順位を確定できない。6社の選定・除外・ランキングは行っていない。各社の保存記録との接点は [review.json](review.json) に限定記載した。

次に厳密な日本株実装を検討するなら、著者のearnings yield/ROC・会計調整・順位仕様と日本企業の対象財務項目/時点を先に確定する必要がある。今回、その別資料探索・新戦略採用・計算器・予測・価格/閾値変更は開始していない。

原バイト・取得完了/開始時刻・固定UA・元hrefは[capture.json](capture.json)、本文/原バイトSHAは[sources.json](sources.json)、短い逐語引用とoffsetは[quotes.json](quotes.json)、404空robotsの扱いは[robots-review.json](robots-review.json)、局所照合は[validation.json](validation.json)へ保存した。登録/Login/Stock Screener・結果・外部プロモーションリンクは未取得。DB・コード・旧成果・IR送信は変更していない。
