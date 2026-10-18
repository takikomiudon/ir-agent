# 明示ゼロ成長の純算術拡張

正の明示NOPAT_next・正の明示ROC_newと、明示finite decimal文字列のg=0を受け付けた。計算は既存の `r=g/ROC_new`、`R_next=NOPAT_next×r`、`FCFF_next=NOPAT_next−R_next` のままで、ゼロの場合はr=R_next=0、FCFF_next=明示NOPAT_nextを返す。これは純代数の定義域拡張である。

欠損・null・空・JSON numberの0を文字列ゼロへ補完しない。ROC0はg0の場合も分母未定義を先に返し、負成長・非正NOPAT・負ROCの境界は維持した。符号付きゼロを含む元token・source refs・説明はrequestとSHAに保持し、算術結果のゼロは文字列`"0"`として返す。

全結果は `intermediate_only / adoption:unresolved`、全verificationはunverifiedのままである。g0の結果からgross capex/維持投資/維持費0、資本維持、正常利益採用を認定しない。新forecast・IR・valuationやDBへ自動接続する変更はない。

## 著者根拠と限界

保存済みDamodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies*（2009）PDF p17/p21のg/ROCと次期税引後営業利益の価値式分子を利用する。原PDF SHA-256は `16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40`、保存text SHA-256は `bc0de814b9bac9a6923a09919084071f4342e1fbfe5f9665c678d32ce096ea5b`。原本は既存[保存sources.json](../valuation-model-routing-2026-10-15/sources.json)内の `damodaran.cyclical-commodity.2009` で、改変・再取得していない。

p17のToyotaはg=.015、ROC=.0509、p21のExxonはg=.02、表示ROC=.21の正成長例である。p21には次の説明がある。

> New investments are expected to generate a return on capital that reflects
> the normalized operating income and current capital invested; this return on capital is
> used to compute a reinvestment rate.

この有限確認範囲にはゼロ成長の維持投資・経済適合の説明はない。著者がゼロ成長の経済ルールを指定したとは述べず、式そのものから条件付きで求まる代数結果だけを受け入れた。元の[read-only報告](README.md)は実装前の履歴として保存した。

## 変更と検証

変更ファイルは専有の `src/ir_agent/stable_reinvestment.py`、`tests/test_stable_reinvestment.py`、`docs/cyclical-reinvestment-spec.md` の3件。変更前完全バイトは[before-files.json](before-files.json)と`before/`へ保存した。正入力の従来成功結果は算術・キー・診断文まで維持し、ゼロ入力時だけproject adaptationとscope limitationを差し替えた。したがって従来の正入力結果に含まれる「zero unsupported」は旧契約の互換文字列であり、現在のゼロ入力の範囲は更新した専有仕様で明記する。

Focusedテスト26件が成功した。明示ゼロの異なる表記、入力/SHA不変、欠損とゼロの区別、g0/ROC0、非正NOPAT・負ROC・負成長、長いNOPATと小さい正ROC、ambient Decimal trapからの独立性、未検証flags、既存著者例とCLIを確認した。テストの要約は[focused-tests.log](focused-tests.log)、変更前moduleとの全返値比較は[positive-replay.json](positive-replay.json)にある。Toyota/Exxon・通常正入力・r>1/負FCFF・高精度例の5件すべてで全JSON結果が一致した。

初回`uv run`は既定cacheがread-onlyのためテスト開始前に失敗した。既存`.venv/bin/python`で実行し、インストール・ネットワークは行っていない。full suiteと独立レビューはroot担当で、本報告はそれらの完了を主張しない。実DB操作・新GET・外部送信は0。変更SHA・検証記録は[implementation-receipt.json](implementation-receipt.json)、差分は[implementation.patch](implementation.patch)に保存した。
