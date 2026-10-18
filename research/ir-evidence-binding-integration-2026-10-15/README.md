# 保存予測と観測の原文照合

全1,129テスト成功（35.447秒）。既存のGneiting–Raftery原典と[根拠点検契約](../../docs/prediction-evidence-binding.md)に従い、採点前の機械的な参照照合を接続した。source-bindingのDB/APIは本プロジェクトへの適応であり、原典がstateの正しさやIRの収益性を保証するものではない。

元question/reply、明示したsourceのSHA/引用/全親、保存来歴、使用時点/as-of/現在の公開性を読み取る。母集団と予測なし・未確認・保留を保持し、`source_binding_report_only`を返す。selected_state/score_request/scoreはnull、state独立性・signalの意味・訓練・校正はunknown。

[設計](design.md)、[全件ログ](tests.log)、[対象18件ログ](target-tests.log)、[コードSHA](source-code-sha256.json)、[独立再確認](independent-recheck.json)、[要約](summary.json)を保存。別担当は第二原典のfuture/held/synthetic、共有DAGと循環、legacy known-by、後日の保留、本文不一致、DB不変とscorer未呼出を再確認した。

[実台帳へのread-only実行](actual-report.json)は観測/予測0件。[DB byte SHA](actual-read-only-check.json)も不変だった。架空の予測や実state、実採点は追加していない。実案件の原文入り出力は私的本文を含み得るため、Git対象外のdata/へ保存する。
