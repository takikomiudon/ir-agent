# 保存研究による判断保存の最小設計（公開baselineを含む）

**公開研究には既存保存を使い、実際に計算した公開情報baselineの正式保存に限って、返信を必須としない `research-decision-review` 別identity/tableの薄いwrapperを追加するのが最小。** 公開根拠への支持・反証候補・未解決は定性case/jobが既に不変保存できる。数値thesis付きのdaily結果も `proposed_action` と理由・反対根拠・thesis_updateを `jobs.result` へ保存するが、policy/価格未確認の提案であり、判定済みの価格判断とは扱わない。[設計記録](design.json)に既存実装のSHAと該当行を固定した。コード・ネットワーク・実DB操作は行っていない。

## 既存経路でできることと残る差

| 目的 | 最小の既存経路 | 保存の意味と限界 |
|---|---|---|
| 公開資料による特定論点の支持/反証候補/未解決 | 定性caseのsource-bound review job | 根拠・論点・引用・版・leaseを保存。金融actionやvaluationを補わない。 |
| 公開調査を通じた数値thesis更新と研究上の候補action | 既存daily job complete | `validate_result` の既存 `proposed_action`、summary、evidence、counterarguments、thesis_updateが保存される。価格計算とpolicyのbindingを検証したことにはならない。 |
| 完全な入力から価格判断を計算 | pure `decision FILE` | 質問/返信なしで既に計算できる。DB初期化も行わない。caller snapshotとDB存在/最新性は別。 |
| 適用済みIR返信への新価格点検 | 既存 `decision-review add` | 返信と評価が必須。公開研究の保存先へ偽の返信を作って流用しない。 |

公開数値判断が必要なら、既存pure計算の結果と入力を研究artifactへ残し、既存daily結果の標準action・理由・参照へ反映する運用で「研究判断を不変保存する」範囲は達成できる。ただしpolicy/quote/positionの自動結合検証や現在表示を得たとは呼ばない。unknownなextra JSON fieldをdaily結果へ入れれば現validatorは保持するが、そのfieldに価格判断の意味検証はないため、正式な判断APIの代用として保証を主張しない。

[A1/D1原則](../../docs/ir-operation-design.md)は事前仮説、反証、事業説明と評価入力、新情報後の点検を求める。質問を増やすことは目的ではない。DB tableや同一request再送という設計は本projectの適応であり、著者固有のIR戦略や数値閾値ではない。

[既存の採用手順](../../docs/decision-policy.md)は「質問前の公開情報だけによる評価と、返信後の評価を別々に保存する」と明記している。登録済みpolicy、最新thesis、明示position、source-bound quoteから計算した実公開baselineを不変保存する用途には、現在の保存経路に実際の不足がある。`ir-plan` の仮定分岐outcomesは実baseline計算・保存の代用ではない。既存daily提案を判定済みと呼ばず、この目的にだけ新経路を絞る。実装へ進むかは主担当の設計レビュー後に決める。

## 直接流用できない箇所

`decision_reviews.reply_id` はNOT NULLでrepliesへのFKを持ち、`DecisionLifecycle.add_review` もreply_idと適用済みevaluationを要求する。`review_applied` は返信branchからthesis_statusを得る。`current_decision_view` も `review['reply_id']` を直参照する。reply_idをnullableにしたり、架空question/replyを作ったり、research recordへダミーreply_idを足して既存JSON契約を偽装する方法は採らない。

一方、`evaluate_decision`、`sources_for`、全原典DAG、source/thesis保存来歴、明示position、source_assessmentsは再利用できる。`source_assessments(..., reply_id=None)` でもIR由来sourceのmetadata.reply_idから依存返信を発見する。新しいresearch wrapperは、新規の返信を必要とせず、過去の公開補足IRが祖先にある場合も訂正holdを消さない。命名は `research-decision-review`、basisは保存研究と明示する。全originに `ir_reply` がないことと公開性点検成功をengineが確認できた部分集合だけをpublic-only baselineと呼ぶ。IR祖先がある案件はそのbasisを表示し、public-onlyと呼ばない。callerからpublic-only認証を受け取らず、欠損/held原典があれば純公開とは確定しない。

## 必要な場合だけ足す最小契約

新しい `research-decision-review` / `research_decision_reviews` を別identity/tableにし、既存reply table/JSONは変更しない。必要列はid、会社/仮説版、固定policy ID/版、request SHA、immutable data、trusted first_saved_atと既存recordへのFKで足りる。新たな汎用registryや別request-receipt tableは要らない。

