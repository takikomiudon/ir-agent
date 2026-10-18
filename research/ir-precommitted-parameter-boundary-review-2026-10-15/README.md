# 質問前に固定した変更可能入力：限定静的レビュー

2026-10-15。docs/workflow.mdの実キーを先に確認し、実装4file＋関連test1fileだけを静的確認した。コード・DB・GET・テスト実行・元file/共有file変更・新機能・金融値採用は0。必要修正と認定するバグは今回の範囲で発見しなかった。実行検証済みという意味ではない。

**固定decision_contract付き経路は、保存済み分岐の財務入力差分をparameter_pathsと照合し、許可外の倍率・確率・他scenario入力を止める。旧contractなしAPIは、質問前に固定された完全valuationを適用する互換経路であり、同じallowlist保証を持たない。** いずれも返信の経済的意味が分岐を支持するかは人のレビューが必要。

## 実際に到達する経路と保証

| 段階 | 実契約・止まる境界 | 根拠 |
|---|---|---|
| 質問の構造検証 | target_parameterは必須の文章。parameter_pathsと同義ではなく、文章を金融pathへ自動変換しない。分岐は2以上、重複id禁止、unresolved枝必須。その枝にvaluationは置けない。明確枝のvaluationは計算可能な**完全モデル**として検証する。 | W:64–66,197–201; M:179–212 |
| 質問保存 | 現在thesis版・会社・時点・根拠を確認。serverのthesis全体をsnapshot化し、既存IDへのbranch/質問変更は拒否。decision_contractがあるときだけfreeze→planへ進む。 | H:391–431 |
| 契約の固定 | 登録済みpolicyのid/版・snapshot/SHA・実登録時刻、position、事前planを凍結。planは回答前の条件付き比較で、返信を適用した意味ではない。設定不足等のdraft保存はできる。 | L:183–245; W:226–234 |
| planの許可path | 元thesisのcanonical financial inputsに**実在するpath**だけを許す。各分岐の完全valuationを元モデルと比較し、差分が許可list外ならunmapped_parameter_change、全体needs_review。scenario名のドットを拒否し、余分なmetadataやドット付きJSON keyで実入力を隠さない構成。 | D:345–366,376–427 |
| 送信済み記録 | 契約付きはpolicy固定照合、sent_atのposition・鮮度等と現在の依存情報holdを点検し、decision_distinguishing以外は拒否。未来sent_atと進んだthesisも拒否。これは実外部送信を行うAPIではない。 | H:433–451; L:247–269; W:232 |
| 返信適用直前 | callerが渡すのは保存済みbranch_id。保存questionから分岐を引き、現thesis版・質問時版・expected版が同一でなければ拒否。契約付きはvalidate_branchで**再び全canonical差分⊆parameter_paths**を検査し、違反はValueError。preflightでの保留だけに依存しない。 | H:497–530; L:271–282 |
| 適用するモデル | evaluation requestの新valuationや倍率・確率を採用しない。元thesisをコピーし、明確な保存branchにvaluationがある場合だけ**保存branchのvaluation丸ごと**を採用。なければvaluationは保持。evidenceと版・記録日時・次回管理日等を更新する。 | H:563–592 |
| 判断は別点検 | 固定policy、評価時点の明示position、供給quote、sourceを使って別の判断履歴を保存。価格不足ならモデル適用済みでもactionはunresolvedになり得る。quote矛盾等のエラーは外側transactionから伝播する。branch.actionを新規の価格点検済み判断として返さない。 | H:504,585–598; L:284–322; W:156,234 |

canonical比較はscenario名ごとのprobability・method・inputsを対象とし、Decimal上で同値の数値表記は同じ値とする。[D:345–373] baseのEPSだけを許した質問でbaseのPE、別scenarioのEPS、確率まで変えるとそれぞれ別pathの差分になる。pathはprefix wildcardではない。完全valuationを渡せること自体は、全入力の変更許可を意味しない。反対に、複数scenarioや確率のpathを**質問前に明示して固定した場合**は、その許可内の差分を機械的に禁止する契約ではない。どのpathを許すのが適切かは質問設計のレビュー対象である。

## 旧APIとの互換境界

decision_contractなしの旧質問でもvalidate_question、質問・枝の不変保存、公開性・版等の適用gateは通る。しかしH:529–530のvalidate_branchは呼ばれない。旧経路はtarget_parameterが「費用の一時性」でも、事前branchの完全valuationに含まれる複数の倍率・確率等の差分を適用できる。parameter_pathsを補足fieldとして付けただけでも、この旧経路でallowlistが自動作動するわけではない。[M:179–212; H:391–431,529–530,580–590]

これは**返信後に新branchへ差し替えられる**という穴ではない。保存済みbranchの事前指定範囲が広い互換動作である。旧適用の判断はmissing_decision_contract / action unresolvedで、過去branch-only表示もlegacy_branch_onlyとして再区分する。[H:28–35,585–594; W:156] 「全質問がtarget_parameterだけしか変えられない」と呼ぶのは現契約を超える。今回コードを緩める/拡張する提案はしない。

