# 3774 保存資料の1株数値抽出

保存済み公表資料から3数値だけを抽出した `normalize_disclosed_facts` の入力案。対象はこの資料の保存時点の開示であり、最新版の再確認や投資判断ではない。

## 出典を保持

- 原source ID: `case-public:3e8f5cc027fecef0a566a188cc6ceb29669b8988094e48c6ab25abe81ff86a6f`
- 原URL: https://www.iij.ad.jp/ir/library/financial/pdf/IIJ1Q26J.pdf
- 原初回取得日時: `2026-10-15T01:10:08.679271+00:00`（変更なし）
- 公開日: `2026-08-07`。時刻不明のため原sourceの `published_at: null` を維持。
- 原PDF SHA-256: `2f41e73809f88df8bc22e748cfd1e9aaa9002258c86a9c90dc359bdf82747047`
- 保存本文: `3774/evidence/58fa60ba292505d2.txt`、SHA-256 `f3cc58c011bbfc8f52ae8ce2ce6bdf04ff9f3f502e7177026e6f4ba6a4c3c107`
- 位置: すべてPDF第1頁。JSONの各 `location` は空でないobjectで、節・行・列を明記。
- 抽出記録日時: `2026-10-15T02:28:18.323624+00:00`。原取得日時へ遡及させない。

`disclosed-facts-draft.json` は `company_id/source/review/facts` のAPI入力をそのまま保存したもの。`source` 全体は `data/case-source-bundle.json` 内の原objectと同一で、ID・初回取得日時・本文・metadataを保持した。read-onlyで `scripts.build_case_source_bundle.build_case_source_bundle()` を呼び、保存bundleとの全体一致および元raw/snapshot/extraction/manifestのハッシュ・参照の検証が通った。

## 抽出した値

| ID | 区分 | 表示値 | 対象期 | 読み取った列 |
|---|---|---|---|---|
| `3774-fy2027-q1-quarter` | reported_fact | 24.79円/株 | 2026-04-01〜2026-06-30（第1四半期） | 基本的1株当たり四半期利益 |
| `3774-fy2027-q1-eps-forecast` | issuer_guidance | 141.03円/株 | 2026-04-01〜2027-03-31（通期会社予想） | 基本的1株当たり当期利益 |
| `3774-fy2027-q1-dps-forecast` | issuer_guidance | 43.00円/株 | 2026-04-01〜2027-03-31（通期会社予想） | 年間配当金・合計 |

逐語引用は各factの `basis_quote` に保存。引用を原保存本文から直接切り出し、改行・空白・全角数字・記号を変更していない。各引用は同じ原source、同じPDF頁にあり、値・`円`・期間ラベルを含む。表頭の「円 銭」を小数2桁の円表示として扱い、`raw_unit_label: "円"` → `unit: "JPY-per-share"`、明示倍率1で抽出した。ページ冒頭の「百万円未満…」を1株値の倍率へ流用していない。

EPSは連結短信の実績/会社予想、配当は発行会社の年間配当予想として区別。期間の開始・終了日は同頁の連結業績/予想見出しに明記された範囲を読む担当者の主張であり、配当予想行は当該会計年度との対応を記述している。希薄化後EPSの列、半期予想EPSの列、中間配当・期末配当・前期実績とは混同しない。別の本決算の通期実績EPSは今回の抽出対象外。

## API検証と限界

保存JSONをread-backして `ir_agent.disclosed_facts.normalize_disclosed_facts(request, now=<実現在UTC>)` に渡し、3値の正規化、原引用/数値トークン/単位/期間ラベルの一致、PDF頁内一致、原sourceの完全一致を確認。戻り値の派生source IDは `disclosed-facts:bbc6c518c8f6907c5478a161f712e3ff78d6660ef834820a695f075ee01b1968`。同一requestの再計算でもこのIDは一致した。派生結果は検証時のメモリ上だけに生成し、bundle/DBへ取り込んでいない。

これは引用と明示単位演算の検証であり、経済的定義・列・対象範囲・期間の妥当性は担当者の読取りを残す。全factの `financial_inputs_verified: false` / `meaning_review_required: true`、派生metadataの `forecast_values_automatically_adopted: false` を確認した。会社予想を独自予測・確率付きシナリオへ変換しない。四半期EPSの年率換算、EPS×PERの倍率、目標株価、確率、多年DPS配列、終価翌期配当、割引率、配当持続性を補完していない。単年配当予想があるだけではDDM入力契約を充足しない。

新GET・PDF再抽出・IR送信・フォーム入力・企業状態変更なし。IIJのCAPEX質問closed/no-send、パイオラックスのnot-readyという元case結論は維持する。

## 原ファイル保持の確認

作成前後で次のファイルのbytesをSHA-256照合した（すべて変更なし）。

- `data/case-source-bundle.json`: `09dc53022739abfdc8d4e88957de1ec01c33b26566c4e63564330a3a72d2118d`
- `research/ir-case-studies-2026-10-15/3774/README.md`: `c1695ef7b351d5f0468d7bfa9cfb75eb8bef7552edf9ebd8521e37c065f85861`
- `research/ir-case-studies-2026-10-15/3774/draft.json`: `9320eb485feaf6b9e3f9216c9cd4131b54de1447be670f006d2285f92a3e5b52`
- `research/ir-case-studies-2026-10-15/3774/evidence/2f41e73809f88df8bc22e748cfd1e9aaa9002258c86a9c90dc359bdf82747047.raw`: `2f41e73809f88df8bc22e748cfd1e9aaa9002258c86a9c90dc359bdf82747047`
- `research/ir-case-studies-2026-10-15/3774/evidence/58fa60ba292505d2.json`: `494e8c4c10add7415317b363d2b5c0e9ef9be35ef0c563bed8fba6415a440417`
- `research/ir-case-studies-2026-10-15/3774/evidence/58fa60ba292505d2.txt`: `f3cc58c011bbfc8f52ae8ce2ce6bdf04ff9f3f502e7177026e6f4ba6a4c3c107`
- `research/ir-case-studies-2026-10-15/manifest-source-map.json`: `498f6f979e830ea95885b4c9ad5d2ce06d8bb8bf7bd65ddfa6fc2e86d77e4f62`

## CLIによる構造化bundleの保存

`normalize-facts` を下書きへ実行し、[disclosed-facts-normalized.json](disclosed-facts-normalized.json)へ元資料と派生資料を保存した。CLIの終了コード0を確認。3数値の分類・引用・単位・対象期間を保持し、金融入力は未検証、仮説は空配列を維持した。実DB登録、予想・倍率・確率の採用、IR送信は行っていない。
