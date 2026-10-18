# 予測を実観測へ結ぶための根拠点検契約

**最小のread-only原文照合を接続済み。包括レビュー・採点接続は設計案。** 予測と観測の参照・時点・原文・分類・状態判定・訓練来歴を別々に点検する。独立レビュー保存・採点接続・校正は未実装。数値の尤度、必要標本数、採用点、金融判断条件、集計重みを定めない。

[予測接続契約](probability-prediction-contract.md)の根拠照合部分を具体化する。[準備状況監査](prediction-readiness.md)に合格したという理由や、`eligible_for_descriptive_table`だけで採点へ進めない。source hashと本文引用が一致しても、stateの正しさ、分類の意味、IRの追加価値、訓練の独立性、校正は証明されない。

## 原典とプロジェクトの契約を分ける

保存済み[Gneiting–Raftery文献調査](../research/probabilistic-evaluation-2026-10-15/README.md)と[原文・採用記録](../research/probabilistic-evaluation-2026-10-15/sources.json)を使い、新Web取得は行わない。著者公開PDFのSHAは`d31a0c5f0ae8fec1a0a6544db5d056645b2d7296d71b44a2e8efb293c7d87ba2`。

| 確認済みの原典 | 本プロジェクトが別途定めるもの |
|---|---|
| Gneiting–Raftery (2007)、PDF1/誌面359のproperness。真の分布の申告が期待rewardで最適になる性質で、strictなら最適が一意。 | 原文・状態ラベル・予測を同じ会社、質問、期間、版へ結ぶ契約。有限標本の低lossを真の分布や校正の証明にしない。 |
| PDF5/誌面363の多カテゴリBrier rewardとlog reward。 | [既存計算器](probability-scoring.md)は符号を反転したloss、Brierは全カテゴリ和、logは自然対数を採用する。この根拠点検APIは計算器を呼ばない。 |
| PDF14/誌面372の、予測則を観測前に指定する状況。 | 予測の実保存、実送信、受信、状態判明、訂正、訓練資料の当時存在を区別する前向き評価設計。原典が日本株IRのDB構成や自動合格条件を与えるわけではない。 |

`P(signal | state)`の採点は、確認した一つのstateに対応するsignal分布の評価である。`P(state | signal)`の正確さ、IRなしとの比較、IRの意思決定上の追加価値やEVSI、投資利益を同じ採点で証明しない。追加価値を調べるには、結果を見る前に定めた比較予測・共通評価対象・利用可能情報の差などが別途必要であり、本契約では未指定のままにする。

## 現在の実装で確認できる範囲と不足

| 部品 | 現在できること | まだ確認していないこと |
|---|---|---|
| `prediction_store.py` | 同DBの観測ID/版/SHA/design、矩形確率、manifest内容、実予測保存時刻、不変再送。 | manifest記載の訓練が実行された事実、当時の資料存在、評価対象の混入、校正。 |
| `prediction_readiness.py` | 観測の左結合、参照照合、後追い送信/受信による時間違反、state判明後のsignal訂正候補。 | 保存原文への独立照合、stateラベルの意味、最新の根拠公開性を全依存で継続点検すること。 |
| `observations.py` | 期限、最初の返信、衝突、無回答確認、遅延、外部変化、状態判定、可視訂正を使った記述的view。 | 元signalの本文対応、verificationの引用実在、対象期間とstateの意味対応。現在のverification根拠はcallerの参照・引用という位置づけ。 |
| `observation_assessments.py` | 元対象を保持し、本文/SHA/会社/質問/受信時刻を照合。全親の会社・時点・公開性とrealへのsynthetic混入を確認。新規保存時は申告評価時刻とtrusted保存時刻の両方の公開性保留を確認。 | 保存後に追加された保留による既存bindingの自動取消。本文引用が分類やstateを意味的に支持するか。 |

`sources`・`replies`・`questions`の実保存証跡は、[別のrecord_availability台帳](historical-availability-design.md)で保持する。新規のtrusted_insertと旧snapshotのlegacy_presenceを区別し、後者のfirst_saved_atはnullのままにする。元JSONの`retrieved_at`や`received_at`だけで当時DBに存在したとしない。来歴table自体のない独立観測DBや、legacyの存在観測より前はunknownになり得る。観測版にsource IDや引用があるだけではsource全体の当時存在を証明せず、公表時刻不明を取得時刻で補わない。

## 接続した最小APIとCLI

```python
report_prediction_bindings(connection, binding_requests, *, as_of, now)
```

```bash
.venv/bin/python scripts/report_prediction_bindings.py \
  --db PATH --bindings BINDINGS_JSON --as-of OFFSET_AWARE_TIMESTAMP
```