## 既存契約への誘導文案（docsは未編集）

> target_parameterは質問の説明ラベルで、機械的な変更許可listではない。新運用では固定decision_contractとparameter_pathsを付け、変更を許す実入力pathを質問前に明示する。返信後は保存済み分岐だけを適用し、原文の意味がその分岐と数値変更を支持するかは別途レビューする。

旧APIのbranchモデル適用を、価格点検済みactionの成立と混同しない。この誘導は既存guardの緩和や旧互換の変更を提案するものではない。

## 公開性・曖昧さ・現在基準の区別

- rawreplyのinformation_status既定値はunclear。評価時の明示分類を受け付けるが、最新の非public訂正があればそれを優先する。public_clarification以外はheld_for_reviewで新thesisを作らない。これは初期unclearから人が公開補足と再分類する通常経路も許す。[M:215–224; H:531–558]
- publicでもaction unresolvedの枝はunresolvedのままでモデルを変えない。独立に、既存thesisの全依存原典の情報訂正をtrusted current_timeで確認し、raw sourceの公開性holdも、source/model書込みより前に止める。[H:542–562; L:30–75]
- 契約付きのbranch入力違反は分類分岐より先にエラーとなる。したがって不正枝を「unclearなので単に保留」として適用可能な状態に扱わない。[H:529–530,556–562]
- 公開性訂正は過去の原文・モデル・判断JSONを自動で巻き戻す仕組みではない。返却はcurrent_evaluation_view(..., now=current_time)を呼び、現在の有効性を過去結果と分ける。[H:508–510,597–598; W:273–284,480] 今回はinformation_review.pyを追加の監査対象にせず、そのhelper全内部の正しさ・全guardを再認定していない。

## 人の意味レビューが残る所

basis_quoteは保存返信内の逐語部分文字列でなければ拒否するが、branch.conditionやinterpretationとの意味的一致を自然言語から証明するコードではない。[H:519–525] 「費用は一時的」という発言が対象期のEPS増加をどれだけ支持するか、公正倍率や確率を同時に動かしてよいか、会社予想と投資家仮定の区別、そもそも事前枝の数値が妥当かは、引用・理由と事前モデルを照合する担当者の責任。public_clarificationラベルも経済的因果や返信の正確性を証明しない。

このハーネスは、**人が適切に設計した変更範囲を保存し、適用時に形式上の逸脱を検出する**用途では足りる。誤った枝選択や、事前から過剰に広い許可listを置いたことまで意味的に是正するものではない。未想定の数値や曖昧な回答を受けたら、都合のよいvaluationを返信評価へ追加するのでなくunresolvedとして再研究する必要がある。

## 関連testの静的確認

読んだtestはtests/test_decision_lifecycle.pyの1fileだけ。実行していない。

| 範囲 | 既存testが記述している確認 |
|---|---|
| 73–82 | 質問/quoteの再送不変と、後続policy版が固定版を置き換えないこと |
| 93–125 | 送信時の価格・position点検、返信適用後の価格不足hold、固定policyと新quoteによる判断 |
| 127–139 | 無効sourceで全適用をrollback、非許可PE変更を含むdraftの送信をneeds_reviewで拒否 |
| 234–247 | 古い版/未来reviewの拒否、旧branch-only表示の区分 |

このtest fileは許可外確率・全method・全scenarioの網羅testではない。その保護の見解はD/Lの同じ差分比較経路の静的読取に基づく。Storeの低水準書換えや直接SQL改変、全valuation method実装、current表示helperの再監査は対象外。今回の範囲では最小修正・再現実行を要する新findingはない。

## ファイル固定（読取時全byte SHA-256）

本文のM/H/L/D/Wは下表のファイル、数字は1起算行。原ファイルは変更していない。

| ID | ファイル | SHA-256 |
|---|---|---|
| M | [src/ir_agent/models.py](../../src/ir_agent/models.py) | `8bf7fa62b925f80bfc7535759e7a7756c3c6816e3a0978f7049beedee6f1c01c` |
| H | [src/ir_agent/harness.py](../../src/ir_agent/harness.py) | `a1adc6dd29df103497498b159cacd555dc230d48f873051429ae55e979e6fae8` |
| L | [src/ir_agent/decision_lifecycle.py](../../src/ir_agent/decision_lifecycle.py) | `2fc7753f8c09a0c055a7340ffc8d53954e6f175c144231c1f306aa62cc110731` |
| D | [src/ir_agent/decision.py](../../src/ir_agent/decision.py) | `a37bbc586c0aa7c00a924ecc54db7e7132417fa89e350915b9fe2215646b064b` |
| T | [tests/test_decision_lifecycle.py](../../tests/test_decision_lifecycle.py) | `70400c7a6e90dab2dc229798b8916d21a93762f9cb9087e3c9402630df3fbd99` |
| W | [docs/workflow.md](../../docs/workflow.md) | `f56971d477d421a70f5d58b140c5f1a37310119c772ee12b170054f08aa10655` |
