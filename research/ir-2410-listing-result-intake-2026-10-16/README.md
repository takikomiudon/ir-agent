2410の10月15日審査結果・監理指定解除告知 **1sourceだけを投入するfile-only準備** です。[親受入済みbundle](../ir-case-studies-2026-10-15/2410/listing-review-current-entry-followup-2026-10-16/source-bundle.json)の `/sources/0` 全objectをそのまま抽出し、新bundleはcompanies/theses空。既存2410会社snapshotと旧原2sourceは再ingest・再分類しません。

分類は `other` / `financial_content:true` / expected_version0。制度・株式手続資料という区分は旧10月1日告知と同じですが、今回は9月30日時点の流通株数・時価総額・比率と維持基準の数値表があるため金融内容ありとします。旧告知の数値なしfalseは変更しません。原文basisはp1の当期末表示行と基準行の連続substringで、文字/UTF8 byte位置、元quote/file SHA、native source SHAを固定しました。既存Intake.completeが保存するinputs_verified:falseを維持し、厳密6field requestへ新fieldを加えていません。

会社の10月15日公表は、9月30日期末基準適合、10月15日の解除通知受領、10月16日の解除効力、Standard申請取下げ/Prime継続の意思決定を区別して記録します。旧10月1日時点の結果未確認は会社公表scopeで解消しますが、独立した取引所現状・申請取下完了・将来上場や売買の保証へ拡張しません。表の102.41億円等を現在の1株価格へ逆算したり、利益/評価/投資閾値へ移したりしません。公表日10月15日の日精度・published_at:null、原HTTP完了06:54:28.233394UTCは原objectのまま、actual firstsaveは未設定です。

入力pinは新producer manifest列挙＋manifest/親受入の25filesのみ。旧原2sourceはこの準備bundleに含めません。normalizer、新numeric facts、金融モデル・価格・質問・送信は0です。

baselineはroot指定main SHA `524fdcfffdf0bdeacb6f4b9e3358e4ed71a0ab56f1d2111b9f82e57ec08052a0`、207sources206分類115全完了jobs、112attempt224event112receipt、25case47版144既読、2410既存source2です。`baseline-reference.json`はroot受入済み2341native登録receiptへの参照であり、今回実DBの接続・file読取はありません。実行時にrunnerが既存company/資料2件、新ID未登録とbaselineを改めてRO検査します。

`run_once.py`は受入済みsingle-source patternから会社/baseline/件数/worker/要求ID/backup名だけを変更。差分を保存しAST parseのみでimport/実行はしていません。copy-first、全27table旧row/schema/case保持、source-only ingest1→new_only intake1job→要求ID付きobserved claim→complete(expected_attempt1)、実UTCとfsyncする段階journalを維持します。全pipelineは単一transactionではないため、失敗/不明時はjournal/backupを点検し、成功済み/不確実mutatorを再送しません。

現44codeは1558テスト受入のmanifest SHA `9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60` と同bytes・全SHA一致です。rootが新 `parent-input-acceptance.json` を保存してから、rootのみshadowを一度実行します。

```bash
.venv/bin/python research/ir-2410-listing-result-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2410-listing-result-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60
```

同じdata/runner/codeの成功shadowをrootが受け入れた後、stageをactualへ変えてrootのみ一度実行します。actualは親入力受入、成功shadow/pins一致、main SHA、新stage journal/backupを要求します。

期待する将来増分はsource/availability/classification/job/attempt/requestreceipt各+1、event+2のみ。208source207分類116全完了jobs、113attempt226event113receipt、2410資料2→3、case25/47/144と全旧row/schema/企業/金融record不変を検証すべきで、今回の成功ではありません。

実DB接続/file読取/書込・Store初期化・backup/copy・runner/shadow/actual・GET・normalizer・旧producer/共有docs/production変更・金融採用・外部行為0。13準備filesをfreezeし、rootレビュー待ちで停止します。