`--bindings`省略時は空配列として全観測の不足を返す。未送信・予測なし・未判定を母集団から除かない。scriptはmode=ro/query_only/一貫snapshotで読み、Store初期化や移行を行わない。`now`は内部の実行時計で、CLIから遡及指定できない。既存の外側transactionを関数がcommit/rollbackすることもない。

`binding_requests`は配列で、各項目には次だけを渡す。未設定/nullは不足として返し、callerのverified/承認/時計欄は受け取らない。

| 欄 | 最小の対応付け |
|---|---|
| observation_ref | id, version, snapshot_sha256, design_sha256。as-of可視の最新観測版と一致させる。古い版のmappingを現在版へ自動適用しない。 |
| source_links | role（premise/state_evidence）, observation_evidence_id, source_id, source_snapshot_sha256。引用・URL・公表/取得日時は観測側の既存参照から読む。 |
| reply_links | reply_id, observation_reply_sha256, raw_reply_sha256, basis_quote。元観測分類と保存返信原文を分けて照合する。 |

戻り値は`source_binding_report_only`。`population`と各観測の元view/予測、`reference_check`, `question_binding`, `resolved_bindings`, `missing_bindings`を保持する。全親のsourceについてusage時点/as-of/現在のavailability/publicityを分け、legacy known-byとtrusted first-saveを別表示する。source/reply snapshotはSHAとともに出力し、後から生じた保留も新しい報告で再確認する。

`binding_status: matched`は機械的な参照・本文・来歴の一致だけを指す。`reported_state`は既存viewの申告状態であり、採用状態`selected_state`はnull。`semantic_signal`, `state_independence`, `training`, `calibration`はunknown、`score_request`と`score`はnullのまま。既存の無回答/衝突/外部変化/分類漏洩の理由も保持する。

出力には非公開の返信本文や質問snapshotを含み得る。実案件の報告はGit対象外の`data/`へ保存し、公開研究ファイルへ自動複製しない。

全1,129テスト成功（35.447秒）、うち新API13件・CLI5件。架空台帳上の検証であり、実予測の校正や実IR採点ではない。実台帳の読み取りでは観測/予測0件、DB byte SHA不変を確認した。[検証記録](../research/ir-evidence-binding-integration-2026-10-15/README.md)。

## 将来の包括レビューAPI案

次の包括レビューAPI名とshapeは設計用で、未実装。先行する原文mapping照合は別の `report_prediction_bindings` に限定し、この包括レビューを実装済みと扱わない。

```python
audit_prediction_evidence(connection, request: dict, *, as_of: str, checked_at: str) -> dict
```

`connection`は同一SQLite DBの一貫したread-only snapshot。`as_of`は再現する観測・評価時点、`checked_at`は呼出元の信頼できる実行時計で、request JSONから受け取らない。`as_of <= checked_at`とし、歴史的状態と現在既知の保留を分離して返す。schema作成や`Store`のconstructorを呼ばず、欠損tableと既知0件を区別する。

requestは次の識別子だけを受ける案とする。NULLは必要な記録がまだないという意味で、暗黙の承認にしない。

| field | 必要な契約 |
|---|---|
| `prediction_id` | 同DBの不変予測を解決する。行列・会社・実保存時刻をrequest側で再提出しない。 |
| `observation_ref` | `id,version,snapshot_sha256,design_sha256`。as-of可視の既存観測版と照合し、予測が参照した元版も別に保持する。 |
| `evaluation_protocol_ref` | `null`または不変の`id,version,snapshot_sha256`。比較モデル、母集団、分類手順、訂正採用規則、group/timeの評価方法を事前に固定した別の評価計画。投資用のdecision policyを代用しない。現在この独立した保存/解決契約は未実装。 |
| `signal_review_ref` | `null`または保存された分類判断の`id,version,snapshot_sha256`。元分類か訂正版か、根拠と判断時点を固定する。既存訂正イベントだけで全要件を満たすとは認定しない。 |
| `state_review_ref` | `null`または状態判定判断の同形式参照。事前state定義、対象期間、独立した公表根拠との対応を記録した版。現在のverification objectだけで独立確認済みとしない。 |
| `training_review_ref` | `null`または訓練manifest・当時の資料版・分割を点検した判断記録の同形式参照。未実装のresolverや存在しない履歴を作らない。 |

review参照は保存済み内容を読み出すためのものである。名前のあるreviewer、`approved:true`、自己申告のSHAや`independent:true`を根拠の代用にしない。callerが検証結果、実保存時刻、存在しない当時履歴を持ち込むfieldは受け付けない。未対応schema/壊れた型/曖昧な参照は通常の検証エラー、根拠不足・未実装resolverは理由付き`unknown`として対象に残す。

