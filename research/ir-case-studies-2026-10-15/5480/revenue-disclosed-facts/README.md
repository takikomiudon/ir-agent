# 5480：既存メッセージの連結年間売上高1項目

`annual-input-followup/candidate-raw-tokens.json`の候補から、**連結売上高150,866百万円だけ**を既存normalizerで別派生へ保存した。原典は既存の2026年6月表示の株主向けメッセージで、新しく取得した正式通期短信ではない。会計基準は不明のまま、正式短信との独立照合・最新性・モデル適合は未確認。GET・実DBの読書き、既存営業利益fact・索引・sourceの変更はない。

| 欄 | 保存内容 |
| --- | --- |
| fact ID | `nyk5480-fy202603-consolidated-revenue` |
| 指標 | 原ラベル「連結売上高」 |
| raw値・単位 | `150,866` / `百万円` |
| 明示単位変換後 | `150866000000` JPY |
| 区分 | `reported_fact`。会社メッセージが述べる過去の通期実績 |
| 期 | 第144期、2025-04-01〜2026-03-31。連結、通期累計 |
| 会計基準 | `null`。日本基準やIFRSを補っていない |
| source | [株主・投資家の皆様へ](https://www.nyk.co.jp/investors/message.html)、保存`../07.json`。HTMLなのでPDF頁なし |

原文は「第144期（2025年4月1日から2026年3月31日まで）」から当連結会計年度の業績説明までを含む連続した引用で、期・「連結売上高」・数値・単位の対応を同じ本文内で確認した。[normalization-request.json](normalization-request.json)の引用範囲は元本文のUnicode位置`742:1432`、値tokenは`1279:1286`で、終端を含まない。

「前年度比21,231百万円減」は変化額であり、前年売上そのものではない。前年売上を逆算していない。他の利益指標を追加factとして取り込んでもいない。

## 原典と実時計

- original source ID：`case-public:7ebd4f421bb0d918ddc742534804347eb60927dfe2b6c6371b56af46358fcf00`
- 元の初回取得：`2026-10-15T02:46:12.089948+00:00`
- 原raw SHA：`9f1ad20e842de2161e18ec8e2c2d2367f93580ccc8fd0996ea846a2fda8f94ae`
- 表示公表月：`2026-06`。正確な公表日・時刻は不明なので`published_at:null`を維持。
- review実時刻：`2026-10-15T05:06:09.534236+00:00`
- derived source ID：`disclosed-facts:487cb89709ae01cba3c250ed113295e5383cf391599e2c4eda6dcde578c99e6f`

派生取得は今回の実構造化時計で、元取得日や6月へbackdateしていない。原source snapshotを`../source-bundle.json`と完全同一で保持した。[normalized-bundle.json](normalized-bundle.json)は原資料＋派生資料の2source、companies/thesesは空。元本文/snapshot SHAと`original_source_id`を保存し、DBには取り込んでいない。

## 営業利益との対応は同じ原典内だけ

既存の連結営業利益10,973百万円のfactは`../disclosed-facts/`にある。今回の売上と、同じ原source・同じ第144期・同じ連結範囲の記載を参照することは確認した。[same-source-context.json](same-source-context.json)に既存営業利益fact IDと派生IDを結び付けた。

ただし、**二つの派生レコードがあっても原典は同じメッセージ1本**である。独立した財務裏付けが追加されたわけではない。正式通期短信の2項目と照合済みとも扱わない。営業利益の既存派生・引用・値は変更せず、売上との比率も計算していない。

## 残る不足

正式な通期短信・明示的な比較年度表、会計基準、連結範囲の継続性、最新公表期が未確認である。2026年6月表示のメッセージを2026年10月の最新確認済み決算と記載しない。

1年の要約では全サイクル、現在規模に適合する平常利益、再投資・資本収益・資金条件は確認できない。正常売上・正常利益・将来予測・ROIC・税率の前提やモデル採用を追加していない。各factの`financial_inputs_verified:false`、`meaning_review_required:true`、全体の`model_adopted:false`を維持した。

## オフライン再現

```bash
.venv/bin/python research/ir-case-studies-2026-10-15/5480/revenue-disclosed-facts/build_and_verify.py
```

[verification.json](verification.json)は原raw/snapshot/本文のSHAと元source ID再計算、raw HTMLからの再抽出一致、引用・数値token位置、期間と候補の一致、単位変換、既存営業利益との原典・年間期対応、normalizerのreplay/reproduceを確認した記録。`reproduced`で理由は空。異なる実行時計でも派生ID・本文・metadataが同じことを確認する。

[baseline.json](baseline.json)で既存入力と既存営業利益bundleのハッシュを保持し、前後で不変を点検した。原典一致と計算再現は、正式財務資料の独立裏付けや会計意味・全サイクル・モデル適合の確認とは区別する。
