# 明示zero growthの純算術境界：変更前read-only確認

**正の明示NOPAT_next・正の明示ROC_newに対する明示g=0は、既存式の純算術の定義域拡張として切り分けられる。経済適合や著者の新しい売買ルールの採用ではない。** この確認ではsrc/tests/docを変更せず、計算やテストも実行していない。rootの別full suiteが進行中のため、実装変更はその完了通知まで行わない。新規作成はこのREADMEだけ。ネット・実DB操作は0。

## 現状と著者根拠

現コードはROC_new=0をundefined denominatorとして先に拒否し、非正NOPAT/負ROC/負成長も範囲外とする。g=0だけは「nonzero ROCなら数学的に定義されるが初版の正の著者例scopeで未対応」と明示している。docsと既存testもこの差を保持している。これは当初projectの機能範囲で、原著がg=0を数式エラーと指定した規則ではない。

著者はAswath Damodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies*（2009年9月）。原PDFと抽出textは[既存sources.json](../valuation-model-routing-2026-10-15/sources.json)のsource_id `damodaran.cyclical-commodity.2009` に保存されている。原PDF SHAは `16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40`。今回意味確認したのはPDF p17/p21のみ。p17の“Stable period reinvestment rate”のg/ROC式と、p21の次の新規投資ROCの説明を確認した。

> New investments are expected to generate a return on capital that reflects
> the normalized operating income and current capital invested; this return on capital is
> used to compute a reinvestment rate.

両頁の具体例は正成長のToyota/Exxonであり、今回の確認範囲にはzero growth時の維持投資や資本維持の適用説明はない。この不明を経済的適用可能・不可能のいずれにも変換しない。正成長例の数値を現在企業の既定値にも使わない。

## 切り分けられる変更と維持する境界

同じbasis/年次期間についてNOPAT_next>0、ROC_new>0、**callerが明示したg=0**なら、既存式 `r=g/ROC_new`、`R=NOPAT_next×r`、`FCFF=NOPAT_next−R` は代数的にr=0、R=0、FCFF=明示NOPAT_nextとなる。これは式からの条件付き分解であり、当該企業の予測や再投資額を採用した結果ではない。

この範囲を受け入れる場合も、欠損/null/空/未指定を0へ置換せず、strict decimal文字列・原入力・出典申告・同一basis/期間を保持する。ROC0の分母未定義を先に返す順序、負g・非正NOPAT・負ROCの範囲外、税/NOLや(1+g)の再適用禁止は維持できる。追加の負成長・損失企業・ROC推定モデルへ広げる必要はない。

結果は引き続き `intermediate_only / adoption:unresolved`、source/意味/安定期/新規投資ROC/資金調達等のverificationはunverified。原典がzeroケースの経済適合を明示したとは表示しない。**式で求めるR=0をgross capex=0、維持投資/維持費=0、資産劣化なし、分配可能額確定と読み替えない。** 設備投資・D&A・運転資本からnet reinvestmentを再構成する機能でも、DCF・終価・価格・売買を許可する機能でもない。

実装する場合の有限検証は、明示0で上記代数結果を保持すること、欠損が引き続き拒否されること、ROC0/負成長/非正NOPATが従来どおり区別されること、未検証/adoption flagsとCLIの純計算境界を維持することに限る。まだ変更・検証していない。

## 点検した保存版

- `src/ir_agent/stable_reinvestment.py` — SHA-256 `8e95ffbb61155f7a42ff1b2d00f27071daa431cb7c37841d32e79372216a93a9`
- `docs/cyclical-reinvestment-spec.md` — SHA-256 `6d10c16d0d020ad6afd6e3ed63ddba24ba6b81499b6f71b163cde05432bd31b7`
- `tests/test_stable_reinvestment.py` — SHA-256 `7e324059ac58bec8e08d2a26e9fe1f2e7fa05132e467d8f5fb9c12327090779c`
- `research/valuation-model-routing-2026-10-15/sources.json` — SHA-256 `a9b8c046d3ff5b23eb65fdaabdd4ee8ef55c66498b52cbcad9fc5099c3cc7538`

記録時刻：2026-10-15T21:20:46.548764+00:00。全著作についてzero説明が存在しないという結論ではなく、指定した保存p17/p21と現行契約の有限確認である。
