# 5480 native監視：登録前の準備のみ

case-context.jsonの3論点は採用済みDamodaranの全サイクル・現在規模・ROC/再投資/financingの整合を、会社資料へ適応した研究条件である。正常窓・正常値・予測・金融policy・株価条件・IRは未設定。既存の全サイクル/原文経路探索は再開していない。

実DBをmode=ro/query_only/closingで照合した結果はactual-readonly-source-inventory.jsonに保存した。source10件は旧原8＋同message由来の売上/OP派生2、5480のnativecaseは観測時点で0件。全sourceの保存objectが既存bundleと一致し、読取前後mainSHAは同一。旧原8のfirstsave未知をlegacy_presenceと区別して保持する。旧READMEにある未登録等は当時の記録であり、今回の実台帳観測と混同しない。

register-request.jsonはcase初回・expected-version0用の候補。review-manifest.jsonを4bootstrap共通のreview_refとし、株主message・会社概要・OP派生・売上派生だけをhandoff時刻で限定再確認した。逐語根拠はreading-evidence.jsonに固定した。残6sourceを既読扱いせず、source分類完了を定性レビュー完了としない。2派生は同原典の再表現で、独立裏付け2本ではない。

管理日はこの準備票ではnull。従ってこの版に管理日期日jobは設定されない。rootは受入後、actual-inputsで既存Anthropicの四半期点検を内部管理日へ明示適応する方針で、旧準備票を上書きせず差分を残す。

root用の確認手順（未実行）:

1. 一貫したSQLite backupから作ったdisposable copyで、会社・source/DAG・現在公開性・分類・known-by・case未登録を再確認する。WAL使用中のmainファイルだけをcpして整合したDBcopyとみなさない。
2. 管理日を変更するなら別actual-inputsと根拠fileを用意し、参照SHA・recorded/reviewed時刻・source objectを確認する。現bootstrapのID/SHAやlegacyfirstsaveは書き換えない。
3. 既存CLI `ir-agent --db COPY_DB qualitative register REQUEST --expected-version 0 --research-root /workspace/ir-agent` をcopyで使用する。正確な引数は保存help-register.txt、help-queue.txt参照。
4. 登録だけの差分と、明示caseのcopyqueueによる差分を分けて確認する。4bootstrapの引継ぎ、旧rows保持、原source/金融records不変を確認する。未読sourceがあるためqueue0は期待しない。実queue/result/CAS/leaseは未作成。
5. rootが受入とcopy検証を終えてから実登録を判断する。今回、実登録script・copyDB・Store初期化・DB書込・新GET・共有/旧file編集は0。
