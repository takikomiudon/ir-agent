# 観測台帳の分類訂正設計

**実装済み。** 既存の返信や外部変化を削除・編集せず、その分類を訂正する記録を追加する。金融判断の閾値、尤度推定、送信、売買、仮説の自動変更は追加しない。

背景となる原則は、[観測設計](ir-outcome-observation.md)の「原文と分類を分ける」「将来の状態判定を返信の正解にしない」「無回答も母集団から消さない」である。日付付きの変化と反証を保持する考え方は、保存済み[Anthropic Thesis Tracker](../third_party/anthropic/skills/thesis-tracker/SKILL.md)に基づく。以下のJSON、版、CAS、可視性の契約は本プロジェクトの記録方式であり、外部著者の投資ルールではない。

## 拡張前の不足と維持する境界

[observations.py](../src/ir_agent/observations.py)では、受信時に記録した`reply.signal`と`reply.information_status`、外部事象の`external_change.impact`を集計に使う。[observation_store.py](../src/ir_agent/observation_store.py)は`replies`・`external_changes`をprefix-onlyとし、既存項目の変更・削除を拒否する。[既存テスト](../tests/test_observation_store.py)も返信分類の書換え拒否と旧snapshotの不変性を確認している。

この保存規則は維持する。拡張前には分類の訂正先を示すイベントがなく、次の状態を正しく解決できなかった。

- 同じ返信を再点検して、事前に定義した別のsignalへ分類し直す。
- 公開性が未確認だった返信について、新たな公開根拠を確認する。逆に、公開補足という判定を撤回する。
- 外部変化の影響が未解決だったが、後の公開証拠で対象状態への影響を整理できる。

現行の`replies`には原文本文・原文SHA・保存source参照がない。**観測中の返信IDと分類があるだけでは、原文引用が照合できたと認定できない。** この不足を埋めず、同じ返信に新IDを付けて追記する方法は採用しない。件数の重複と、最初の返信を選ぶ規則の回避になる。

## 既存台帳への最小の接続

観測recordに任意の`assessments`配列を追加した。配列はprefix-onlyで、各項目も一度保存したら変更・削除できない。新しいSQL台帳を別に作らず、既存の`ir_observation_versions`へ新しい全体snapshotとして保存し、その`first_saved_at`を使う。

既存の設計固定欄、`replies`、`external_changes`はそのまま維持する。`assessments`だけを既存の`_MUTABLE`対象へ追加する。旧recordに配列がないことと、新形式で訂正が0件であることは解釈上同じだが、旧JSONへ自動で`[]`を挿入して再保存しない。旧design hashも、旧JSONも、旧版も変更しない。

`ObservationStore.append(record, expected_version, now)`を引き続き唯一の保存入口にする。ここでの`expected_version`は観測全体の版であり、後述の対象別訂正版とは別の値である。rootのCLIが実際の`now`を渡す。訂正日時を理由にDBの実保存時刻を過去へ戻さない。

初回の実案件登録に訂正イベントを含めない。事前設計の登録、実際の対象イベントの保存、その後の訂正の順にする。既存の明示的な`synthetic:true`による過去例の扱いは保持するが、syntheticでも未来の記録を受理しない。

## 訂正イベントの必要フィールド

一つのイベントは一つの既存対象を評価する。対象別の版0は、元のreplyまたはexternal_changeに保存された分類である。

| フィールド | 意味・検証 |
|---|---|
| `id` | 観測内で一意の安定した訂正ID。同IDを別内容へ再利用しない。 |
| `target_kind` | `reply`または`external_change`。他の設計欄や状態の正解を対象にしない。 |
| `target_id` | 同じ観測に既に保存された返信・外部変化のID。別会社・別質問・別観測を参照しない。 |
| `target_snapshot_sha256` | 元対象のcanonical JSONのSHA-256。原文のSHAとは区別し、保存済み対象を取り違えないために使う。 |
| `version` | 対象ごとの訂正版。最初は1、以後は連番。 |
| `expected_previous_version` | 対象ごとのCAS。最初は0。その対象の直前版と一致させる。 |
| `recorded_at` | 訂正判断を記録したオフセット付き日時。実保存時刻以前、対象の記録・直前の訂正・直前snapshotの保存時刻以後。 |
| `reviewer` | 分類を記録した担当者・worker。レビュー済みを自動的に真実と扱わない。 |
| `rationale` | 誤読、公開性の根拠の変更、外部影響の整理など、訂正の理由。実現損益や後の正解に分類を合わせる理由にしない。 |
| `basis` | 保存された原文・公開資料・対象事象との結び付き。次節の本文・引用・SHA・時点を持つ参照。 |
| `assessment` | replyの場合は完全な`{signal, information_status}`、external_changeの場合は完全な`{impact}`。部分更新で前版の値を暗黙補完しない。 |

