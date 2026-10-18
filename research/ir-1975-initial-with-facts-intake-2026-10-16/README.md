# 1975：4資料の初期分類投入準備

本成果は**準備のみ**。親受入済み原文3件（公式root、Q1短信、Q1説明資料）と、既存短信からの9数値派生1件をsource-only bundleへまとめた。正規化bundleに含まれる短信原本は重複投入しない。会社・thesisは空配列、金融入力の採用・株価/予測の更新・IR登録/送信は0。

| sourceの役割 | 分類 / financial_content | 意味の境界 |
| --- | --- | --- |
| 公式rootのIR新着・リンク一覧 | index_only / false | ページに事業案内もあるが、この分類はIR一覧として扱う。リンク先の財務本文を本頁の内容としない |
| 2027年3月期Q1日本基準連結短信 | financial_statement / true | 8月4日付資料。Q1実績と当時通期会社予想、通常EPS、年間合計DPS、百万円未満切捨てを維持 |
| 同Q1会社説明資料 | earnings_presentation / true | Q1竣工・利益計上時期の説明、建設/機器事業差、需要回復見込みと既受注の売上計上を分離。正常利益や将来回復の保証にしない |
| 元短信の9表示の構造化 | other / true | 同じ原開示の派生資料。新開示・独立予測ではなく、意味/金融妥当性は未認証 |

原sourceは受入済みのJSON object全fieldと一致し、ID・content・取得完了時刻・published_at:null・元metadataを保持した。初期資料の意味受入は短信物理1/2/4/7頁、説明物理6/7/14頁の既存親receiptを再利用し、全PDFの新しい精読とはしない。

`classification-evidence.json`は4逐語引用をexact source.contentへUnicode文字offsetとUTF8 byte offsetで結び、native SHAは `sha256(models.json_text(source).encode('utf-8'))`。compact JSONのSHAと混同しない。`source-map.json`は取得raw SHA/bytes・snapshot SHA・保存抽出本文とcontent一致も保持する。構造化sourceは純粋reproducerで9factsを再現し、原短信snapshot一致を確認した。新numeric factの生成は0。

## 固定入力と実行前の受入

`input-pins.json`は受入済み3フォルダのproducer manifest列挙原資料・manifest・parent acceptanceだけをpinする。別担当のindex準備subdir、native case、最新監視・共有文書等を網羅pinしていない。`prepared-code-pins.json`は現行srcの44 Python filesで、1558tests受入時の `fixed-code-under-test-pins.json` と完全一致した。現在はprepared=currentだが、将来の実行時にはrunnerが再照合する。

方法は受入済み [1963の準備](../ir-1963-initial-with-facts-intake-2026-10-16/README.md) とrunnerを再利用した。`adapted-runner.diff`の変更は会社・source数・基準DB hash/件数・case件数・作業ID/backup名と結果件数。初期company1819件の明示チェックを追加した。API・journal・copy→actual・旧row保持の仕組みは変えていない。

rootは入力とrunnerを読んだ後、まず新規 `parent-input-acceptance.json` を保存する。後の実行受入 `parent-acceptance.json` と別名で保持する。rootだけが次を実行できる。以下のCODE_SHAは受入済み44file manifestの実SHAへ置換し、コードが変わった場合は旧preparedを上書きせず新しい受入manifestを渡す。

```bash
.venv/bin/python research/ir-1975-initial-with-facts-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-1975-initial-with-facts-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 CODE_SHA
```

shadow全table比較が成功し、同じrunner/data/execution-code SHAを受入した後に、rootがstageを `actual` へ変えて1回だけ実行する。actualはparent入力受入と成功shadowを必須にし、実DBを変更する前にGit対象外data/backupsへ完全backupを作る。今回の準備担当はrunnerを**import/実行せずAST parseのみ**、backup/copyを作っていない。

runnerはAPIを実時計で `Harness.ingest(source-only)` → `Intake.queue(company_id=jp:1975,new_only=True)` → request ID付きobserved claim → `Harness.complete(expected_attempt=1)` の1jobへ限定する。各段階を新規journalへbegin/succeededとしてfsyncする。packet/worker/generation/lease/source全snapshotを照合し、各段階は別transactionである。失敗・不明な段階はjournal/backupを調べ、成功済み又は不確実なmutatorを自動再送しない。原HTTP完了/今回準備時刻を、将来実ingestのfirstsaveへ置換しない。

## read-only baselineと将来の期待差分

実DB main SHAは `ac2c17f7a7750ac3ffa0ceafd850f2916c3c31de79faa287468aa24f313c1f89`。`mode=ro/query_only/contextlib.closing`で186sources/185classifications/106全完了jobs、103attempts/206events/103request receipts、21case heads/42versions/125reviewed sources、1975既存会社・source0、新4ID未登録を確認した。Store初期化・DB書込みは0で、読取前後main SHAは不変。

将来の期待増分はsources+4 / record_availability+4 / source_classifications+4 / jobs+1 / job_attempts+1 / job_attempt_events+2 / job_request_receipts+1だけ。190sources/189classifications/107全完了jobs、104attempts/208events/104receiptsとなる。schema、全tableの旧row、既存company、qualitative case21/42/125を保持する。runnerは全tableをmultiset比較し、旧rowの変更/削除や他table増分を拒否する。ここではこれらの将来成功を主張しない。

新GET・DB書込み・Store初期化・backup/copy作成・shadow/actual実行・production/shared file変更・金融採用・IR/注文は0。準備フォルダだけを固定し、rootレビュー待ちで停止する。
