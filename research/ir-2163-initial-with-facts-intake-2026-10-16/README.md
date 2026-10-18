# 2163：5資料の初期分類投入準備

本成果は**準備のみ**。親受入済み原文4件（IRroot、連結中間短信、常設IR FAQ、補足説明資料）と、既存短信の10数値派生1件をsource-only bundleへまとめた。正規化bundleに含まれる原短信は重複投入しない。会社・thesisは空配列。金融入力採用・予測や株価の更新・IR登録/送信は0。

| sourceの役割 | 分類 / financial_content | 維持する範囲 |
| --- | --- | --- |
| 会社IRroot | index_only / false | 一覧入口。既存指標表示とリンク先本文の読了/最新性を区別 |
| 2027年1月期中間日本基準連結短信 | financial_statement / true | 実績P/L千円と表紙/当時会社通期予想百万円、初年度連結による前年連結比較なし |
| 常設IR FAQ | qa / true | 会議Q&Aではない。稼働率の分母、未配属労務費の販管費/原価、季節性・引当/現金・法定マージン差の会社説明 |
| 同中間短信の補足説明資料 | earnings_presentation / true | 単体平均と期末人員/稼働率/単価/工数、連結結果と単体指標、DPSの分割前後基準と年間dash |
| 原短信の直接10表示の構造化 | other / true | 同じ原開示の派生資料で、新開示・独立予測ではない。数値の意味/金融妥当性は未認証 |

原sourceは受入済みJSON object全fieldと一致し、ID・content・HTTP完了時刻・published_at:null・元metadataを保持する。原文意味の受入は短信9頁中の物理1/2/4/6、補足22頁中の11/12/16と常設FAQの選定5範囲であり、既存親receiptを再利用した。今回は全原PDFの新精読ではない。

`classification-evidence.json`は5逐語引用をexact source.contentへUnicode文字offset・UTF8 byte offsetで固定する。native SHAは `sha256(models.json_text(source).encode('utf-8'))` で、compact JSON SHAと区別。`source-map.json`は原raw SHA/bytes・snapshot SHA・保存抽出本文との一致も保持する。派生sourceの10factsは純粋reproducerで再現し、原短信snapshot一致を確認。新numeric fact生成は0。

会社表示のEPS38.43/58.85は株式分割の影響を既に遡及反映済みとして保持し、再分割しない。千円実績の精度を百万円表紙へ落とさず、百万円会社予想から千円精度を補わない。中間DPS43と期末予想21.50は分割基準が混在し、年間DPSを合算しない。配当支払予定を実施済みにせず、会社の配当性向方針を投資家売買閾値にしない。常設FAQの労務費区分変更は費用の消失を意味しない。単体平均指標を期末値や連結売上へ掛け戻さない。

## 固定入力と実行前の受入

`input-pins.json`は、受入済みinitial/public-explanationのproducer manifest列挙filesと、disclosed-facts manifestの明示outputs、そのmanifest/parent acceptanceだけをpinする。別担当の未受入statement-note/index/native case/監視・current docs等は広く含めていない。`prepared-code-pins.json`の現行src44 Python filesは最新1558tests受入時のfixed-code pinsと完全一致。prepared=currentだが、実行時に再照合する。

方法は受入済み [1975の準備](../ir-1975-initial-with-facts-intake-2026-10-16/README.md) とrunnerを再利用した。`adapted-runner.diff`の変更はcompany、5source数、基準DB hash/件数・case件数、作業ID/backup名、期待完了件数だけ。API・journal・copy→actual・全旧row保持ガードを変えていない。

rootは入力/runnerを読み、新規 `parent-input-acceptance.json` を保存する。後の実行受入 `parent-acceptance.json` とは別名で保持する。以下はrootだけが実行する将来コマンドであり、本準備では未実行。CODE_SHAは受入済み44file manifestの実SHAへ置換する。コードが変われば旧preparedを上書きせず、受入済み新manifestを渡す。

```bash
.venv/bin/python research/ir-2163-initial-with-facts-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2163-initial-with-facts-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 CODE_SHA
```

shadowで全table比較が成功し、同一runner/data/execution-code SHAを受入後にrootだけがstageをactualへ変え1回実行する。actualはparent入力受入と成功shadowを必須にし、DB変更前にGit対象外data/backupsへ完全backupを作る。準備担当はrunnerをimport/実行せずAST parseのみ、backup/copyも作っていない。

runnerはAPIを実時計で `Harness.ingest(source-only)` → `Intake.queue(company_id=jp:2163,new_only=True)` → request ID付きobserved claim → `Harness.complete(expected_attempt=1)` の1jobに限定する。段階別の新規journalへbegin/succeededをfsyncする。packet/source全snapshot・worker/generation/leaseを点検し、全pipelineは単一transactionではない。失敗/不明段階はjournal/backupを確認し、成功済み又は不確実なmutatorを自動再送しない。原HTTP完了/準備時刻を将来の実ingest firstsaveに置換しない。

## read-only baselineと将来の期待差分

実DB main SHAは `28185d10772c7e29c57bfb93b967c5e4d94739f6d6b8fd66ce86faa2365dbb64`。`mode=ro/query_only/contextlib.closing`で190sources/189classifications/107全完了jobs、104attempts/208events/104request receipts、22case heads/43versions/129reviewed sources、2163既存会社/source0と新5ID未登録を確認した。Store初期化・DB書込みは0で読取前後main SHA不変。

将来の期待増分はsources+5 / record_availability+5 / source_classifications+5 / jobs+1 / job_attempts+1 / job_attempt_events+2 / job_request_receipts+1だけ。195sources/194classifications/108全完了jobs、105attempts/210events/105receiptsとなる。schema、全table旧row、既存company、case22/43/129を保持する。runnerは全tableをmultiset比較し、旧row変更/削除や他table増分を拒否する。これらの将来成功を今回実施済みとは主張しない。

新GET・DB書込み・Store初期化・backup/copy・runner実行・production/shared file変更・金融採用・IR/注文は0。準備フォルダだけを固定し、rootレビュー待ちで停止する。