返却案は`status: evidence_review_only`、`prediction_ref`、`observation_ref`、元の観測view、各項目の点検結果、保留理由、未解決参照、時点別根拠一覧である。各項目は`matched / mismatch / unknown / held / not_applicable`を用い、**matchedが何に一致したか**を明示する。例えば引用の`matched`は文字列一致であり、stateの真実性を表さない。

`score_request`は本段階では常に`null`。包括的な`evidence_verified`、`calibration_verified`、`ir_incremental_value_verified`は`null`、対応するstatusを`unknown`にする。既存APIのfalseは未検証を示しているため、その保存値をtrueへ上書きしない。参照の一致だけを集約して`ready_for_scoring`へ進める経路を作らない。

## 根拠を点検する順序

### 1. 母集団と予測の参照

最初に既存のreadiness監査を行い、観測を母集団の左側に保つ。予測なし、未送信、到達失敗・不明、未判定、未確認、保留、孤立予測を別々に残す。同じ観測に複数予測があっても独立観測数を増やさず、結果を見て最良の予測だけを採用しない。cohort/design/対象期間/syntheticの異なる標本を同じ分母へ混ぜない。

予測の矩形、会社、質問、版、snapshot、定義、生成・実保存時刻を再確認する。後で保存されたdispatch/receiptの実発生が予測保存前なら、保存当時未送信に見えていても前向き評価を保留する。同時刻だけで実行順を証明しない。

### 2. 本文と全原典の機械的照合

根拠ごとにsource ID、source全体のcanonical JSON SHA、本文SHA、逐語引用、資料位置を解決する。raw bytesが保存されている場合はraw SHAと抽出方法・抽出本文の関係も保持する。rawがなければその確認結果は`unknown`であり、本文一致からraw照合済みへ進めない。

`metadata.original_source_id`と`original_source_ids`の全親を辿る。同社・正しい質問帰属、公開性、利用可能時点、欠損、循環、共有親、synthetic区分を確認する。rootがpublicでも、第二原典が別社・未来・非公開・syntheticなら実案件の根拠として解放しない。別source IDや別URLであっても、同じIR原文の派生なら独立資料と数えない。

### 3. 公開性と訂正を三つの時点で区別

1. **根拠を使ったと申告する時点**：公表・取得・当時存在と、その時点で可視の公開性訂正を点検する。
2. **評価as-of**：実保存と記録時刻の両方で可視の最新訂正を読む。訂正ID/版/SHAを根拠一覧へ固定し、観測やsourceの古いmetadataだけを使わない。
3. **trusted checked_at**：新たに評価根拠として採用する入口では、既に見える最新の保留を全親について再点検する。古いas-ofや自己申告日時で現在既知の非公開判定を迂回しない。

歴史的な引用一致と現在の`held`は同時に返せる。現在の保留は当時のsnapshotや既計算のlossを消す理由にはせず、現在の利用・再採点の保留として別表示する。後に公開性が戻っても新しい点検版を必要とし、以前の保留を無言で解消しない。保存済みbindingの再送は旧結果を保持する一方、新しい根拠監査は新しい時点の結果であることを区別する。

### 4. signalと無回答の根拠

実返信は不変の返信ID、question/会社、原文、本文SHA、受信時刻、元分類、適用訂正版を解決する。事前のsignal定義と原文のどの記述が対応するかを、引用と明示理由で記録する。引用が本文にあることと、その文章がカテゴリを意味的に支持することは別々の結果にする。分類の意味が未確定なら`unknown`のまま採点へ渡さない。

対象の選択は既存viewに従い、最初の期限内返信、同時刻の衝突、遅延を変更しない。無回答には返信本文がないため本文bindingは`not_applicable`だが、実送信と期限までの受信確認を示す不変ログが別途必要になる。response_checkの自己申告だけで受信ログ全体を独立照合済みにしない。ログの欠落・配信状態不明・期限前は無回答として採用しない。

### 5. 独立stateと分類漏洩

state判定は、固定された仮説/state定義、`state_timing`、対象期間、会計/事業範囲、後の公表資料の実績・予想・対象期を対応させる。IRの説明signalそのもの、モデルの事後推定、株価上昇、投資損益、会社の将来予想だけをstateの実現根拠にしない。本文が同じというだけでは、会社年度と対象期間の意味対応や単発/継続の判定は完了しない。

判定記録には、使った公開根拠と逐語引用、判定手順の版、担当、判断時刻と実保存時刻、支持/反証/未確定、依存関係、残る限界を保持する。別URL・別担当・`independent:true`だけで独立性を認定せず、元IR信号からラベルが循環していないかを点検する。判断記録の実在が確認できても、担当の結論を絶対的に正しいと証明したことにはならない。証拠が状態を識別できない場合は`state:null`を維持する。

