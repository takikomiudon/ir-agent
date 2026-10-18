# 非営業資産・少数持分を分けるDCFの統合確認

`dcf_explicit_terminal_equity_bridge`を別methodとして追加した。DamodaranのToyota例に沿い、営業資産価値へ現金・非営業資産を加え、負債・少数持分を控除する。[原典35引用と9入力](../ir-toyota-author-valuation-readiness-2026-10-15/readiness.json)、[独立原典レビュー](../ir-toyota-author-valuation-readiness-2026-10-15/independent-review.json)、[仕様](../../docs/explicit-equity-bridge-spec.md)を参照する。

全**1,281テスト成功、34.985秒**。[全件ログ](tests.log)には旧1,253件と追加28件を含む。新単体20件は9必須入力、符号・時点、独立Fraction、Decimal隔離、旧契約・出力互換を点検する。新統合8件は出典監査、事前に許可したIR入力変更、無許可変更の保留、旧baselineへの後付け拒否、CLIを点検する。全件成功は金融前提・投資成績の検証を意味しない。

[親の独立計算](independent-recheck.json)は、9入力が保存済み原典候補と完全一致すること、FractionによるPV・終価・調整・1株価値と表示丸めを確認した。[再現スクリプト](independent-recheck.py)は相対repo rootで起動できるが、実DB確認部はこの研究台帳が必要。

| 例 | 計算結果と留保 |
|---|---|
| 合成例 | 92.82円。非営業資産20百万円と少数持分10百万円を別表示し、旧explicit例より1株1円増加。価格100円を含め仮想。 |
| Toyotaの著者表示入力 | 3,944.09円。2009年の著者表示3,943円とは終価段階から差があり、未表示入力を逆算しない。比較3,060円も当時の価格。 |

両例とも`unweighted`で確率・期待値を補わない。`enterprise_value_jpy`は非営業資産加算前の営業資産価値。簿価/時価・持分範囲・重複やその他請求権の適合は別レビューである。旧`dcf`・厳格7入力`dcf_explicit_terminal`・保存済み質問は再解釈しない。

[架空の返信適用フロー](demo-workflow.py)と[実行記録](synthetic-workflow-result.json)では、質問前に許可した基本シナリオの非営業資産だけが10→20へ変わり、少数持分10とその他の入力、仮説v1・質問原文・返信原文は不変だった。仮説v2と、その版・固定policy・新しい架空価格を参照する`exit_review`を保存した。理由は架空価格の目標到達であり、肯定的返信だけの購入ではない。費用・閾値・価格を含め全て合成例で、メモリ内の架空送信記録は外部送信を行っていない。

親のread-only確認では実DBは1,819社、64資料、分類63件、theses/questions/replies各0。確認前後のDB SHAは同一。GET・DB書込・実IR送信・注文・現企業予測の採用は0。これ以前の[1,253件チェックポイント](../ir-explicit-terminal-integration-2026-10-15/README.md)はそのまま残す。
