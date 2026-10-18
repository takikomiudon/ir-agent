# J-Quants 財務summaryの日次snapshot

`sync --provider jquants-financials --date YYYY-MM-DD` は、**既存company scopeに対応するSDK財務summary row**を公開資料sourceとして保存する明示opt-inである。個別会社サイトのPDFが未取得でも使える別データ経路だが、元PDFや開示全文の取得完了ではない。通常の `jquants` 株価providerと `edinet` の挙動は変更していない。

```bash
.venv/bin/ir-agent --db PATH sync --provider jquants-financials --date YYYY-MM-DD
```

実行すると、既存DBのcompany ID一覧を明示scopeとして渡し、公式SDK2.8.0の `ClientV2.get_fin_summary_cursor(date_yyyymmdd=DATE)` を1回だけ呼ぶ。dateはSDKが定義する**開示日**で、必ずYYYY-MM-DDの実在日を指定する。scopeは空でないcanonical `jp:CODE` の集合である必要があり、不正・空scopeはSDK初期化/API呼出前にエラーとなる。scopeの所属はcallerの責任で、CLIは実際の既存company一覧を使う。会社マスター再取得や会社の追加は行わず、返却bundleの `companies` は常に空配列である。

SDKは内部で `pagination_key` を追うため、1 SDK呼出を1 HTTP要求と数えない。cursor引数は渡さず、返却cursorも保存・利用しない。premium限定のcursor差分取得、range、銘柄ごとの要求/並列取得、定期実行の設定は実装していない。任意SDKと認証設定は既存のdata extra/SDK方式を使う。この実装・offline検証では実認証呼出、契約や金融データの受領を行っていない。利用権、銘柄/期間のcoverage、現在最新の会社予想を保証しない。

## rowの保持と対象範囲

APIは次の2つで、実DBへの登録は `fetch`/`normalize` とは別のCLI ingest段階で行う。

```python
normalize_jquants_financial_summary(rows, *, company_ids, retrieved_at=None)
fetch_jquants_financial_summary(date, *, company_ids, api_key=None, client=None)
```

`rows` はSDK DataFrame又はrecord配列。既存 `records` / `canonical_json` を使い、SDKが返した型・値をJSON互換へ保存する。NaN/NaT/NA/nullはnull、空文字は空文字、ダッシュはダッシュ、存在しないfieldは不在のままとし、0で補わない。Decimalは既存helperに従い文字列化し、SDKから文字列で返る数値tokenも保持する。SDKの型変換以前のHTTP JSON数値tokenや精度を独立確認した意味ではない。

SDK2.8.0は111列を定義し、`DiscDate`, `CurPerSt`, `CurPerEn`, `CurFYSt`, `CurFYEn`, `NxtFYSt`, `NxtFYEn` を `pd.to_datetime(errors='coerce')` で変換する。SDKは返却列を定数一覧へ限定するため、SDK前段で削除・変換されたfieldは本adapterでは復元できない。インストール済み実装/型/列とlicenseを[SDK根拠](../research/ir-jquants-financial-summary-integration-2026-10-15/sdk-contract-evidence.json)へ固定した。field名だけから金額単位や会計上の意味を推定していない。

`Code` を既存普通株code helperで照合し、明示scope外と5桁末尾非0の別種証券は `skipped_security_codes` へ理由・件数付きで残す。対象rowには有効な `DiscDate` が必要で、fetchの要求日と違う場合はDB登録前にエラーで停止する。scope外rowを採用したり、会社名・status・heldを取得データから変更したりしない。

`CurPerType` / 各期の境界、実績field、`F...` / `NxF...`、非連結の `NC...` 等は同じrow中の独立fieldとして保存し、共通のforecast/連結/年次ラベルや単位を付けない。将来配当列、EPS、利益、規制資本再投資、FCFE、倍率や評価額は作らない。同じrowは取得時刻を除くstable IDで重複排除し、同じ `DiscNo` でも変更fieldがあれば別のimmutable sourceにする。

## sourceと時刻の契約

sourceは `public_disclosure` / `requires_research: true`、metadata providerは **`jquants_financials`**、datasetは **`fins/summary`**。株価用の `provider: jquants` / `dataset: equities/bars/daily` と分離し、既存quote normalizerは財務summaryを拒否する。sourceのURLは当該開示日のdataset参照であり、銘柄単位のHTTP要求を行った証拠ではない。

`published_at` はnullのままにし、`DiscDate` / `DiscTime` からtimezone付き公表時刻を創作しない。`retrieved_at` はfetchのSDK呼出が復帰した後のローカル受領時刻であり、HTTP本文完了・公表時刻・当時のDB存在を示さない。source初回DB保存時刻は既存Storeの保存来歴に従う。offline normalizerへ渡す `retrieved_at` もaware時刻が必要となる。

`meaning_review_required: true` / `financial_inputs_verified: false` を保持する。rowの保存は資料分類、金融入力の意味点検、仮説やモデル採用の代わりではない。既存のintake/定性job/金融モデル/投資判断契約を変更せず、source分類やactionを自動追加しない。

[実装・検証報告](../research/ir-jquants-financial-summary-integration-2026-10-15/README.md)に変更前bytes、SDK根拠、架空応答だけのfocused検証、未確認範囲をまとめた。
