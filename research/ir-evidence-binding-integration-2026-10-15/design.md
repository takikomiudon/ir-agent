# 保存予測からproper scoreへ接続する最小設計

2026-10-15。設計のみ。production、DB、既存docs/testsの変更・追加取得・採点は行っていない。

## 推奨する次の一単位

**採点adapterの前に、source原文・版・引用・全親・実保存証跡を保持するread-only evidence-binding reportを実装する。** 既存`prediction_readiness`は母集団と予測参照/確率矩形/既知時点を点検できるが、観測verificationの引用を保存sourceへ解決せず、元signalの本文分類根拠も確認しない。`eligible_for_descriptive_table`を使って直ちにscorerへ渡す実装は、この不足を迂回する。

推奨する実装範囲は新規module・read-only script・小さな回帰testだけ。既存の予測保存器、観測設計、訂正保存器、金融判断を変更せず、scorerもまだ呼ばない。最初の価値は「どの既存観測にどの保存本文が結び付き、何が不足するか」を再現可能にすることにある。

## 参照した仕様と原典

- `/workspace/ir-agent/docs/probability-prediction-contract.md`
- `docs/probability-prediction-storage.md`, `docs/prediction-readiness.md`
- `docs/observation-corrections-design.md`, `docs/probability-scoring.md`
- `src/ir_agent/prediction_readiness.py`, `observations.py`, `observation_store.py`, `observation_assessments.py`, `probability_scoring.py`, `availability.py`
- 先行の詳細案`docs/prediction-evidence-binding.md`。同文書の「独立first_saved_atがない」という記載は新しい`record_availability`導入前の不足を説明するもの。次の実装は、現在のreceiptを利用しつつ、欠損・legacyの過去を推測しない。
- 保存済みGneiting–Raftery (2007)著者公開本文、`research/probabilistic-evaluation-2026-10-15/README.md`, `sources.json`。PDF SHA `d31a0c5f0ae8fec1a0a6544db5d056645b2d7296d71b44a2e8efb293c7d87ba2`。

原典PDF1/誌面359のpropernessは真の分布を申告することが期待rewardで最適になる性質。PDF5/誌面363のBrier/logを既存計算器でlossへ符号反転している。PDF14/誌面372の観測前に予測則を固定する状況を参照するが、DB receipt、独立stateの確認、IRへの適用規約は本projectの契約である。有限標本の良いlossが真の分布や投資利益を証明するという原典ではない。

## 最小API案

```python
report_prediction_bindings(connection, binding_requests: list[dict], *, as_of: str, now: str) -> dict
```

`connection`は同じSQLite DBのread-only connection。`as_of`は観測を再現する評価時点、`now`はtrusted runtime clock。呼出元が`now`を渡し、binding requestに時計や承認fieldを持ち込ませない。`as_of <= now`。SQLite scriptは`mode=ro`, `query_only=ON`, `BEGIN`で一貫snapshotを取り、`Store`constructor、DDL、移行、presence観測、更新処理を呼ばない。JSONは`models.parse_json`で重複キー/非有限を拒否する。

母集団は引き続きas-of可視の観測全件で、binding_requestsは対象を追加/削除するフィルタではない。全予測はreadinessと同じ左結合を使う。参照不能のmapping/孤立予測は別一覧に残す。

一つのbinding requestは次の小さな対応付けとする。

```text
observation_ref: {id, version, snapshot_sha256, design_sha256}
source_links: [
  {role: premise|state_evidence,
   observation_evidence_id, source_id, source_snapshot_sha256}
]
reply_links: [
  {reply_id, observation_reply_sha256, raw_reply_sha256, basis_quote}
]
```

source_linksの逐語引用・会社・URL・公表/取得日時はrequest側で再提出せず、該当観測版の既存premise_evidence又はverification.evidenceから取る。元のIDが保存source IDと同名でも、同一資料だと暗黙認定せず上記linkを照合する。reply_linksのquoteは保存raw_text内で照合するが、そのquoteがsignalカテゴリを意味的に支持するかは別の未検証事項。

referenceの型/版/SHA/重複role-ID/曖昧な対応付けは通常の入力エラー。対象やtableの欠損は全体を成功扱いで落とさず、該当checkを`unknown`として保持する。既存recordにない余計なevidence IDは不一致として報告する。callerの`verified`, `independent`, `calibrated`, `approve`, first_saved_at等は未定義fieldとして拒否する。

## 出力とstatus

```text
status: source_binding_report_only
as_of, checked_at
table_status: tableごとのknown / unknown
population: {observation_count, visible_prediction_count, no_prediction_count,
             orphan_prediction_count, ...既存coverage件数}
observations: [
  observation_ref, original_observation_view,
  predictions: [prediction_ref, model_ref, request_sha256, readiness_checks],
  resolved_bindings: [role, original_reference, source_ref, quote,
                     snapshot_checks, lineage_refs, historical_availability,
                     current_information_checks],
  original_signal, current_signal, applied_assessment_refs,
  reported_state, selected_state: null,
  leakage_candidates, missing_bindings, reason_codes,
  semantic_state_review: unknown,
  state_label_independence: unknown,
  training_provenance: unknown,
  score_request: null, score: null
]
sources_by_id: dedupした原文source snapshotと各SHA/receipt
reply_snapshots: 必要な不変原文の参照/SHA/引用とreceipt
calibration: unknown
posterior_validation: unknown
ir_incremental_value: unknown
evsi_adoption: not_performed
```