`assessment.signal`は、質問前に固定した`signals`のうち実返信の分類だけを許す。実返信を`no_response_by_deadline`に訂正しない。`information_status`と`impact`は既存の列挙値だけを受ける。list/dict/bool/nullをenumとして受け取らず、通常の検証エラーにする。

記録の外形例は次のとおり。ID・日時・hash等はプレースホルダーであり、投入可能な実データではない。

```json
{
  "id": "ASSESSMENT_ID",
  "target_kind": "reply",
  "target_id": "EXISTING_REPLY_ID",
  "target_snapshot_sha256": "SHA256_OF_ORIGINAL_OBSERVATION_REPLY_RECORD",
  "version": 1,
  "expected_previous_version": 0,
  "recorded_at": "OFFSET_AWARE_TIMESTAMP",
  "reviewer": "REVIEWER_ID",
  "rationale": "保存原文と公開根拠を点検した訂正理由",
  "basis": {
    "target_text_reference": "IMMUTABLE_REPLY_REFERENCE",
    "target_text_sha256": "SHA256_OF_RECEIVED_TEXT",
    "basis_quote": "保存原文内の逐語引用",
    "public_evidence_references": []
  },
  "assessment": {
    "signal": "PRECOMMITTED_RESPONSE_SIGNAL",
    "information_status": "unclear"
  }
}
```

## 原文と公開根拠へのbinding

返信の`target_text_reference`は、既存Harnessに保存された不変のreply recordまたは、同等の不変原文snapshotを指す。保存入口でID・question_id・会社帰属・受信時刻を観測の対象と照合し、原文SHAと引用の一致を確認する。観測側の`target_snapshot_sha256`と、受信本文の`target_text_sha256`を同一視しない。既存観測に本文参照がなくても、原文を元の観測JSONへ後付けして上書きしない。

外部変化の場合は、元の`description`と不変の公開sourceを使う。引用とSHAの照合先、公開日、初回取得日時、対象期間、会社帰属を記録する。後の公開資料が影響の解釈を変えた場合、その資料を新しい根拠として追加できるが、元の発生日・descriptionを変えない。

公開補足への訂正は、原文の好意的な語調だけを理由にしない。公開根拠を指す参照は保存sourceへ結び付け、訂正時点で利用可能かを確認する。後に公表された資料を、受信時から公表済みだった資料として扱わない。既存の[情報公開性レビュー](../src/ir_agent/information_review.py)を参照する場合は、そのreply ID・レビュー版・実保存時刻・snapshot hashを明示し、対象と時点を照合する。

必要な原文が見つからない場合、引用・SHAの確認済み訂正として受理しない。保存入口が算定する`basis_verification`を`unverified`として残せるのは、返信を`unclear`/`potential_nonpublic`へ保留する場合、または外部影響を`unresolved`へ保留する場合だけとする。原文未結合の返信ではsignalの変更は許さず、直前のsignalをそのまま記録する。単独JSONの自己申告参照を独立照合済みとしない。

一方、signalの再分類、公開補足への訂正、外部影響を`reviewed_no_change`として集計へ戻す訂正には、独立に照合したbindingが必要である。不足すれば保存前に通常の検証エラーにし、成功や有効分母への復帰を表示しない。`basis_verification`はcallerが自由に指定して承認を偽る欄にせず、保存入口が照合結果と理由を保存snapshotへ追加する。原文未結合の保留訂正を使ったviewでは、保留理由とその状態を明示する。

保存入口が付ける照合結果と、callerの訂正requestは分けて保持する。transport retryは訂正IDと元requestの完全一致で保存済み結果を返し、照合済みメタデータの付加だけで別の訂正を作らない。clientが`basis_verification:verified`を付けて送っても承認として受け取らず、既存IDなら保存済みイベントとの一致、新IDなら新たな照合を必要とする。既存イベントの照合結果を現在の資料で無言再計算して上書きしない。

