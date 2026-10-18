# 1379：Shared Research申告の価格snapshot候補

**後続記録（05:43:42 UTC）：親担当が原HTML・静的JSON・4項目・実DBの親source・IDとquote pathを独立照合し、実DBへ市場source1件を取り込み済み。** [親照合](root-recheck.json)と[取り込み結果](actual-ingest.json)を参照する。実台帳は61sources（公開60＋市場1）/60classifications。他の会社状態・既存source・job・仮説・質問は不変。以下の「DBへ登録していない」は、05:40時点の抽出担当作業の範囲を記す。価格鮮度・現在値・金融入力の採用は依然未確認である。

**保存済みHTMLの静的JSONから指定4フィールドだけを抽出した。価格は提供者申告の2,048円、quote時刻は`2026-10-14T06:30:00.000Z`。live/current価格、取引所による独立検証済み価格、金融モデル採用とは扱わない。** 新GET、DB読書き、既存source/他研究/productionの変更、valuation・仮説・policy・注文・送信は0件。

[取り込み候補bundle](source-bundle.json)は新market_data source1件のみ。`companies=[]/theses=[]`、`requires_research:false`、`published_at:null`。親による独立照合と取り込みは別で、この作業ではDBへ登録していない。[quote候補](quote-candidate.json)は既存decision形式で、priceと観測時刻を派生sourceの実fieldに結ぶ。

| 原field path | 保存値 | 派生表現 |
|---|---|---|
| company.stock.ticker | 1379（文字列） | company_id jp:1379 |
| company.stock.currency | JPY | currency JPY |
| company.stock.price | 2048（JSON整数） | price_jpy "2048" |
| company.stock.quotedAt | 2026-10-14T06:30:00.000Z | observed_atを逐語保持、observation_precision instant |

出典は[Shared Researchのホクト会社ページ](https://sharedresearch.jp/ja/companies/1379)。`instant`は提供者のtimestamp表記の精度で、取引所の約定時刻・終値であるとの独立検証ではない。価格種別、取引所/市場、調整/非調整、上流feedと遅延、売買可能性は未確認。株価2048円を現在の注文価格や実行条件へ採用しない。

## 3つの時刻を分ける

- 提供者申告quote：`2026-10-14T06:30:00.000Z`。
- 原HTMLの初回取得：`2026-10-15T05:28:30.141744+00:00`。metadata別欄へ保存し、上書きしていない。
- 派生sourceの実抽出：`2026-10-15T05:40:23.213016+00:00`。この時計を派生retrieved_atに用いた。DB初回保存時刻ではない。

quotedAtをpublished_atへ転用していない。原レポートのselectedProject更新日時も、stock価格の公表日時として使っていない。鮮度policyは未採用であり、このsnapshotが現在利用できるかの判定もしていない。

## 原文はreportContentとstockを分けて辿る

親sourceは `case-public:a14372edbaf8c2897b8553a1a93dc1e4b1dc63859a14ce2f716bdb571a862e7b`、新sourceは `sharedresearch-stock:14c38b71b93e2f60a03c639c0071bbd8d21a10036b54969a1c3402a83be9639b`。`metadata.original_source_ids`に親IDを保持した。ただし親source.contentはreportContentの可視本文で、構造化company.stockではない。その本文のfield pathに価格があると偽っていない。

[抽出証跡](stock-field-extraction.json)は次の連鎖を固定する。

1. 親source metadataが指す保存原HTML。raw SHA-256は `d938ae48895d52b61b2ae6a8e31e5c09f6e4f47245b77c4480871768ed2e9dcd`、3,314,925 bytes。
2. 原transport snapshot/初回取得・全文UTF-8バイト、元保存textとの一致。
3. `window.state`代入が1つであること、JSON値の終端とsemicolon、重複key/非有限値拒否。JavaScriptを実行しない。
4. 原HTML上のJSON位置 `32755:2915520` とpayload SHA `128989a4efb6707f7ff530cfc5ddb82520739a5e49ff55cb0b10ee05c86d9c0c`。既存guard記録と一致。
5. 抽出stateと保存`02.embedded-state.json`の値一致。保存JSONファイルSHAは `3fdec46616ed41a4b52b14a1a86b59257f913397b7cbe477eb05b0c62a90fe25`。payloadの原字列SHAとは区別する。
6. 親会社ID/URL、state.company.tick、stock.tickerの1379対応。指定4field pathの値だけから派生contentを再現。

親sourceのstable ID/本文hashも照合したが、その本文の一致だけでstock値を支持したとはしていない。一般のdecision quote照合が確認するのは派生source内のfield値であり、このcaseのraw/window.state抽出を自動replayする強制機構ではない。取り込み前にraw連鎖の独立点検が必要である。

## 保存物と再現

- [normalized-stock.json](normalized-stock.json)：source.contentとUTF-8バイト一致する正規化payload。raw_stock_fieldsは4項目だけ。
- [source-bundle.json](source-bundle.json)、[quote-candidate.json](quote-candidate.json)：既存のsource/quote形。price_pathはcontent.price_jpy、observed_at_pathはcontent.observed_at。
- [stock-field-extraction.json](stock-field-extraction.json)：全原path/hash/guard/field対応。
- [meaning-review.json](meaning-review.json)：提供者申告と独立検証・金融採用の区別。
- [baseline.json](baseline.json)：実初回抽出時刻と元ファイルSHAを固定。
- [verification.json](verification.json)：source契約、値とfield path、元資料不変、静的JSON再抽出、有限8反例の結果。

```bash
.venv/bin/python research/ir-case-studies-2026-10-15/1379/provider-market-snapshot/build_and_verify.py
```

通常実行は保存済み実抽出時刻を固定して再構築・比較し、stdoutへ結果だけを返す。source、baseline、verificationを再保存せず、新しい取得と主張しない。`--build`はbaseline不在時だけ実時計で初期作成でき、既存時は拒否する。再現にネットワーク/DB/JS/追加依存は不要。元ファイルを書き換えて検証することもしない。

source IDは既存stable_source_idヘルパーを使った。source契約のvalidate_sourceとdecision._source_fieldで両quote pathを点検した。型違いの価格、ticker/通貨の不一致、原取得より未来のquotedAt、重複marker/JSON key、非有限値、semicolon欠損の有限8反例をmemory-onlyで拒否した。金融モデル全体を実行したテストではない。

marketCap/sharesOutstanding/PE/PBR/ROEは、元JSONにあることと定義・期間・分母が検証済みであることを分け、値を抽出/採用していない。全体で `financial_inputs_verified:false`、`model_adopted:false` を維持する。
