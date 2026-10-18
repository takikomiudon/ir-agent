2410の **受入済み派生12fact＋公開Q&A原典1件だけ** を、2source／1intake jobで保存・分類するfile-only準備です。新bundleはcompanies/theses空、sourceは各 `/sources/1`（派生）と `/sources/0`（Q&A）の全objectを変更せず抽出しています。既存原3sourceの再ingest・再分類、normalizer／reproducerの再実行は0です。

| 新source | 分類 | 逐語basis |
|---|---|---|
| 非連結短信の派生12fact | other / financial_content:true | 派生content内のraw_period_label・raw_unit_label・raw_valueの連続JSON |
| 会社が編集した公開Q&A要旨 | qa / financial_content:true | p1の普通配当性向50%以上の会社方針と次期額非開示等の回答部分 |

双方expected_version0・厳密6field request。inputs_verifiedはrequestへ足さず、既存Intake.completeが保存するfalseを維持します。原contentのUnicode/UTF8位置・native source SHA・元引用参照を `classification-evidence.json` に固定しました。Q&Aの質問側の160円等を会社回答の確約にしないよう、basisは回答本文だけです。

派生sourceは非連結net_incomeのままで、親会社帰属利益へ変換しません。千円Q3実績・基本EPS、当時FY会社予想と中間0.00／年間160.00（普通140＋特別20）の区分、日付nullや全scopeをそのまま保持。年度終了後の現在予想/実績や永続配当、現株数からの再構築にしません。

Q&Aは7月31日の会議で、加筆修正された公開要旨です。個別publication_date／published_atはnull、会議日時やPDF技術metadataの8月3日を公表時刻に移しません。普通配当方針・次期費用/利益意向・会社株価目標等の金融説明があることと、将来予測/適正価格/売買条件への採用は別です。質問側の現預金/配当総額や過年度辞退率を回答による認証/将来確率へしません。古い会議の上場発言で、後続10月15日に会社が公表した審査結果を未確認へ戻しません。

入力pinは凍結した派生producer/Q&A manifest列挙＋manifest/親受入、既存原bundle/実受入の37filesだけです。新source全metadata/ID/content/処理・HTTP時刻を保持し、actual firstsaveを先付けしません。既存原短信は実行時に受入normalized bundleのsource[0]と実DB全object一致をguardし、再投入しません。

baselineはroot指定main SHA `412e8cb69f2fdc2bf1efa6f812603e70062a67cea2a501423dba2edadb3d13b5`、208source207分類116全完了jobs、113attempt226event113receipt、25case47版144既読、2410既存資料3です。`baseline-reference.json`は直前のroot受入receiptへの参照で、この準備では実DBの接続・file読取は0です。

`run_once.py`は成功済み2source patternからbaseline/counts/worker/要求ID/backup名と原source全object guardだけを変更し、差分を保存・AST parseのみ実施しました。copy-firstで全27旧tableの旧row/schema/caseを保持し、source-only ingest2→new_only intake1job/2source→要求ID付きobserved claim→complete(expected_attempt1)を行う設計です。各API直前の実UTC、fsyncするbegin/succeeded journalを維持。全pipelineは単一transactionではなく、失敗/不明時はjournal/backupを点検し、成功済み/不確実mutatorを再送しません。

現44codeは1558テスト受入のmanifest SHA `9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60` と同bytes・全SHA一致です。rootが新 `parent-input-acceptance.json` を保存してからrootのみshadowを一度実行します。

```bash
.venv/bin/python research/ir-2410-facts-with-qa-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2410-facts-with-qa-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60
```

同じdata/runner/codeの成功shadowをrootが受け入れた後にstageをactualへ変え、rootのみ一度実行します。actualは親入力受入、成功shadow/pins一致、main SHA、新stage journal/backupを要求します。

将来期待増分はsource/availability/classification各+2、job/attempt/requestreceipt各+1、event+2のみ。210source209分類117全完了jobs、114attempt228event114receipt、2410資料3→5、case25/47/144と全旧row/schema/企業・金融record不変を検証すべきで、今回の実行成功ではありません。

実DB接続/読取/書込・Store初期化・backup/copy・runner/shadow/actual・GET・normalizer・旧producer/共有docs/production変更・金融採用・IR/注文0。13準備filesをfreezeしrootレビュー待ちで停止します。
