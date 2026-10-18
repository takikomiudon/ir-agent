# 2315補足1source：初期分類投入準備

**準備のみ。** [受入済み補足原典](../ir-case-studies-2026-10-15/2315/supplement-financial-definition-followup-2026-10-16/README.md)のsource-bundle全bytesをそのまま保存した。canonical jp:2315、companies/theses空、PDF金融本文1source。旧6sourceは再投入/再分類せず、旧successful jobも再実行しない。

分類は現行 `ir_agent.intake.KINDS` 内の `earnings_presentation` / `financial_content:true` / `expected_version:0`。p17のビットコイン売却損等という逐語本文をbasis_quoteとし、元quote ID/page、native source SHA、content SHA、Unicode/UTF8 offsetを固定した。会社の損失説明は負外部売上の認識表示定義の解決ではない。p17累計/p22四半期/p9年次を分離し、指標の正常化・利益相殺・金融値採用をしない。

原source ID・content・metadata・raw/抽出来歴・取得完了時刻・published_at:nullは不変。受入済み意味範囲は物理9/17/22の3頁だけで、66頁全文を精読したとはしない。未読locator p20/57/58に関する公開解決可能性は保持し、IRだけが解決できるとは認定しない。この取り込み準備では新読解や追加GETをしていない。

`input-pins.json`は補足producerの凍結manifest列挙23files、manifest、親受入の計25filesだけ。model/residual/currentdocs/index/native作業を広くpinしない。`prepared-code-pins.json`はsrc44filesで最新1558tests受入の9c8e77b5…manifestと一致。

## baselineと限定adapt

DB main SHA `b85405d687fce2e91e9830b8cc53a81e6652f3c77169c78dd8d3eb2560b2b1d9` を、mode=ro/query_only/contextlib.closingで読取前後照合した。201sources/availability201/200classifications/109全完了jobs/106attempts212events106receipts、case23heads44versions134reads、pending/leased0、2315旧6sourceと新1ID未登録を確認。Storeは初期化せず、backup/copyも作っていない。

受入済み [旧2315 six-source runner](../ir-2315-initial-with-facts-intake-2026-10-16/README.md)から、新1source、baseline件数/hash、旧company資料6件、期待件数、新worker/requestID/backup名だけをadaptした。`adapted-runner.diff`を保存し、AST parseのみ。API/journal/copy→actual・全table旧row/schema/case保持ガードは継続する。

rootが入力を読み新規parent-input-acceptance.jsonを保存後、rootだけがshadowを一度実行する。後のparent-acceptance.jsonとは別名で保持する。CODE_SHAは受入した44file manifestの実SHAに置換する。

```bash
.venv/bin/python research/ir-2315-supplement-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2315-supplement-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 CODE_SHA
```

成功shadowの全table比較・同じrunner/data/code SHAを受入後、rootだけがstageをactualへ変え一度実行する。actualは親入力受入/成功shadowを要求し、Git対象外data/backupsへ事前backupを作る。旧source6件を含む全旧row/schema/caseは不変を要求し、新1sourceだけ `ingest` → new_only1job → request ID付きobserved claim → complete(expected_attempt1)を行う。新段階journalをfsyncし、pipeline全体を単一transactionとしない。失敗/不明時はjournal/backupを確認し、成功済み又は不確実なmutatorを自動再送しない。

将来期待増分はsources+1/availability+1/classifications+1/jobs+1/attempts+1/events+2/requestreceipts+1だけ。202sources/availability202/201classes/110全完了jobs、107attempts214events107receiptsとなり、2315sourcesは6→7、case23/44/134は不変。ここでは成功を主張しない。

原HTTP完了を実DB firstsaveへ置換しない。GET・DB書込み・Store初期化・backup/copy・runner/shadow/actual実行・旧file/共有code/doc編集・金融採用・IR送信は0。準備13filesを一度固定し、rootレビュー待ちで停止する。
