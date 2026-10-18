1975の受入済み9表示値を追加する **file-only v33候補** です。[proposed-index-v33.json](proposed-index-v33.json) はこの専用dir内だけに保存し、ルートの最終v33索引・現在値docsは作成／変更していません。実DB接続も行いません。

旧[v32](../../../disclosed-fact-index-v32.json)の36parent／171factは全fieldを保持し、1975の原短信に基づく1parent／9factだけをappendします。計算した候補全体は24社・180fact・37parent・39派生source・30会社原典pairです。[expected-diff.json](expected-diff.json) と [validation.json](validation.json) が旧全object不変と件数の証跡です。

raw fact.source_idは引用元の原短信IDです。新entryではこの値をfact単位のindexoverrideに転記せず、enclosing entry.source_idの新派生IDへ解決させます。既存個別source／artifact overrideは全て不変です。9値のperiod／scope／unit／kind等は受入bundleの値をそのままprojectします。

Q1実績と8月4日時点会社予想を分け、EPSの現在分母／予想最新性は未認定です。DPSは当年予想の年間合計144.00だけで、前年同額・中間72.00・期末72.00を混ぜず合算しません。年度両端・基準日・GAAP・連結null、DDM採用falseを保持します。5月14日参照は業績予想だけです。別取得の説明PDFは追加していません。

新entryの `derived_source_imported_into_actual_database:false` はこの準備段階の状態です。旧 `actual_research_source_connections` はv32に記録された歴史snapshotを丸ごと残しており、候補全体の現在DB状態を表しません。追加の `candidate_connection_state` とlayout_noteにその境界を明記し、将来の登録完了・件数・firstsaveを先取りしません。金融入力採用はfalseです。

[input-pins.json](input-pins.json) は存在する凍結依存45fileだけをpinし、未作成のactual receipt等は含めません。[親受入](../parent-acceptance.json)・既存生成／再現receiptを読みますが、この段階でnormalizer／reproducerを再実行しません。[build_index.py](build_index.py) はstdlibのfile処理のみで、同名出力があれば停止します。[manifest.json](manifest.json) は成果と依存SHAを保持します。

次段はrootの実intake完了通知・実receipt・DB SHAを受けた別指示後です。その段階でRO/query_only/closingによるsource全object／availability／分類／実件数を確認し、候補の未接続状態や歴史DB注記を適切に更新してから、最終v33を別に作成します。本準備ではその段階を実行しません。DB／GET／production code／共有docs／旧index変更はいずれも0です。