caller入力は安定した論理id、既存company_id、expected_thesis_version、policy_id/version、sourceに結合したdecision_quote、assessmentのthesis_status/evidence_ids/rationale/reviewer。synthetic区分は明示可能だが架空入力を実案件へ昇格させない。policy/thesis/sourceの任意snapshot、held、保存時計、action、valuation結果はcallerから上書きさせない。assessmentは会社の語調から自動決定せず、根拠付きreviewer判断として保持する。

最小版の新規writeは**信頼できる現在時刻での評価だけ**にする。transaction取得後に時計を採取し、現在raw最新thesis版とstrict-currentで利用可能な選択版の両方がexpected版と一致することを確かめる。同じtransaction内で固定policy版と登録時刻、会社一致、全sourceとquote原典DAGの来歴/公開性、明示position、最新visible依存返信分類を解決してから既存pure decisionを呼ぶ。最新policyを自動選択するのではなく、指定済みの固定版を使う。

未知のpositionはimport時held=falseで埋めず未解決にする。知られていない保存来歴も未解決とし、原文公表/取得日時で補完しない。選択した最新recordの来歴が確認できる場合、無関係な旧版legacyがあるという理由だけで現在判断を一律禁止せず、選択recordのavailabilityと除外診断を分ける。

identity不正、別会社、壊れた引用/価格binding、変更済み同id要求等はエラーで追加0。有効な要求だが価格・position・設定値等が不足する場合は、既存規則のunresolved理由を不変保存できる。判断とrequest、thesis/policy/quote/position snapshots、source IDs/SHA閉包、依存分類版、availability診断、実保存時刻をatomicに保存し、thesis・会社・source分類・質問・返信を変更しない。

## 版、再送、時間の扱い

同id・同requestの再送は、最新thesisのCAS検査より先に元recordを返す。後でthesisが進んだことを理由に正当な再送が別判断を作らず、同idでquoteやpolicyを変えた要求は拒否する。basisが保存研究であることと全originのIR有無をengineが記録する。新しい価格の再点検は新idと現在のexpected版で行い、同じ返信を適用し直さない。元resultと現在viewを分けるため、再送の現在表示だけが時間経過で変わることはある。

保存済みpolicyの指定版・snapshot/hash・登録時刻を固定する。新policy版は過去判断を書き換えない。decision前に登録されていたという事実は、価格変化や結果を知る前から閾値を固定していた証明ではない。事前性を主張する場合は、その対象と時点の別の保存根拠が必要となる。

過去分析は既存 `thesis_view` のPIT二締切一致又は明示retrospectiveを使うread-only研究を優先する。retrospectiveで知識締切を現在へ暗黙補完せず、後着資料を当時存在したことにしない。新最小APIへ過去as_ofのwriteやperformance採点まで増やさない。新review自身はtableのfirst_saved_atで存在を示し、対象がsource/thesis/reply/questionに限定された `RecordAvailability` に新entityを追加して時刻を二重管理しない。

新research用current wrapperでは、既存quote timingと最新thesis版の比較を再利用し、保存thesisのreview期限、依存分類の後日変更、現在の明示positionも確認する。position不明/held変化・期限到来・版変更・価格期限切れ・情報holdなら現在actionを保留し、historical_resultを保持する。既存current helperはpositionや全保存来歴まで保証するものではないため、そのまま全条件確認済みと称さない。current表示だけで過去unresolvedをbuy等へ昇格させず、新recordの計算へ自動変換しない。

## 実装する場合の有限受入項目

1. 質問/返信0件の架空fixtureでresearch判断を保存でき、会社・policy・thesis・sourceの旧行は不変。
2. 同id同要求は新行0・firstsave不変、同idの変更要求はreject。新idは最新thesis版が合う時だけ保存。
3. quote原典又は第二親が後着/別会社/非公開/欠損ならhold又は構造エラー。import時held=falseは明示positionと扱わない。
4. 保存前に既知の依存返信holdを検査し、source/thesis追加へ進まない。保存後の分類変更は現在viewをholdし、公開に戻った分類も未消費の新版なら自動再採用しない。
5. 現在の価格期限1µs境界、thesis版変更/期限、position不明/変化を検査し、historical_result不変。
6. 固定policyを後の最新版で置換せず、synthetic混入を実判断へ昇格しない。後着過去資料でPIT成立や当時の判断を捏造しない。
7. 計算/保存/receipt失敗でatomic rollbackし、旧replyレビューのJSON・current表示・再送挙動を回帰確認する。

この設計では実装、live/架空の計算実行、実DB照会、現案件のpolicy/position/input準備判定を行っていない。定性研究や提案の保存は既存経路を使い、正式な実公開baselineの保存はそれと区別して、この最小追加案の採否を主担当が判断できる形にした。