この拡張は**観測上の分類訂正**に限る。Harnessの受信原文、仮説、売買検討、既存の情報公開性レビュー、日次jobを直接変更しない。観測側の公開性を変えたことだけで、Harness側の判断保留が解ける経路も作らない。

## 保存と時点のルール

1. 対象イベントは、訂正を追加する前の観測snapshotに既に存在しなければならない。同じappendで新返信とその訂正をまとめて事前履歴のように作らない。
2. 新訂正の対象別版は連番で、期待する直前版と一致させる。別担当が全体版を更新した場合は既存の観測版CASでも拒否する。分岐した訂正履歴を作らない。
3. 新訂正は`recorded_at <= now`を満たす。根拠の公開・取得も、引用元の利用可能時刻も、訂正時点以前にする。追加イベントのrecorded_atを直前snapshotの保存時刻より前にしない。
4. 前版の訂正を変更・削除せず、訂正の撤回も次の版として、完全なassessmentと新しい理由・根拠を保存する。未入力に戻す削除操作は認めない。
5. 同じ最新recordのtransport retryは同じ観測版を返す。新しい訂正IDを作り直して件数を増やさない。版不一致・引用不一致・保存失敗では全書込みをrollbackする。
6. `records_as_of(as_of)`は従来どおり実際の`first_saved_at`で観測snapshotを選ぶ。その版に含まれる訂正について、さらに`recorded_at <= as_of`を満たすものだけを使う。過去の日付を自己申告した訂正も、実際に保存される前の集計に現れない。

例えば10月20日に過去の誤分類を訂正した場合、10月10日のledger集計は元分類を保持し、10月20日以後の集計は新分類と適用した訂正ID・版を表示する。既に出力した過去レポートを上書きしない。

台帳を介さないファイルの`summarize`には実保存時刻の独立した証跡がない。そうした入力は提供された履歴の記述的集計とし、台帳由来のpoint-in-time集計と同じ保証を表示しない。

## 集計で変えるものと保持するもの

集計用viewでのみ、対象ごとの最新の可視訂正を適用する。元の対象オブジェクトを変更せず、`original_classification`・`effective_classification`・適用した訂正IDと版・binding状況を並べて返す。対象別の訂正がなければ版0の元分類を使う。

**返信**：最初の期限内返信を選ぶ順序は元の`received_at`で決める。訂正は返信を新たに受信したことにせず、到達・受信件数・遅延件数を増やさない。訂正後のsignalも事前定義の中から選び、公開性が保留なら分類値があっても状態×signalの有効分母へ入れない。同時刻の複数返信については、それぞれに有効な分類を適用してから、既存の衝突判定を行う。一方の返信だけを消して衝突を解消しない。

**外部変化**：訂正は元の`occurred_at`を変えない。ある一件が`reviewed_no_change`へ整理されても、他の未解決・状態推定を妨げる外部変化があれば保留を維持する。外部影響の保留が解けることと、stateが`verified`になることは別である。従来のverificationに`state_changed`等が残る場合、stateの独立した根拠付き再判定なしに有効分母へ戻さない。

**無回答**：実際に期限までに受信した返信を、後の分類訂正で無回答に変えない。元から期限後に届いた返信も、訂正によって期限内へ移さない。受信確認済みの期限内無回答と、受信ログ未確認の区別は既存規則のまま保持する。

全対象数、送信数、到達失敗、未判定、保留は残す。訂正で有効分母が変わった場合、対象ID、元分類、新分類、増減の理由と適用時点を報告する。条件比率は引き続きcohort/designごとで、訂正件数を独立した観測数に加算しない。`observations_only`・`needs_calibration`を維持する。

現在の解釈による記述的集計と、質問時や返信期限時に利用できた情報の検証は分ける。訂正が後続のstate判定より後か、公開根拠が受信期限より後に利用可能になったかを監査情報として残す。結果を見て分類を合わせた可能性を消さず、現在有効な分類を過去の投資判断やEVSIの実証へ自動転用しない。

## 実装の接続と検証

[observation_assessments.py](../src/ir_agent/observation_assessments.py)が構造検証、保存原文・根拠との照合、集計用copyへの適用を担当する。`ObservationStore.append`は、既存の観測版を読んだtransaction内で照合し、callerの訂正requestと、保存入口で算定した`first_saved_at`・`basis_verification`を別々に保持する。既存CLIの`observations append FILE --expected-version N`から利用でき、SQL schema、CLI parser、Harnessの受信原文を変更しない。

