2341アルバイトタイムスの初回PDF1sourceを保存・分類する **file-only準備** です。[初回受入済みbundle](../ir-case-studies-2026-10-15/2341/initial-public-review-2026-10-16/source-bundle.json)を全bytesそのまま複製し、companies/theses空・原source1件だけです。派生facts、別途のCF/株式/利益/segment/modelscope追補は含めず、準備pinにも加えていません。

分類票は既存Intakeの `financial_statement` / `financial_content:true` / expected_version0。p1の中間連結業績見出しを逐語basis_quoteとし、原source native SHA/content SHA・文字/UTF8 byte位置・元の受入済み頁引用へ固定しました。厳密な6field分類requestにinputs_verifiedを足さず、既存Intake.completeが保存するinputs_verified:falseと、金融入力の検証・採用0を区別して記録します。

公表日2026-10-08・正確時計null、実績2026-03-01〜08-31と会社通期予想2026-03-01〜2027-02-28、初回意味/画像1/2/4/6頁・全15頁を保持します。表紙の直近修正無とp6の4月9日予想対10月7日修正は異なる比較点で、特別益を営業/正常利益へ移しません。sourceのID/本文/全metadata/raw/HTTP時刻は不変です。root受入済み原文が根拠で、今回新しい意味頁は読んでいません。

`input-pins.json`は初回manifestの27files＋manifest/親受入の29filesのみ。`prepared-code-pins.json`は現src44filesで、1558テスト受入の9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60と全bytes一致します。将来codeが変わった場合はこれを上書きせず、rootが別の受入manifestを明示します。

baselineはroot指定main SHA bfa74dd03c96940843b73a1039fabe50d1f26521ff598407d3bdcefd00834c04、203sources/202分類/112全完了jobs、109attempt218event109receipt、24case46版142既読です。`baseline-reference.json`は受入済みRO成果と親受入への参照で、**この準備では実DBへの接続・file読取・Store初期化・backup/copyを行っていません**。2341のsource0/既存companyと新ID未登録を含む実行時のbaseline guardはroot runnerが改めて検査します。

`run_once.py`は受入済み2315年次1source経路から会社/baseline/既存資料数/worker/要求ID/backup名/期待件数だけを限定adaptしました。API順序はsource-only ingest→new_only intake1job→要求ID付きobserved claim→complete(expected_attempt1)。原子性は各APIの範囲で、全pipelineが単一transactionではありません。段階journalはbegin/succeededをfsyncし、失敗・不明時は成功済みmutatorを再送せず、journal/backupで停止位置を確認します。`adapted-runner.diff`を保存しAST parseだけを実施、import/実行は0です。

rootが入力と44codeを受け入れて `parent-input-acceptance.json` を別途作成し、rootのみがshadowを一度実行します。実行後のparent-acceptanceとは別名で保存してください。

```bash
.venv/bin/python research/ir-2341-initial-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2341-initial-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60
```

同じrunner/data/codeの成功shadowと全旧row/schema/case保持をrootが確認後、stageをactualへ変えてrootのみが一度実行します。actualは入力受入・成功shadow/pins一致・main SHA一致・新stage journal・新backupを要求し、data/backupsへ実行前backupを保存します。渡すnowは各API直前の実UTCで、原HTTP/準備時刻をactual firstsaveへ置換しません。

期待増分はsource/availability/classification/job/attempt/requestreceipt各+1、event+2だけ。将来204sources/203分類/113全完了jobs、110attempt220event110receipt、2341資料0→1、case24/46/142・全旧rowとschemaは不変であるべきです。これは検証すべき将来値で、今回の実行成功ではありません。

GET・実DB接続/書込・Store/backup・runner/shadow/actual実行・旧producer/共有docs/production変更・金融採用・IR送信/注文0。追加読解の完了を待って依存へ取り込む作業はせず、ここでfreezeしてrootレビューを待ちます。
