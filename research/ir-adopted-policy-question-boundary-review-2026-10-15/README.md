# 採用policyと新legacy質問の境界：新しい不具合は未確認

**今回の一点ではP2等の新規所見0。** `decision_contract`なしの新質問でも、既知のlegacy経路で保存済みvaluation branchを適用できる。ただし判断は `action: unresolved / decision_status: missing_decision_contract` のまま。workflowはこのモデル更新を明記し、既存testも同じ動作を期待している。後続 `decision-review` はcontractなしを拒否する。

policyのglobal ID/version登録、会社別採用参照、各questionでの明示freezeを分けて確認した。coverageは `company.decision_policy_ref` 又は同社の保存済みcontractを採用参照として数えるので、「会社参照が存在しない」とはしていない。一方このread-only棚卸しを、将来の全質問へpolicyを自動継承/強制する契約とは読まない。workflowもregistryだけで全社自動採用とはしない。

SKILLの現運用は、実案件で `policy add` とquestionのpolicy ID/version・価格根拠の明示を要求する。手順を省略した入力をAPIへ渡せることは、その省略が現運用に適合するという意味ではない。ただし今回のdocs/codeには、会社参照又は過去の同社contractがあれば新legacy質問を必ず拒否すると約束した条件は確認できず、既知互換仕様だけをbug扱いしない。legacy更新がpolicy適合済みと認定されるという主張もない。

質問前の方針記録・freezeは、保存Anthropic原典の仮説/評価/退出記録をIRへ適応したプロジェクト契約。原著の数値売買規則又は会社別自動gateとは混同しない。[review.json](review.json)に12旧ファイルのSHA、13逐語anchorと位置、静的経路、未検証範囲を保存した。

新たな文書約束との不一致が確認された場合だけ再現するという依頼条件を満たさないため、memory/temp再現0。新GET/実DB/code/tests/旧ファイル変更/fullsuite0。追加gate・仕様変更・金融条件を提案せず、この既知境界の記録で終了する。
