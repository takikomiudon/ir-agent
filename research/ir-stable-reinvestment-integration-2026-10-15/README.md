# 安定期再投資とFCFFの中間計算

全1,209テスト成功（34.480秒）。[全件ログ](tests.log)、[独立確認](independent-recheck.json)、[コードSHA](source-code-sha256.json)を保存した。

Damodaran 2009年論文p17/p21の式に基づき、明示された次期税引後NOPAT・同じ安定期g・新規投資ROCから、g/ROC、再投資額、FCFFを分ける。税や成長を再適用しない。合成例のFCFF80、Exxonの著者表示入力を分解した例をFractionで独立照合した。原典の丸めや不一致は保持し、現在の企業予測へ採用していない。

負FCFF、g0の未対応範囲とROC0の分母未定義、不正入力、外部Decimal設定からの独立を確認。API/CLIの入力・DB不変も別担当が確認した。財務的妥当性・新規投資ROCの適合・正常化・存続は未検証で、status intermediate_only / adoption unresolvedを維持する。実DB変更、送信、注文はない。
