# 1975 Q1公開説明資料の限定追加読解

保存済みroot `02.json` links[101]に明示された `https://www.asahikogyosha.co.jp/wp-content/uploads/2026/08/98_1st-quarter-financial-results-appendix.pdf` だけを別phase最大1 GETで取得した。200・完全1,069,126B、raw SHA `ffaba5e0bbdc0aa176a16ed6497fc1dfd35c94ac0180d23adc61ed702d4b8443`。原HTTP完了 `2026-10-16T04:26:06.566587+00:00`。開始/headers/完了/原raw保存・responseは `capture.json`/`01.json`。

同hostのrobotsは初期phaseの完全200、取得完了 `2026-10-16T04:18:24.479458+00:00` の保存規則・原SHAを再利用し、このliteralへのcan_fetchを確認した。今回の最新サーバー規則を再取得したものではない。holds-v8の12hostを再照合、固定UA・通常proxy/TLS、robots/root再GET・retry・redirect・別host・JS・検索・フォーム・Cloud診断0。初期3 GETの記録は不変。

PDF全文17頁は `text/01-full.txt` と新source.content1本に保存。**本文の意味/画像確認は物理6・7・14の3頁のみ**。表紙・目次・見出しは資料/頁の選定と書誌事項確認のみで、その他1–5/8–13/15–17の内容読了は主張しない。公表日は8月4日day精度、exact publication clockはnull。原取得時刻・後のlocal抽出観測・実DB初保存を区別する。

初期短信p4の既知説明と、今回追加された公開説明を比較した。

- 短信の「設備工事は売上増/粗利率改善」に対し、説明p6はQ1竣工物件が多く、竣工に向けて利益計上が進む傾向を示す。Q1の高い粗利益率を通期の正常利益率へ延長しない。売上の四半期推移は実績/会社見通しを分け、グラフ座標の独自数値化はしていない。
- 短信の「機器減収/損失拡大」に対し、p7は主要取引先の生産計画調整を挙げ、新規主要取引先獲得等への取り組みを説明する。実績表は設備工事/機器、2025/2026/2027年3月期の各Q1、百万円/%/ptを保持。取り組みを顧客獲得済みとは扱わない。
- 短信の「下半期受注回復見込み」に対し、p14は通期機器受注をFPD需要回復、売上を2025年3月期に大型受注したドライヤ案件の売上計上で説明する。**新規受注回復と既受注案件の売上計上は別**。年度内/下半期の成約・計上時期・利益/入金保証は認定しない。設備工事は施工体制を踏まえ通期受注微減、既存手持工事の進捗で増収を計画するため、Q1受注増を全年度へ延長しない。

`review.json`に初期原source/受入済み意味範囲のpinと比較を保存し、同じQ1短信や9値派生sourceは重複作成していない。新sourceは説明原本1本のみ。`source-quotes.json`は3頁のnative object/content/raw SHA、Unicode/UTF8 offset付き逐語引用。新予測・評価・正規化・金融採用ではなく、metadata.financial_contentはproducer内容判断でnative分類とは別。

Q1/前年同期/通期会社予想・連結segment・百万円/%/pt・営業利益と粗利益を区別し、EPS/株式分母やCFへ転用しない。正確な正常利益/将来CF、顧客回復の成立時期、既受注ドライヤ案件の期内計上・採算・現金回収、新規顧客獲得の成果等は未解決。初期短信p9/10や説明未読頁・公開Q&A本文・後日変更も未確認を維持する。

Anthropicの公開資料先行DD/metrics/guidance/strategy-changeとDamodaranの利益/期間/主体/将来CF分離を適用。既存sharedbuilderを再利用しwhole original capture/rawを保持。producer側でraw/全文/契約/stableID/3引用/3画像と初期32pins不変を照合した。汎用byte verifier未実行のためmatchedとはしない。rootの独立画像/意味受入待ち。

DBwrite・共有code/旧file変更・case・normalizer・金融採用・IR草案・外部送信は0。freeze後の追加GET予定0。