個別の狭いcheckは`matched / mismatch / held / unknown / not_applicable`。`matched`は機械照合の対象を具体的に示す（例：同じsource snapshot、同一引用）。包括的`evidence_verified:true`や`ready_for_scoring`は出さない。既存APIの未検証falseを書き換えず、報告全体でも校正や独立stateを認定しない。snapshotを出力するときは内容を修復/省略して別物にせず、原JSON内容とSHAを保持する。raw sourceと抽出本文の原文保存場所・raw SHAが存在する場合はその来歴を示し、存在しなければraw照合はunknownとする。

## 正とするDB記録・結合条件

| 対象 | 正とする記録と必須の照合 |
|---|---|
| 母集団・現在の観測版 | `ir_observation_versions`の実first_saved_at <= as_ofから最新version。record内各イベントもrecorded_atで切り、既存viewを再利用。予測なし/未送信/未判定/保留を落とさない。 |
| 予測の元観測 | `ir_predictions`のrequest.observation_refが指す同DBの元版。ID、版、全snapshot SHA、design SHA、会社/質問/cohort/定義/syntheticを照合し、現在の観測版と混同しない。 |
| 予測・モデル | 不変request、request_sha256、first_saved_at、created_at、`ir_prediction_models`のcommitmentを解決。矩形と十進厳密合計はprediction_storeの既存validatorを再利用。 |
| 送信/受信 | 観測全可視履歴のdispatch/receipt実発生時刻と予測first_saved_atを比較。後追い保存で過去の実送信が見つかった場合も事前性違反にする。mutable question.sent_atだけから当時の保存順を推測しない。 |
| question/reply | `questions.data`と`replies.data`の不変JSON、正しいID/会社/質問/受信日時、raw_text/quote SHA、`record_availability`を照合。Store.questionが付ける現在status等を元snapshotへ混ぜてhash計算しない。 |
| premise/state公表根拠 | 観測版の当該evidence objectと明示mapping先` sources.data`。会社、ID、URL、逐語引用、公表/取得日時、完全source SHA。URL又はIDの一致だけでsnapshot一致としない。保存sourceにない引用はmismatch。 |
| 原典closure | `models.source_origins`でsingle/array両方を全て辿る。全親の会社、時点、公開性、synthetic、欠損、循環を確認。共有親DAGは循環にしない。保存source.content_hashと全JSON SHAを混同しない。 |
| 当時の存在 | `RecordAvailability.at`のread-only判定を再利用。snapshot SHAをreceiptに一致させ、申告effective時刻とknowledge cutoffを分ける。receipt table自体なしならunknown。 |
| 公開性 | root/全親の固定metadataだけでなく、IR原典のreply IDを解決し`reply_information_reviews`の実first_saved_atとrecorded_at両方がcutoff以内の最新版を確認。歴史as_ofとtrusted nowの結果は別々に保持。 |
| 訂正 | 対象元snapshotとassessment ID/対象版/expected_previous_version/保存時刻/binding原典SHAを保持。保存時verifiedを現在の公開性保証に読み替えない。 |

新receiptはpresenceの証跡を与えるが、その資料が真実か、公開性やstateの意味が正しいかの証明ではない。`trusted_insert`なら実first_savedを利用できる。`legacy_presence`はknown-byでありfirst_saved_atはnullのまま。presence以前の当時存在はunknown、presence以後の利用可能性だけを現在のlibraryの意味に従って確認できる。legacy known-byを最初の取得/保存へ遡及補完しない。

時点の点検を三つに分ける。予測の生成/訓練cutoff時、評価as_of時、現在now時である。入力資料が予測時に未利用なら事前性を満たさず、後の公表資料が対象期だけ過去という理由で訓練へ戻さない。state判定用の後続資料は評価as_ofまでに可視であることを別途確認する。現在既知の公開性保留は新しい利用を止めるが、歴史的snapshot/既出力を消さない。

## state判明後のsignal再分類を迂回しない

既存viewの現在signalをそのまま主評価のobserved_categoryにしない。元signal、各訂正、最初にstateが判明した可能性のある日時と根拠利用可能時刻を時系列で並べる。verification.recorded_atだけでなく実保存、資料公表/取得/known-byも表示する。分類時点やstateを見得た時点が不明なら独立性unknown。

state判明後のsignal変更は漏洩候補を保持し、主たる前向き採点への採用を保留する。早い申告日だけで非盲検の可能性を消さず、担当者の名前/独立宣言も証明にはしない。元signalへ自動的に戻して採点することもせず、事前に固定した採用分類・訂正規約と適用の証跡を別途必要とする。観測の記述的viewへ訂正を適用することと、予測評価へ採用することを分ける。

