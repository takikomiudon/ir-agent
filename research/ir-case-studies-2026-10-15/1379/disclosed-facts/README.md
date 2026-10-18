# 1379 ホクト：正式Q1短信の公表5事実

保存済み正式短信（2027年3月期第1四半期、2026年8月12日公表日表示）のPDF1頁から、公表実績2件と会社予想3件を構造化した。日本基準・連結。新規GET・DB変更・既存case/索引変更はない。2026年10月時点の最新開示を網羅したことは未確認。

| ID末尾 | 種別・期間 | 原文値 | 構造化値 |
| --- | --- | --- | --- |
| 2027q1-basic-eps | Q1累計実績 2026-04-01〜06-30 | 14.44円/株 | 14.44 JPY-per-share |
| 2027fy-company-eps | 通期会社予想 2026-04-01〜2027-03-31 | 167.22円/株 | 167.22 JPY-per-share |
| 2027q1-operating-income | 同Q1連結営業利益実績 | 418百万円 | 418000000 JPY |
| 2027fy-company-operating-income | 同通期連結営業利益会社予想 | 7,260百万円 | 7260000000 JPY |
| 2027fy-company-annual-dividend | 同FY年間配当会社予想・合計 | 62.00円/株 | 62.00 JPY-per-share |

各fact IDの共通接頭辞は`hokto1379-`。Q1 EPS14.44には負号がなく、前年43.43円・潜在株式調整後12.37円と区別した。中間予想EPS△3.00円をQ1実績や通期予想へ転用していない。営業利益もQ1前年176百万円、通期予想と中間予想110百万円を混同していない。

配当は当年予想の合計62.00円を原表から採り、期末52.00円、前年合計55.00円と区別した。中間10.00円と期末52.00円の加算から値を作ってはいない。ダッシュ/灰色空欄を0にせず、年間配当予想を長期保証・将来DPS配列へ拡張していない。配当は発行会社の1株当たり配当で、連結利益項目とは異なる。

PDF1〜2頁の表・注記を原PDF画像で確認した。表題に連結/日本基準、実績見出しに累計と日付、通期予想見出しに期間がある。百万円未満切捨ての公表値を円へ換算するだけで、切捨て前の数値を復元しない。PDF2頁は添付四半期財務諸表の会計士/監査法人レビュー「無」、予想達成を約束しないことを明記している。数値・列・期間・範囲の意味は抽出担当の主張として保存し、モデルへの適合や採用は未検証のまま。

原source IDは`case-public:92d3398dc3d1cb38b6be2afbda4f4131aeab2494e4fe3a2835f4a1adef1397a0`、取得日時は`2026-10-15T05:15:01.401229+00:00`。reviewは`2026-10-15T05:20:54.632873+00:00`、派生資料取得日時は`2026-10-15T05:21:33.363709+00:00`で、元資料取得日へのbackdateはない。派生IDは`disclosed-facts:43b8d8f89d4eb8dc1a97242c8082d63c5ec0e2d155e0d44009f241518a2b1b78`。DBへ登録していないためDB初回保存日時は未設定。

[normalization-request.json](normalization-request.json)は元source snapshotをbundleと完全同一で保持。[normalized-bundle.json](normalized-bundle.json)は元sourceと別ID派生sourceを含み、会社のactive化や仮説は含まない。[meaning-review.json](meaning-review.json)に8引用、頁/offset、列の読み分け、画像SHA/再描画手順、残る意味上の制約がある。[verification.json](verification.json)にraw/text/snapshot/manifest/sourceID照合、全11頁の機械的再抽出一致、5 factの引用位置、normalizer replay/reproduceを記録した。

再検証はリポジトリルートで以下を実行する。既存のbundle/review時刻は変えず再計算し、検証レポート時刻だけ更新する。

```bash
.venv/bin/python research/ir-case-studies-2026-10-15/1379/disclosed-facts/build_and_verify.py
```

`financial_inputs_verified:false`、`meaning_review_required:true`、`model_adopted:false`を維持する。公表5項目に欠損はなかった。季節性を理由とするQ1の年率化・正常化、将来利益・PER・税率・ROC・成長率・確率、評価額や売買判断は作成していない。
