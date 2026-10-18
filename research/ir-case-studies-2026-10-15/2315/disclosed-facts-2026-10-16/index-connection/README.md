2315の親受入済み12表示値を1parentとして[正式v35](../../../disclosed-fact-index-v35.json)へ接続しました。旧v34の38parent／190fact全objectを保持し、全26社202fact／39parent／41派生source／32会社原典pairです。実台帳39派生195factと、台帳外8331／9702の2派生7factをROで実測しました。

Q3 P/L千円表示の売上・営業利益・経常損失・親会社損失と、負の基本EPSを保持します。会社定義の調整後EBITDA199百万円は独立した非GAAP概念で、CF／正常利益への採用や再構築をしません。当時の通期会社予想5値は別期間・kindで、同額107の営業利益列と経常利益列は別tokenです。中間DPS0.00は直接表示だけで、支払確認ではありません。期末／年間の未定・dashは0にせず、年間DPSを生成しません。配当の日付両端・基準日・GAAP・連結null、特別損益／税／NCIの非相殺・非正常化、将来CF／現在EPS分母／金融採用未確認も全scopeのままです。

[実intake受入](../../../../ir-2315-initial-with-facts-intake-2026-10-16/parent-acceptance.json)、[初回保存receipt](../../../../ir-2315-initial-with-facts-intake-2026-10-16/actual-source-firstsave.json)、保存済み現行分類と照合し、原5＋派生1の全6source object／native SHA／分類全object／availabilityを確認しました。実初回保存2026-10-16T05:18:48.226120+00:00と原HTTP／派生処理時刻を区別します。原通知2sourceは実保存照合に含めますが、追加fact parentは短信派生1件だけです。raw fact.source_idをindex overrideへ転記せず、enclosing entryの派生IDへ解決。旧個別overrideは不変です。

観測DBは201source／200分類／109全job完了、106attempt／212event／106receipt、pending／leased0、case23head／44版／134既読。2315 native登録前のsnapshotとして記録しました。[validation.json](validation.json)に6source照合・実件数・DB前後SHAを保持しています。

[build_index.py](build_index.py)はSQLite URI mode=ro／query_only／contextlib.closingで読み、Store／normalizer／reproducerを呼びません。既存の受入・再現receiptを参照し、旧bundle・scopeや値を再生成しません。最初のfile読取で旧社例のsource-firstsave.json名を想定しましたが本件にはなく、rg inventoryで存在確認したactual-source-firstsave.jsonのlist形式を使用しました。DB接続・生成前の有限訂正であり、元receipt変更はありません。

全依存pinと旧v34不変。DB書込み／GET／現在3docs／production／他producer変更／金融採用0。rootレビュー待ちで停止します。
