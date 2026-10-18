# 1975 公表予定4件：既存schedule-only入力準備

root受入済みの公式カレンダー取得phaseと、08:42:21UTCにroot受入された既存shared builder由来の**calendar原source1候補をそのまま参照**する。重複source/source-bundleは作らない。`catalyst-schedule-requests.json` は既存schedule-onlyのevent7fields・period5fields・claim13fieldsを満たす4件の入力配列。純粋な既存request validatorだけを実行し、実DB/コピーDBのreportは実行していない。

| 原文ラベル（2027年3月期） | 日付 | kind |
|---|---|---|
| 第2四半期（中間期）決算発表 | 2026-11-12 | earnings_release |
| 第2四半期（中間期）決算説明会 | 2026-11-17 | earnings_presentation |
| 第3四半期決算発表 | 2027-02-09 | earnings_release |
| 第3四半期個人投資家向け会社説明会 | 2027-02-16 | earnings_presentation |

原文は「2026年度（第98期）：2026年4月1日～2027年3月31日」と年付きの日付/対象期を明記。同一HTML liの日付と表題の対応は先行root受入で確認され、今回source.contentでも逐語対応した。年度範囲をQ2/Q3の会計開始終了日へ補わず、`period`には原ラベルだけを残す。予告なく変更する旨の留保を各根拠blockに含め、時刻/timezone/supersedesは全null。予定日をUTC/JSTの日末や管理期限へしない。

参照SHAは保存source全native objectの `models.json_text` によるもの。raw/content/normalizer hashと混同しない。引用はsource.content Unicode781:982、UTF8位置も `source-and-mapping.json` に固定。元HTTP取得08:36:53.179132UTC・公表日時unknownを保持し、予定日/研究mapping作成時刻と分ける。

**実DBのsource初回保存はnull・root接続待ち**。source欠損/availability/lineage/分類の状態をこのファイル準備で確認したとはせず、`source_bound_candidate`を称しない。後続はrootのみがsourceを保存→既存intake→実時計のread-only予定reportで点検する。そこでsource結合してもcaller mapping未認証・floating date/due null・実施未確定のままになる。既存1975caseの次の公開確認機会へ利用できるが、自動job/日程到来による決算実施/結果改善/会社予想維持を作らない。

新GET/source/DB・Storewrite/コード・共有docs・旧producer編集/財務予測・入力採用/正式IR・分岐は0。この4入力と引用・handoffをfile-onlyでfreezeしroot受入を待つ。
