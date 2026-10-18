# ニッスイ：公表予定3件のmonitor入力候補

[候補JSON](catalyst-schedule-candidates.json)は保存済み原文を現在の記録者が対応付けた下書きである。monitor実装への登録済み入力、過去に固定された予定監視、実施済みイベントを意味しない。記録日時は `2026-10-15T05:00:15.926847+00:00`。原source・DB・productionを変更せず、新GETも行っていない。

## 3イベント

| ID末尾 | 会社の対象期・行事 | 原文日付 | 年対応後の暦日 | time / timezone |
|---|---|---|---|---|
| 2027fy-q2-release | 2027年3月期第2四半期決算発表 | 11月06日（予定） | 2026-11-06 | null / null |
| 2027fy-q2-presentation | 同第2四半期決算説明会 | 11月10日（予定） | 2026-11-10 | null / null |
| 2027fy-q3-release | 同第3四半期決算発表 | 02月05日（予定） | 2027-02-05 | null / null |

会社IDは `jp:1332`。原文の「2026年度（令和8年度） 2026年4月～2027年3月」と各月日から年を対応付けた。2月は翌2027年である。会計対象期間の開始・終了日はここから補完していない。発表と説明会は別IDにした。

各eventのclaimsはschedule1件だけ。`occurrence_claims:[]`、`result_links:[]`で、変更検証はunknown。変更可能という注意書きは、実際に日程変更があった証拠ではない。日本企業であることからtimezoneを確定せず、floating dateとして扱う。UTC/JSTの深夜や日付到来からdue/発表済み/延期を判定しない。

## カレンダー原文とsnapshot

- source ID：`case-public:4ca42c264c3f7af4506f664ad01edbcf4c738bf920ea3efcd32a686fabec4edb`
- URL：https://www.nissui.co.jp/ir/calendar/index.html
- published_at：null、元取得：`2026-10-15T04:22:56.478724+00:00`
- canonical source snapshot SHA-256：`85a80377b7896a657a6af101c55a03f38d13d234c3a3376a5ac5cf442f82c6e5`
- 原raw SHA-256：`ac2bc17427bf1a8cf5fc149ac59ec0b3ca147b85f193a71bfb95c05fbd2122b8`
- 抽出本文SHA-256：`866ce9827bdbf89c093c1e7f563289a31f0fff5236d01aeb1394c63b074d069d`
- 保存原引用：`calendar-year-and-events`、HTML本文Unicode位置2668:2891（0-based、末尾除外）。

```text
IRカレンダー 都合により変更する場合があることを、予めご了承ください。 最新情報 2025年度 2024年度 2023年度 2022年度 2021年度 2026年度（令和8年度） 2026年4月～2027年3月 日程 タイトル 関連資料ダウンロード その他コンテンツ 02月05日（予定） 2027年3月期第3四半期決算発表 11月10日（予定） 2027年3月期第2四半期決算説明会 11月06日（予定） 2027年3月期第2四半期決算発表 
```

3claimsは同じ原引用を保持し、日付と対象期ラベルを別々に対応付ける。原文は変更せず、逐語引用と指定位置が保存sourceに一致することを確認した。引用一致はその解釈の正しさや全予定の網羅を保証しない。

## 次の公開資料で確認するCFの論点

正式1Q短信source IDは `case-public:a6203650fe32b00c12d4b6f4c5b3f4fe252431cd4449a1f2716ea658fede985b`、canonical source snapshot SHAは `9deda8530ccba8cad302629d3f600be3cde91734dd99651688433450dd163921`、元取得は `2026-10-15T04:22:54.928767+00:00`。原文 `cashflow-not-prepared` はPDF物理13頁・印刷11頁、頁内Unicode位置1657:2307。候補JSONには注記・当期/前期期間・表を含む保存引用全体を保持した。

> 当第１四半期連結累計期間に係る四半期連結キャッシュ・フロー計算書は作成しておりません。

当期は2026-04-01〜2026-06-30の2027年3月期第1四半期連結累計期間。次に利用できる当該期の公開資料で、正式CF計算書の有無、指標の対象期間・範囲、補足資料の表示との対応を確認する論点とした。2Q/3Qに必ずCFが掲載されること、説明会で同じ資料が配布されること、数値が改善することは仮定していない。モデル入力path・将来CF数値はnull、質問・仮説の登録はない。

## 原JSONと別に読んだ保存来歴

DBをmode=ro、query_only=ON、単一読取transactionで照合した。両sourceのDB JSONが保存source-bundleとcanonical一致し、既存RecordAvailabilityのsnapshot照合がavailableとなることを記録時点で確認した。sourceのraw hash/bytecount、抽出本文hash/UTF-8本文、2引用の頁/位置も確認した。

| source | 実first_saved_at | basis |
|---|---|---|
| カレンダー | 2026-10-15T04:30:14.136467+00:00 | trusted_insert |
| 1Q正式短信 | 2026-10-15T04:30:14.136467+00:00 | trusted_insert |

receiptはsource JSONへ追記せず、候補の `source_observations[].read_only_database_observation` に別記した。現実装のsource receiptのsnapshot_sha256は同じcanonical source JSONのSHAであり、rawや抽出本文SHAと区別する。初回取得と初回保存も別時刻である。

この来歴点検は、当時の分類/公開性判定、日程mappingの意味、過去のprospective commitmentを確認したものではない。mappingは今回作成した解釈で、古いsource保存時刻へbackdateしていない。最終monitor実装が原DBの分類・時点・公開性を改めて点検する必要がある。

この2ファイルは候補fixtureのみ。仮説、質問、日次job、送信、注文の追加は0件。
