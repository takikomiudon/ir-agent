# 規制資本FCFEの中間計算を接続

保存済みDamodaran原典p22の`FCFE = NetIncome − ReinvestmentInRegulatoryCapital`を実装した。[原文・画像・SHA](author-evidence.json)、[入力契約](../../docs/regulatory-fcfe.md)、[実装](../../src/ir_agent/regulatory_fcfe.py)、[テスト](../../tests/test_regulatory_fcfe.py)を固定する。新規GETは0。著者の例示資本比率を採用したり、必要/目標資本を補完したりしない。

`regulatory-fcfe FILE`は、明示した年次の純利益と規制資本再投資を同じ会社・通貨・単位・主体・株主範囲で差し引く。利益の会計測定と資本の規制/政策測定は別に保持する。負の結果を切り上げず、異なる年を合計・平均せず、割引・終価・株価・IR適用は行わない。既存のDecimal/JSON/source参照helperと、DBを開かないCLI経路を再利用した。

元の仕様に対応する入力契約の適応であり、年次/比較可能性・資本政策・出典の意味を機械的に認証するものではない。adoptionはunresolved、verificationはunverified。原典のFCFEをDDMの終価へ記号だけ置き換えていない。

新規12件と全1,421件が成功（unittest37.099秒）。[全件ログ](full-suite.log)・[時刻/SHA](full-suite.json)・受入を保存した。大きい値の相殺、負/0、主体・通貨・単位・期間の不一致、営業利益/資本残高の誤用、出典参照の未検証、CLIのDB副作用を点検。最初のCLI不正JSONテストは既存のexit1をexit2と誤認し、既存契約を確認して期待値を訂正した。productionのエラー契約は変更していない。

[架空CLI例](CLI-example-result.json)は15−10=5。実DB121資料のSHAは全件検証前後で不変。実会社のFCFE・金融thesis・判断・IRは作成していない。[5831の入力対応](../ir-case-studies-2026-10-15/5831/regulatory-fcfe-input-map/input-map.json)でも、会社の年間NI予想候補と未確認の将来再投資を分け、足元資本差を代入しない。独立agentによるコード点検は未完了。