stateが知られた時点はverificationの申告時刻だけでなく、根拠公表/取得、実保存、ラベル判断、担当が利用し得た情報の履歴を分けて記録する。時刻が不足する場合は独立性`unknown`。state判明後のsignal変更、またはstateを既に利用できた可能性のある分類は主たる前向き評価を保留する。早い日時の自己申告だけで非盲検の可能性を消さない。元分類へ自動的に戻して採点する回避もせず、事前に固定した分類・訂正採用手順とその適用証拠を必要とする。事後の感度分析を行う場合は別の目的・履歴として扱う。

外部影響の`reviewed_no_change`はstateの確定ではない。他の未解決変化やverificationの`state_changed`等を保留に残し、不明stateを任意のprior・signal・平均値で補完しない。

### 6. 訓練来歴と後続の採点入口

モデル/訓練manifestのSHA一致に加え、使用観測・分類・stateラベル・sourceの版と完全snapshotを解決する。各資料/訂正が学習締切までに実際に利用可能だった証跡、学習完了、コード/設定版、対象会社・期・質問group、評価対象との重複、モデル選択に使った対象を点検する。manifestに書かれているだけの履歴は解決済みとしない。外部モデルで訓練内容が非公開、当時版が欠落、group/time規約が未指定なら該当結果は`unknown`、主たる前向き評価への採用は保留する。

このAPIが行うのは根拠点検結果の提示である。将来scorerへ接続する段階でも、別途固定した評価手順、対象signal/stateの判断根拠と採用規則、保留理由の解消を、版付きの判断記録へ残す必要がある。未知の来歴をtrueへ変更するフラグや包括承認引数を設けない。点検が十分な場合にも、採点できるのは確認したstateの一列から取り出すsignal分布一件だけであり、全stateの同時採点、priorによる重み付け、EVSIへの自動採用へ広げない。

数学的なlossを仮ラベルで計算すること自体と、その値を前向き評価の検証結果として採用することは異なる。後者の根拠がなければ、純粋計算器の`calculation_only`を検証済みへ読み替えない。観測カテゴリの予測確率0は、根拠欠損や未観測とは別であり、将来適格な入力を採点する際にepsilon置換や除外で隠さない。

## 将来の有限な受入ケース

以下は実装時の受入条件であり、今回はテストや採点を実行した結果ではない。

| 入力・履歴 | 必要な結果 |
|---|---|
| source/本文SHA/引用/全親が一致するがstate reviewがない | 文字列照合だけ`matched`、stateの意味/独立性`unknown`、`score_request:null`。 |
| state reviewの参照は実在するが、根拠が同じIR説明だけ | 判断記録の一致と循環する根拠を別表示し、独立state採用を保留。 |
| 全資料の引用が実在するが対象期間や実績/会社予想が違う | 意味対応`mismatch`または`unknown`、stateを補完しない。 |
| rootはpublic、第二原典がsynthetic/他社/未来/保留 | 全親の問題を表示し、realへの採用を保留。 |
| 評価16時、保留訂正17時、trusted点検は翌日 | 歴史的照合と現在`held`を区別し、古い日時で現在の保留を迂回しない。 |
| 以前のbinding保存後に新しい公開性保留が追加された | 新監査は現在`held`、旧binding/旧版/過去出力を変更しない。再送を新監査と混同しない。 |
| 予測保存時にdispatchがなく、後のログでは予測保存前に送信済み | 前向き時点`mismatch`、予測と観測を母集団に残す。 |
| sourceの取得日時だけは学習締切前だが、当時存在のsnapshot証跡がない | 当時利用可能性`unknown`。取得日時をDB実保存時刻にしない。 |
| 受信確認済みとの記録はあるが、完全な期限内ログの証跡がない | 既存viewの無回答表示を残しても独立ログ照合は`unknown`。 |
| state判明後にsignal変更、理由・引用は整っている | 本文一致とは別に分類漏洩候補を残し、主たる評価採用を保留。 |
| 一件の外部変化は解決したが別の変化/未検証stateが残る | 有効stateを作らず、既存viewの保留を保持。 |
| 訓練manifestはSHA一致だが評価対象が混入、または分割不明 | 混入が既知なら`mismatch`、不明なら`unknown`。どちらも校正済みにしない。 |
| 予測なし/未送信/到達不明/未判定、または根拠table自体がない | 全観測を保持し、件数・理由・table未知/既知空を区別。0点や不正解にしない。 |
| 全機械照合と判断記録の解決ができた | 狭い確認結果と判断の来歴を返す。本段階の包括検証/校正は`null/unknown`、採点requestは依然null。 |
| callerが`evidence_verified:true`、任意の実保存時刻、承認済み欄を追加 | 未定義fieldとして拒否し、保存根拠や過去出力を変更しない。 |

この契約の完成は、独立stateの実測、IRの追加価値の確認、校正、採点接続の実装完了を意味しない。未解決の証跡と意味対応はそのまま次の作業として残す。
