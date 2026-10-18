# 4318報告PL派生1source：接続準備

このfolderはprepare-only。rootだけがrunnerを実行する。現在の実DBをread-only/query_only/closingで確認し、原source一致・派生未保存・pending/leased0・既存case v4/config1をbaselineへ保存した。Store/backup/clone/ingest/queue/claim/completeは実行していない。

run_once.pyは既存1source runnerの限定適応。source-bundleは新派生1件だけ、分類はother/financial_content=true。コピーDB shadow→独立レビュー→同runner actualで進め、各成功結果をexclusive JSONへfsyncしてから次操作へ進む。journalがsentinelとなり再実行を拒否する。pipeline全体は単一transactionではなく、失敗時に自動resume/retryしない。各段階で旧全row・schema・case状態保持と規定増分だけを検証する。

実行前にrootがparent-input-acceptance.json（status accepted_*）を保存し、現在の全srcコードSHA一覧をexecution-code-pinsとして指定する。例：`.venv/bin/python -B research/ir-4318-reported-PL-connection-2026-10-16/run_once.py shadow --execution-code-pins research/ir-4318-reported-PL-connection-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 <当該fileのSHA>`。actualは成功shadowのreceiptと同じpins/baselineを要求する。rootが実行までにDBを変えた場合、古いbaselineで進まず別の明示した改版が必要。

qualitative-handoff.jsonは次の正当packet向けの参考で、読了/完了の先取りではない。case/config/Jan16をrunnerで変更せず、rootが実保存後にnativequeue→claim→packetを確認し、結果を別phaseで作成する。旧正常EPS税gap・2千円表示差原因null・日本OP≠OIADP・D&A内包未確認を維持する。

prepare_index_candidate.pyはDBから独立した純file helper。旧v42を全保持し4factをappendした候補だけを、指定のresearch内新fileへ出す。共有v43の名前や既存fileへの上書きを拒否する。helper自体も今回実行していない。実保存時刻/分類/availabilityを認証せず、rootのactual receipt後にcanonical接続を別途行う。価格・EV/TTM/正常利益・金融採用・IR送信0。
