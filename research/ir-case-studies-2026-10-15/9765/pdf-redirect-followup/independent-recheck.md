# 9765 SESSAレポート：独立オフライン再点検

指定範囲のバイト/原文/解釈チェックは**88件成功、指摘対象の不一致0件**。元4capture（200/200/302/302）と追加PDF200の計5capture、会社notice1＋PDF1のsource、原引用2＋13件、元25fileの不変を点検した。新GET・DBアクセス・旧file変更・金融モデル/IR採用は0。

## 原文と経路

- 元4captureは各rawのSHA/実bytes/本文完了と保存textを再現。HTMLは既存Page parserでnoticeと302ページを再抽出し、noticeの全抽出fieldも一致。
- notice内の実HTTP PDF href→元captureのHTTP302 Location→追加要求HTTPS URLを照合。HTTP robotsのLocationは既存HTTPS robotsを参照し、同じ記録UAで対象pathが許可される。今回新しいネット要求やURL組立はしていない。
- PDFはapplication/pdf、`%PDF-`、4,830,456実bytes/Content-Length、16MiB未満を確認。`pdftotext -layout`をstdoutへ再実行し、保存本文と全bytes一致、物理31頁を確認。
- 両sourceのcanonical jp:9765・schema・stableID・本文/元raw/transport/extraction SHAを再計算。PDF source IDは`case-public:25c1494baa3fb143084b16ad0b83b6c872c537b135d2bf56cf18b9842c89fab3`。
- source.retrieved_atはnotice/PDFそれぞれの本文受信完了。PDFは2026-10-15T09:52:21.077140Z、published_at=null。表紙/配信表示2026-09-28とHTTP Last-Modified2026-10-06を混同しない。
- 全15quoteのsource ID・指定頁/offsetと逐語本文が一致。generic verifierは新providerのためunknown1/mismatch0のまま。今回の局所照合をgeneric verifiedへ昇格しない。

## 指定意味の点検

表紙/p25は既存画像を視認し、p27/28/31のみ保存PDFから/tmpへ画像化して視認した。全31頁を画像精読したとは主張しない。

| 論点 | 原文で確認した範囲 | 採用しないもの |
|---|---|---|
| 著者と利害 | 表紙Sessa Investment Research・チームカバレッジ、p31会社委託/対価として報酬、役職員の売買可能性 | 個人アナリストの推定、報酬額/保有事実/経済的独立性の認証 |
| EPS91.64/DPS44.00 | 表紙`FY2027/5会予`。p28もFY26Eは会社計画ベース。短信規定と違うSIRデータ処理の注記あり | 著者独自の点予測、会社短信原典と完全に同定義という自動認定 |
| 著者の上振れ見解 | p25会社利益率11.7%に対する質的上振れ、p27案件構成/単価/スライド→利益率→EPS見通し引上げのカタリスト | 自作上振れEPS・幅・確率・反証/買売閾値 |
| PER比較 | p27の12.8倍は9/7終値と会社計画による他社比較。表紙は9/25株価1,207/会社予想PER13.2倍 | 日付の統一、公正PER・目標価格・目標算式への読み替え |
| 年度表示差 | p25本文/見出しは2027/5、最終表ヘッダは画像でも26/5CE。producerは両方を保存 | 誤植と決めつけて27/5CEへ補正、当該列の財務入力採用 |

著者自身の点EPS・目標価格・数式が確認範囲に現れなかったことを、全公開資料に存在しないという結論には拡張しない。会社CAPM6～8%の引用も著者独自discount rateやproject inputにはしていない。

## 出典グラフの限界

PDF metadataの`link_provenance`は実際の旧captureファイル/SHA/302 Locationを参照し、会社notice sourceも別bundleに実在する。ただしPDFには`original_source_id(s)`が宣言されていないため、**source_originsの機械的親集合は空**。artifact経路の一致を、noticeが自動追跡されるsource親として確認済みとは扱わない。今回この形式を変更せず、将来の全親graph監査で必要なら別途検討する限界として記録した。

taskのUA記録5件は同じだが、wire/per-response request headerの独立検証は未実施。HTTP完了はDB初回保存や過去PITを証明せず、今回はreceipt台帳を読んでいない。新しい財務採用・価格/期待値・IR質問/送信・注文の判断は行っていない。