無回答は本文bindingの代わりに実送信と期限までの完全な受信確認ログを必要とする。現在はresponse_checkが自己申告であり、完備したログの独立照合は自動的にできない。本文確認がnot_applicableでも全体が確認済みになるわけではない。外部影響の解消も独立stateを作らない。

## その後の最小scorer adapter（今回の次単位には含めない）

根拠報告の次には、事前の評価手順、独立stateの判断記録、採用signalの固定方法、訓練/評価来歴の確認範囲を版付きで接続する契約が必要。callerの承認booleanでreportのunknownを消す入口を設けない。状態の意味・独立性を確定できない現状では、次のadapterも本番採点対象を作れないと正直に示す。

将来、別途確認したstate `s`とsignal `y`を採用できる場合の純計算入力は厳密に次である。

```python
categories = list(frozen_observation['signals'])
probabilities = {signal: saved_prediction['likelihoods'][signal][s]
                 for signal in categories}
observed_category = y
```

行列の表現はsignal→stateなので、実装上は`likelihoods[signal][s]`を全signalについて取り出す。実現state一つの条件付き分布だけを一件として採点する。未実現state全行へ同じsignalを与えず、prior加重・posterior・周辺化で欠損stateを補完しない。

既存scorerの残り3引数はnonempty文字列なので、prediction ID/request SHA、観測ID/使用版/snapshot SHA、定義SHAをcanonical JSONの参照文字列へencodeできる。structuredな対応表と根拠報告のhashは外側結果に保持する。計算器のverification=false欄は変更せず、外側の機械照合結果とも別にする。結果は`calculation_only`とし、score、採用ラベル、分類版、原典版を無言で差し替えない。

Brierは全カテゴリ和、logは自然対数。実現カテゴリの確率0はlog positive_infinity/value nullで、欠損/保留/有限0と区別する。epsilon、score閾値、必要N、モデル比較重みを追加しない。良いlossからposteriorの正しさ、calibration、IRなしとの差、EVSI、金融方針への採用へ進めない。

## 有限な受入ケース

1. 全件0/予測なし/未送信/不達/状態未判定/保留でも母集団とcoverageを保持し、scoreはnull。
2. table欠落と既知空を区別。source/receipt/レビュー表がない独立観測DBはunknown。
3. 観測quoteを含む実sourceに明示mappingできる。本文とSHAはmatchedになるが、state意味/独立性はunknownのまま。
4. 同じID/URLでも本文や全JSON SHAが違えばmismatch。引用が別資料にだけある場合も不一致。
5. 第二原典だけが未来/別社/保留/syntheticなら問題を検出。rootがpublicでも迂回不可。共有親DAGは正しく通る。
6. source/reply/question receiptのsnapshotが一致しない、receiptがfuture、trusted first-saveがcutoff後なら利用不可/unknownの理由を保持。
7. legacy presence以前はunknown。presence以後はknown-byの意味を保持しfirst_saved_at nullを埋めない。
8. 予測保存時未送信に見えても、後着のactual dispatch/receiptが保存前ならprospective timing invalid。
9. 保存済みbindingの後に保留訂正が追加された場合、新報告は現在held、歴史版/旧報告/DBを改変しない。
10. 16時as_of、17時保留、翌日nowなら歴史的照合と現在heldを両方表示し、新利用は保留。
11. state判明後のsignal再分類と、日時/独立性が不明な分類は主評価採用を保留。元分類へ自動fallbackして点数を作らない。
12. 実返信を無回答に変えず、遅延返信で期限内無回答を上書きせず、同時刻の衝突を消さない。
13. 受信確認自己申告だけならログ完備性unknown。外部変化の一件解消でも他の保留/state_changedは残る。
14. 訓練manifest hash一致でも当時版が未解決、評価会社/期が混入、外部モデル履歴不明なら確認済みとしない。
15. invalid bool/list/dict/nullをenum/版/pathへ置いても通常の検証エラー。caller approval/時計fieldを拒否。
16. report実行前後でDB bytes/total_changes/元snapshotが不変。再実行は同じsnapshot/nowで同じ結果。読取transaction途中の更新が混入しない。
17. 将来adapterでは観測state一つの分布だけを既存scorerへ渡し、p(y)=0の無限logを保持。未観測stateやunknownを採点しない。

これらは実装時の条件で、今回テストしたとの主張ではない。

## 根拠照合後にも残る未検証事項

stateの意味・独立判定の適切さ、IR信号とラベルの循環、分類担当者が実際に何を知っていたか、会社/部署/時期間の依存、全企業への選択偏り、外部モデルを含む実訓練データと学習実行、未使用データでのモデル選択、IRなし比較との追加価値。snapshot/receipt/quote一致でこれらを真へ変更しない。最小単位の完成条件は原文へ結べた範囲と不足を正確に出すことであり、架空の精度・合格点・尤度を作ることではない。
