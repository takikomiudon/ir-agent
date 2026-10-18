# 135A：中間CFの公表実績4行を別派生へ保存

保存済み正式中間短信のPDF8頁・印刷6頁から、当期列の4行だけを既存normalizer契約で構造化した。全て**日本基準・非連結・中間累計の公表実績**であり、会社予想や将来CFではない。既存のEPS・配当等5factとは別の派生資料。新GET、実DBの読書き、既存source・5fact・索引の変更は行っていない。

## 保存した4行

| fact ID（先頭`vrain135a-2027interim-`） | 元の表行 | raw表示 | 正規化値 JPY | 表示上の意味 |
| --- | --- | --- | --- | --- |
| `operating-cashflow` | 営業活動によるキャッシュ・フロー | `223` 百万円 | `223000000` | 当中間期の営業CF純額。小計425や前年△468とは別 |
| `depreciation-cf-adjustment` | 減価償却費 | `30` 百万円 | `30000000` | 間接法の営業CF調整行。前年28とは別 |
| `ppe-acquisition-cashflow` | 有形固定資産の取得による支出 | `△100` 百万円 | `-100000000` | 投資CF内の符号付き支出。正のCAPEX入力へ変換していない |
| `receivables-contract-assets-cf-adjustment` | 売上債権及び契約資産の増減額（△は増加） | `154` 百万円 | `154000000` | 売上債権と契約資産の複合行のCF調整。資産残高増加+154ではない |

当中間会計期間は2026-03-01〜2026-08-31。比較列は2025-03-01〜2025-08-31。単独第2四半期や通期値へ換算していない。元資料は百万円未満切捨て表示であり、JPYへの乗算は表示値の明示単位変換だけで、基礎実額を1円精度で確認した意味ではない。

## 売上債権のCF表示と資産残高の符号

原文の行は次のとおりである。

> 売上債権及び契約資産の増減額（△は増加）                △418                154

行注記は**△が資産の増加を表す**としている。したがって当期の正の154を「売上債権資産が154百万円増えた」とは読まない。表示規則上の減少方向のCF調整として保持したが、その値を符号反転して貸借対照表の残高増減へ変換していない。為替・非現金変動・分類等との残高照合は未実施であり、売上債権単独の行でもない。

棚卸資産、前払費用、仕入債務、未払・契約負債等は別の行である。この154だけを運転資本全体の増減にしない。各行を合計してWC・純再投資・FCFFを作る操作もしていない。

## 引用・表列・原典

[原PDF](https://contents.xj-storage.jp/xcontents/AS06543/0e4abefd/2c7d/4512/9376/0761580b1ba5/140120260831528808.pdf)の表をローカル画像`/tmp/vrain-135a-cashflow-p8.png`で確認した。当期列・比較列・百万円・△符号を確認した担当者、画像SHA、元PDF SHAと画像化方法は[meaning-review.json](meaning-review.json)に記録している。

各factの引用は単位・当期/比較期の見出し・対象行が入る保存本文の**連続した原文**。PDF頁、印刷頁、頁内Unicode文字位置に加え、元の行全体と選択した数値tokenの位置も[normalization-request.json](normalization-request.json)へ保持した。近傍に同じ数値があることだけで列の意味を自動確認済みとはしない。

原source snapshotは`library-followup/source-bundle.json`と完全同一で、前の5項目の派生資料を原資料として連鎖参照していない。

- original ID：`case-public:4b9aaae627aa90731140aa648b9c8bf60be1767accaab06041ac23dc5f6955fb`
- 原PDF SHA：`6c7d2b098b4ac5f8ed797ff552b8be239237a54e72824cb60ab25df9d49f9515`
- 元の初回取得：`2026-10-15T04:42:37.094960+00:00`
- review実時刻：`2026-10-15T04:55:43.068876+00:00`
- derived ID：`disclosed-facts:8d3e2fabf17b9e9476c9d99e5237ca7c39fd707df13927c7d19ba994881ab224`

派生取得は今回の構造化実行時計を使い、公表日や元取得時刻へbackdateしていない。[normalized-bundle.json](normalized-bundle.json)は原資料＋派生資料の2source、companies/thesesは空。原本文/snapshotのSHA、original_source_id、引用・期間・単位・raw符号・reviewを保存した。実DBに取り込んでいない。

## 再投資点検へ渡す前に残ること

保存済みDamodaran研究方針の再投資点検へ使える公表データを集める段階であり、この4行だけで会社のmodel routeを決めていない。過去実績から正常再投資や将来入力を算出する原典式を今回追加したわけでもない。

- 減価償却30百万円はCF調整で、現金収入そのものではない。内訳や将来の償却・設備稼働対応、持続性は未確認。
- 有形固定資産取得支出△100百万円はその現金支出の範囲であり、取得原価、投資全体、維持/成長区分、正常CAPEX、純再投資へ自動採用しない。
- 営業CF223百万円には報告された税・利息・各調整の範囲がある。アンレバードFCFFではない。`CFO−CAPEX`の計算や営業利益への任意加算はしていない。
- 売上債権及び契約資産の調整154百万円は、BS残高差・運転資本全体と未照合。負債行との符号規約も同一視しない。
- 当期の4行を平常値・将来CF・投資額予想にしない。公表値の引用/算術一致と会計意味・モデル適合・正常化は別の確認である。
- 表に存在する他の行のダッシュは今回採用せず、0にしていない。欠損を埋めるための行・数値は作っていない。

全factで`financial_inputs_verified:false`、`meaning_review_required:true`。全体でも`model_adopted:false`、`working_capital_or_reinvestment_or_fcff_calculated:false`を維持した。

## オフライン検証

```bash
.venv/bin/python research/ir-case-studies-2026-10-15/135A/cashflow-disclosed-facts/build_and_verify.py
```

[verification.json](verification.json)は元3資料のraw/text/snapshot SHA、source ID再計算、PDF再抽出とJS/JSONPの非実行データ復元、4factの頁・行・数値token位置、意味レビュー6引用、既存normalizerでの再現を確認した記録。`reproduce_disclosed_fact_source`は`reproduced`となり理由は空。元snapshot一致、実行時刻が変わっても派生本文・IDが同じことを検証した。既存入力ハッシュは[baseline.json](baseline.json)に保存し、元のファイルを変更していない。
