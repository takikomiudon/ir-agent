# 保存研究からの価格判断を保存する

`research-decision-review` は、既存の最新thesisと指定済み固定policy、明示position、sourceに結合したquoteから計算した点検候補を、返信を必須とせず不変保存する。公開情報だけのbaselineはこの経路の一部である。質問や返信、金融入力、方針の数値、注文は作らない。既存daily結果の `proposed_action` はpolicy/価格未確認の研究提案として残し、この計算済み記録とは区別する。

```bash
.venv/bin/ir-agent --db PATH research-decision-review add REQUEST.json
.venv/bin/ir-agent --db PATH research-decision-review show REVIEW_ID
```

Pythonでは `Harness.review_research_decision(request, *, now=None)` 又は `ResearchDecisions(store).add_review(request, *, now=None)`、読取りは `ResearchDecisions(store).show_review(id, *, now=None)`。`now` はengine/test用の信頼時計であり、CLI requestから指定する時刻ではない。返却envelopeは `record`、table由来の `first_saved_at`、`added`、`current_view` を持つ。

## 入力は既存recordへの参照と根拠付きassessment

必須キーは次の7つだけ。任意 `synthetic` はbool、省略時false。

| キー | 内容 |
|---|---|
| `id` | callerが固定する論理要求ID。再送は同じID・同じ要求を使う。 |
| `company_id` | 既存会社。 |
| `expected_thesis_version` | 現在raw最新版の期待版。strict現在選択とも一致する必要がある。 |
| `policy_id` / `policy_version` | 登録済み方針の明示版。最新版を自動選択しない。 |
| `decision_quote` | 既存decisionと同じsource結合quote。会社/通貨/価格/観測・取得時刻/source ID、price_path/observed_at_pathを指定する。空や有効な不足はunresolvedにできる。 |
| `assessment` | 厳密に `thesis_status`, `evidence_ids`, `reviewer`, `rationale` の4キー。 |

assessmentの `thesis_status` はintact/invalidated/uncertain、根拠IDは選んだthesisのevidence_idsの空でない部分集合。reviewerとrationaleを記録する。これは人/agentの根拠付き評価であり、engineが事業仮説の正しさや財務入力の意味を事実認定した結果ではない。好意的な語調からthesis_statusや予想を自動設定しない。

callerの `recorded_at` / `as_of` / `held` / `action` / `first_saved_at`、任意のthesis/policy/source snapshots、reply/question ID等の未知キーは拒否する。保有は既存の明示position receiptから解決し、会社import時のheld=falseを未保有の確認へ転用しない。明示positionも利用者の申告であり、broker検証済みではない。

## 保存前の検査と再送

新writeはtransaction取得後のruntime現在時刻でだけ評価する。raw最新thesis版と期待版を比較し、strict-currentの選択recordが同じ版かを確認する。最新の保存来歴が未知/未来でreaderが旧版を選んでも旧版で計算せず、最新snapshotへの未解決理由を保存する。無関係な旧legacy版による全体availability_status=partialだけでは、来歴の分かる選択最新版を一律保留しない。

全source/quote原典DAGを収集し、別会社・identity不整合・cycleを独立に検査する。共有親はcycleとしない。source/thesisのreceiptと取得/作成時刻、sourceの既存公開性metadata、IR由来sourceの元reply/question本文・会社・receipt、最新の依存返信分類を別項目として点検する。source公開性の元holdは、後のpublic assessmentで書換えない。rawreply受信時の初期分類と評価時のimmutable IR source分類も混同しない。最新assessmentがない時は既存契約どおりIR sourceの分類を使い、初期unclearから正式適用public sourceへ進んだ正当な経路を初期分類だけで保留しない。

quoteの会社・市場source・取得時刻・数値/観測時刻のfield bindingは、policyやposition不足でpure計算が早くreturnする場合でも先に検査する。共有したquote helperは旧pure側のearly-return順序を維持し、新wrapperでは部分quoteに提示された矛盾も検査する。別会社、壊れたfield path/値、synthetic祖先の実案件混入等はエラーで新行0。未取得原典、未知来歴、設定や価格不足等はunresolvedとして保持できる。原典全文の意味確認や金融入力採用を保証しない。

同ID・canonical同要求の再送は、現在最新版のCAS検査より先に元recordを返す。first_saved_atを更新せず、新しい計算へ置き換えない。同IDの変更要求は拒否する。新しい価格・policy・assessmentで再点検する時は新IDを使い、現在の期待thesis版を指定する。別policyの新しい登録版ができても、既存記録の固定版/hash/登録時刻は変えない。

## recordと現在表示

独立 `research_decision_reviews` tableに、request/SHA、thesis/policy/quote/position snapshots、全source IDs/SHAとsnapshots、保存来歴診断、消費した依存分類版、元reply/question binding、assessment、計算resultをatomicに保存する。実first_saved_atはtableの信頼時計列を使い、RecordAvailabilityへ新entityは追加しない。旧reply専用table/JSONと金融モデル・判断閾値は変更していない。

`record.basis.kind` は `saved_research`。`has_IR_reply_origin` は全source型から算出し、閉包欠損でIR不在を証明できなければnull。`public_only:true` は**保存sourceの全閉包にir_replyがなく、既存の型/metadata公開性/availability検査を通る**という機械的区分である。元サイトの外界での公開、真正性、issuer identityを独立認証した意味ではない。IR祖先が公開補足である場合も計算できるがpublic_onlyとは呼ばない。欠損/held/未知の閉包を公開only認定しない。source閉包の区分と判断resultの完了は別で、public_onlyでもpositionや価格等が不足すればresultはunresolvedとなる。

`current_view` は元resultを上書きせず、次を現在のruntimeで点検する。

- 固定policyの既存quote期限。境界時刻ちょうどはfresh、1µs超過はstale。
- raw最新thesis版、strict現在選択と保存thesis SHA/receipt、保存thesisの再点検期限。
- 依存返信の新分類版/hold、保存source SHAと現在の全原典availability。
- 現在の明示positionが不明か、保存時からheldが変わったか。同じheldの再申告だけでは変化としない。

不足や変化はrequires_information_review / requires_thesis_review / requires_position_review / requires_price_reviewとして現在actionをunresolvedへ回す。過去の計算は `historical_result` と不変recordで保持する。公開へ戻った未消費の分類新版も、新reviewまでは再点検対象。過去unresolvedを表示の時間経過だけでbuy等へ昇格させない。表示上の現在条件に問題がなくても、金融モデルやassessmentの妥当性が検証済みとはしない。

過去時点のwrite、PIT/retrospective判断の保存、baselineとquestionの紐付け、自動policy移行、価格取得・送信・注文・常駐schedulerは今回の範囲外。過去分析は既存の明示二締切read-only viewを使い、現在保存したrecordを過去の事前判断にしない。

[実装・検証記録](../research/ir-research-decision-review-integration-2026-10-15/README.md)と[設計比較](../research/ir-public-decision-review-design-2026-10-15/README.md)に根拠・変更前bytes・focused検証・限界を保存した。