原文bindingはSQLiteの`replies`・`questions`を読み、reply ID、question ID、会社、受信時刻、本文SHA、本文引用を照合する。返信本文参照の実装値は元reply IDである。外部変化は元descriptionを同じ方式で照合する。公開根拠の実装shapeは`{source_id, source_sha256, basis_quote}`で、`source_sha256`は保存source全体のcanonical JSON hashである。全原典を辿り、会社・利用可能時点・公開性・循環と、存在する情報公開性訂正の保留を点検する。`basis_verification.source_snapshots`には参照closureの各sourceのhashを保存する。JSONのcanonical表記は既存`models.json_text`と同じである。

実案件（`synthetic:false`）では、rootだけでなく全原典の`metadata.synthetic:true`を拒否する。公開性訂正は二つの時点を別々に点検する。資料が評価の`recorded_at`時点で利用できることに加え、新規appendのtrusted `saved_at`時点で既に保存・記録済みの最新保留も参照する。申告した評価時刻が保留訂正より早くても、実保存時点で既知の保留を迂回して分類や公開性を格上げできない。同じ訂正requestの再送は、元の保存済みbindingと実保存時刻をそのまま返し、現在の資料で再照合して上書きしない。

**未接続の範囲：** bindingを一度保存した後に原典の公開性保留が新たに追加された場合、その訂正を既存の観測viewへ自動反映してbindingを取り消す機能はない。現在の根拠を使う前に再点検し、必要なら観測分類の新しい保留訂正を追記する必要がある。既存の`verified`表示は保存時点の照合結果であり、現在の公開性を継続監視して保証する表示ではない。この制限を隠して有効分母や採点へ自動採用せず、旧イベント・過去集計は保持する。

必要なテーブル・原文・公開根拠がない独立観測DBでは、照合を成功とせず、signalを据え置いた公開性保留または外部影響`unresolved`への訂正だけを許可する。callerが新規イベントへ承認メタデータを付けても拒否する。台帳を通さないファイル集計は独立照合を行わない。serverメタデータのないファイル訂正は保留として扱い、メタデータを自己申告したファイルにも保存台帳と同じ証明力はない。

viewの`assessment_views`には元分類・適用分類・訂正ID・版・照合状況・申告時刻・実保存時刻を返す。返信期限後・verification記録後の訂正かも表示する。これは事後の分類判断を認識する監査表示であり、後の分類を過去の意思決定に採用する許可ではない。

[訂正テスト](../tests/test_observation_assessments.py)と[CLIテスト](../tests/test_observation_cli.py)は、以下の境界を有限の架空例で検証する。既存観測・保存テストも引き続き対象とする。

- 旧recordに訂正配列がなくても、元JSON・design hash・既存集計・版0の意味が変わらない。
- 新しいsignal定義、期限、prior、policyを訂正イベントから変更できない。実返信を無回答ラベルへ変更できない。
- 返信の誤分類訂正、公開性の保留への撤回、根拠確認後の再訂正で、元返信と全旧版が不変。
- 原文SHA・引用・target snapshot hash・会社・質問・対象IDの不一致、未知対象、壊れたenumを通常の検証エラーにする。
- 公開性を引き上げる訂正で原文・公開根拠が欠ける場合、成功扱いや有効分母への復帰をしない。
- 実案件へ架空のroot・第二原典を混ぜる訂正と、古い評価時刻を使って実保存時点で既知の公開性保留を迂回する新訂正を拒否する。
- 訂正の自己申告時刻が過去でも、実保存前の`records_as_of`には現れない。未来の根拠・未来の訂正を拒否する。
- 対象別版の飛び・重複・分岐、観測全体のstale CAS、配列prefixの変更を拒否し、retryで新しい版を増やさない。
- 元の受信日時・外部事象日時・期限・到達状態を変えず、訂正後も観測は1件。同時刻返信の衝突規則を維持する。
- 一つの外部変化を解決しても別の未解決事象や未検証stateがあれば保留を維持する。
- 任意の途中エラーでsnapshot・訂正・原文bindingが一緒にrollbackし、外側transactionを勝手にcommitしない。

入力検証とviewの呼出しは`observations.py`、不変保存とCAS・実保存時刻は`observation_store.py`へ接続した。この拡張だけでは公開性レビューやstate検証の根拠を自動作成せず、訂正後の記述的比率を校正済み尤度へ変換しない。
