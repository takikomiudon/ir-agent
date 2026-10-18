# 2315年次会計方針1source：分類投入準備

**準備のみ。** 受入済み [年次有報producer](../ir-case-studies-2026-10-15/2315/annual-accounting-policy-public-followup-2026-10-16/README.md)のsource-bundle全bytesをそのまま保存した。canonical jp:2315、companies/theses空、原source1件。旧7sourceは再投入/再分類せず、旧successful jobも再実行しない。

分類は現行 `ir_agent.intake.KINDS` 内の `financial_statement` / `financial_content:true` / expected_version0。p67の金融サービスの暗号資産売買差額・約定日収益認識という原文を、受入済みfullpage quoteから短く抜き、native source SHA、content SHA、Unicode/UTF8 offset・物理67/印字67/123へ固定した。新numeric factsや金融値採用ではない。

対象は第37期（2024年11月1日〜2025年10月31日）の有価証券報告書で、2026年1月29日提出。意味受入は123頁中の1/66/67だけ。特定のZaif/顧客暗号資産売買契約に関する差額・約定日の方針、市場有無別の暗号資産評価方法という**当該年度の会社方針**を保持する。現在Q3の全取引/法人範囲や全負売上、評価損益表示へ自動適用せず、有価証券のOCI法を暗号資産へ移さない。原ID/content/metadata・HTTP完了時刻・pubnull・raw/抽出来歴は不変。

`input-pins.json`は年次producer凍結manifest列挙22files、manifest、親受入の24filesだけ。同sourceの別途追加2頁読解、model/residual/currentdocs/index/native作業は準備依存に含めていない。`prepared-code-pins.json`はsrc44filesで、最新1558tests受入の9c8e77b5…manifestと一致。

## 読取baselineと限定adapt

DB main SHA `05f653b8e9b12fd29d6b92bd1ad037ef0c3d5cfc41e6e7a7c0e68c1f5683278b` をmode=ro/query_only/contextlib.closingで前後照合した。202sources/availability202/201classifications/110全完了jobs/107attempts214events107receipts、case24heads45versions141reads、pending/leased0、2315旧7source・新ID未登録を確認。Store初期化・backup/copyは0。

受入済み [補足1source runner](../ir-2315-supplement-intake-2026-10-16/README.md)から、baseline/hash/case状態・既存2315資料7件・期待件数・worker/requestID/backup名だけをadaptした。source数は1のままでAPI/journal/copy→actual/全table旧row・schema保持は同じ。`adapted-runner.diff`を保存しAST parseのみ。

rootは3つの現在文書更新を受入するまで実DB変更を保留する。本準備で文書や実DBを変更せず、その受入を先付けしない。rootがその保留を解消し、入力を読んで新規parent-input-acceptance.jsonを保存した後、rootだけがshadowを一度実行する。後のparent-acceptance.jsonとは別名で保持する。

```bash
.venv/bin/python research/ir-2315-annual-accounting-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2315-annual-accounting-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 CODE_SHA
```

CODE_SHAを受入済み44file manifestの実SHAへ置換し、将来code変更時は旧preparedを上書きせず新受入manifestを指定する。成功shadowの全table比較・同じrunner/data/code SHA受入後、rootだけがstageをactualへ変え一度実行する。actualは親入力受入/成功shadowを要求し、Git対象外data/backupsへ事前backupを作る。

旧7sourceを含む全旧row/schema/case不変をguardし、新1sourceだけ `ingest` → new_only1job → request ID付きobserved claim → complete(expected_attempt1)を行う。段階journalをfsyncし、全pipelineは単一transactionではない。失敗/不明時はjournal/backupを確認し、成功済み又は不確実なmutatorを自動再送しない。原HTTP完了/準備時刻を実DB firstsaveへ置換しない。

将来期待増分はsources+1/availability+1/classifications+1/jobs+1/attempts+1/events+2/requestreceipts+1だけ。203sources/availability203/202classes/111全完了jobs、108attempts216events108receipts、2315sources7→8、case24/45/141不変。今回成功を主張しない。

GET・DB書込み・Store初期化・backup/copy・runner/shadow/actual・旧file/共有code/doc編集・金融採用・IR送信は0。準備13filesを固定し、rootレビュー待ちで停止する。
