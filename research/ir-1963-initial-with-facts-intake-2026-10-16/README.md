# 1963：原5＋推奨派生1sourceの初期分類準備

**準備のみ・rootレビュー待ち。runner/shadow/actual実行0。** 受入済み初期bundle3source（事業説明/静的一覧/完全14頁短信）、公開説明bundle2source（完全18頁概要/4頁QA）、受入済み短信9fact派生1sourceを束ねた。正規化bundle内の原短信は初期bundleの同sourceと全object一致し、重複追加しない。元ID/content/metadata/取得時刻/公表day・pubnullを変更していない。companies/thesesは空で、会社マスター・株式/予測・金融thesisを作らない。

|source|分類enum|financial_content|
|---|---|---|
|公式rootのEPC事業説明|business_description|false|
|決算資料・公開QAの静的一覧|index_only|false|
|Q1完全短信|financial_statement|true|
|当時Q1決算概要|earnings_presentation|true|
|会社が公開した説明会QA|qa|true|
|同短信9表示の出典付き構造化|other|true|

現行Intake.KINDSとworkflowを読み、許されるenumを使用した。financial_presentationという新kindは作っていない。各sourceを1回ずつ、expected_version0と逐語basis_quote/理由へ対応し、classification-evidence.jsonにsource native/content SHAと文字/UTF8 spanを固定した。派生sourceはminified JSON内の実substringを使い、整形・復号した文字列を原文引用と扱わない。公開QAの分類根拠は会社回答であり、左列質問者の25,608百万円/7月1日を会社の対価/完了日認証にしない。

当時FY2026=2027年3月期、Q1/年度/予想、百万円/億円、通常EPS/潜在調整後、新規連結/四半期固有処理、営業外FX・税・NCIを分ける。粗利益の約30億比較と前年比営業利益/FXを混同せず、Q2特別利益約200億をQ1/営業利益/CFOへ移さない。DPS年度境界/基準日/GAAP/連結null、現分母/現在予想/正常利益/将来CF未採用を保持する。初回研究/数値抽出時点の公開説明未読という記録は過去の範囲であり、今回の公開概要/QA受入を否定する現在状態へ持ち込まない。native caseや管理日・IR質問を追加する処理はない。

source-map.jsonは3原bundle/pointer/SHAと各root受入を示す。原input90fileをinput-pins.jsonへ固定。method-reference-pins.jsonは旧1950runner/workflowという準備時の方法参照で、実行codeの承認ではない。prepared-code-pins.jsonは準備時のsrc43filesの履歴観測で、他担当のoptional質問参照コード編集により現在codeとの差が既にある。履歴を上書きせず、rootが新版を独立レビューして**別execution-code-pins.json**へ現在のsrc/ir_agent全.pyの相対path→SHA mappingを保存し、そのfile SHAを指定するまでrunnerを使わない。runnerは全path集合と全SHAを両stageで照合する。旧manifestの一致を新code受入と解釈しない。

原正規化の原典全object一致を確認し、既存reproducerはreproduced/matched_supplied_snapshot。新numericfact生成は0。入力準備の最初のコマンドはsystem pythonでir_agent importに失敗したため、既存.venv/bin/pythonで修正した（失敗はAPI/ファイル作成前、preparation-corrections.json）。runnerはAST構文確認だけでimport/呼出しをしていない。

## rootが受入後に行う有限手順

1. parent-input-acceptance.jsonへ入力受入を新規保存し、source/classification/source-map/pins/runnerを独立確認する。実行後のparent-acceptance.jsonとは別名で保持する。現在codeを受入後、新execution-code-pins.jsonとそのSHAを固定する。prepared-code-pins.jsonは書換えない。
2. rootだけが次を一度実行する。以下のAPPROVED_SHAは受入済み新manifestの実SHAへ置換する。現準備時点ではまだ実行していない。

   `.venv/bin/python research/ir-1963-initial-with-facts-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-1963-initial-with-facts-intake-2026-10-16/execution-code-pins.json --execution-code-pins-sha256 APPROVED_SHA`

3. shadowの全table旧row保持/schema/currentcase不変・7table増分・原6source完全一致を独立確認する。失敗時はjournalとcopy/backupを確認し、成功済み又は不確実なmutatorを再送しない。shadow成功後も新code/input変更があれば同じreceiptをactualへ流用しない。
4. rootだけが同じ引数のstageをactualへ変えて一度実行する。actualはparent-input受入・成功shadow・同じrunner/data/execution-code SHAとbaseline DB SHAを要求し、Git対象外のdata/backupsへ完全backupを作ってからStoreを実DBへ渡す。shadowではStoreは/tmpのcopyだけへ渡す。完了後の親受入/現在文書更新はrootの別処理。

APIは実時計でHarness.ingest(source-only)→Intake.queue(company_id=jp:1963,new_only=True)→要求ID付きobserved Harness.claim→6件classificationをHarness.complete(expected_attempt1)の1jobだけ。各段階でcompany/source IDs・全snapshot・packetSHA/worker/generation/leaseを点検する。stage別の新規journalへbegin/succeededをfsyncし、バックアップと要求IDを記録する。pipeline全体は単一transactionではない。実sourceのfirstsaveは後の実ingest時刻であり、原HTTPや今回の準備時刻から作らない。

baselineはDB mainSHA9204bf1af5260b61e81ab50b77e90ea914009e750723dcd17752d46ed55bce4d、180sources/179classes/105全完了job/102attempt204event102receipt、20case41版119既読、pending/leased0。準備ではmode=ro/query_only/contextlib.closingのみで、この件数/既存company1963/原source0/新6ID未登録を確認した。

将来stageの期待差分はsources+6/availability+6/classes+6/job+1/attempt+1/event+2/requestreceipt+1だけ。186sources/185classes/106全完了job、103attempt206event103receiptとなり、case20/41版119既読/全他旧rowは不変を要求する。ここではその成功を主張しない。新GET・DB書込み・backup作成・shadow/actual・production/shared編集・数値/金融採用・外部送信は0。rootレビュー待ちで停止する。
