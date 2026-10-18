# 条件付き信号予測の不変登録

`PredictionStore` は[予測接続契約案](probability-prediction-contract.md)のうち、**既存観測設計に結び付けた予測の登録と読出しだけ**を実装する。[単一予測の採点計算器](probability-scoring.md)への接続、学習、実観測の適格性点検、評価・訂正履歴、集計は含まない。登録成功は較正や投資判断の有効性を意味しない。

原典の事前予測に対するproper scoring ruleの考え方と、このプロジェクトで追加したDBの保存規則は[契約案の根拠表](probability-prediction-contract.md#原典が支持するものとこの設計で決めるもの)で区別している。本実装は尤度、合格点、必要標本数、平滑化、投資基準を追加しない。

## APIと接続

```python
from ir_agent.prediction_store import PredictionStore, SCHEMA

# 同じconnectionにObservationStoreのSCHEMAが既に存在すること。
# SCHEMAのインストールは通常Store初期化時に行い、書込みtransaction外で行う。
connection.executescript(SCHEMA)
predictions = PredictionStore(connection)
saved = predictions.register(request, now=trusted_execution_timestamp)
item = predictions.show(saved["id"])
visible = predictions.list_as_of(as_of=offset_timestamp)
```

`now`は保存入口の信頼できる実行時計から渡すタイムゾーン付き文字列であり、要求JSONから受け取らない。テストでは明示した時計を使う。SQLiteの既存接続を共有し、外側にtransactionがあればsavepointを使って外側をcommitしない。単独の書込みでは`BEGIN IMMEDIATE`で観測版・モデルcommitmentの点検と予測保存を原子的に実行する。

`ir_prediction_models`と`ir_predictions`を追加する。元の観測、元の各版、設計SHA、返信・判定は変更しない。観測IDと版、モデルIDと版への外部キーを持ち、同じ会社・質問に別の観測IDを作る操作はない。APIにupdate/deleteは設けない。DB自体への無制限の直接編集に対する耐改竄性を保証する設計ではない。

CLIからは同じDBに対して次のように使う。`REQUEST_FILE`は参照・manifest・明示確率を全て用意した要求であり、未入力のtemplateをそのまま投入するものではない。

```bash
.venv/bin/ir-agent --db PATH predictions register REQUEST_FILE
.venv/bin/ir-agent --db PATH predictions show PREDICTION_ID
.venv/bin/ir-agent --db PATH predictions list --as-of OFFSET_TIMESTAMP
```

## exact入力

[template](../examples/probability-prediction.template.json)は**未入力の雛形**で、そのまま登録すると拒否する。`null`を埋めるための確率や学習履歴は生成しない。`synthetic:true`は架空例向けの明示で、実案件への自動採用を意味しない。

| 欄 | 必須の内容 |
| --- | --- |
| `id` | 一意の予測ID |
| `observation_ref` | exact `{id, version, snapshot_sha256, design_sha256}`。同DBに存在する観測の現在版を参照する |
| `model_ref` | exact `{id, version, trained_at, manifest, manifest_sha256}`。版は1以上の整数、manifestは非空JSON object |
| `training_ref` | exact `{information_cutoff, manifest, manifest_sha256}`。manifestは非空JSON object |
| `created_at` | 明示した生成・確定時刻。タイムゾーン必須 |
| `likelihoods` | 観測設計の全signal×全stateを持つobject。方向は`likelihoods[signal][state] = P(signal | state)` |
| `provenance` | exact `{kind, reference, rationale}`。kindは`external_evidence` / `user_assumption` / `synthetic_example` |
| `synthetic` | 明示boolean。観測と完全一致。架空根拠をliveへ昇格しない |

上表の8欄以外や、各参照objectの未知欄を拒否する。文字列は前後空白のない非空文字列、版はbooleanと区別した整数、SHAは小文字16進64文字。会社、質問、cohort、design_version、状態とその定義、signalとその定義、state_timing、target_period、synthetic区分は保存済み観測から導出し、要求側で再定義できない。

行列は全キーが一致しなければ拒否する。各値はJSON数値または数値文字列で、有限0〜1。各**stateについて全signalを足した値が十進で厳密に1**であることを確認する。各signalの行和を1にする検証では代用できない。未設定の`null`、欠けた行、boolean、非数、無限大、近似的な合計は拒否し、正規化・補完・epsilon置換をしない。数値を正確に指定するには文字列を使う。

検証用のDecimalコンテキストは呼出元から独立し、入力と呼出元のflagsを変更しない。確率の技術上限は係数256桁・指数絶対値1,000・数値トークン2,048文字、signal/stateは各1,000、セル数100,000。JSON全体は2 MiB、ネスト64段を上限にし、上限超過を黙って丸めず拒否する。これは統計的な必要標本数の設定ではない。

## SHAとmanifestの境界

SHAは`models.json_text(value).encode('utf-8')`のSHA-256である。`json_text`は`ensure_ascii=False, sort_keys=True, allow_nan=False`のJSONを使う。objectキー順を除くJSON内容を保持し、数値文字列、配列順、manifestの任意フィールドを勝手に書き換えない。これは解析済みJSONの内容commitmentであり、元JSONファイルの空白・改行bytesへのcommitmentではない。

- `snapshot_sha256`は参照版の`record`全体に対するSHA。観測の別会社IDへ参照を差し替えてもsnapshot SHAが一致しなければ拒否する。
- `design_sha256`はObservationStoreが持つ不変設計のSHA。登録時にも設計から再計算して照合する。
- 2つの`manifest_sha256`は対応するinline manifestを照合する。改変後のmanifestへ古いSHAを流用できない。
- `request_sha256`は要求全体のSHA。初回保存後は同じIDの本体を変更できない。
- 同じモデル`id, version`は、`model_ref`全体、`training_ref`全体、synthetic区分を一つの不変commitmentとして共有する。別の観測の予測にもそのまま使えるが、manifest、学習完了時刻、情報締切、学習manifest、synthetic区分を付け替える場合は新しいモデル版が必要。

manifest内部は呼出元が明示したJSON内容として保持する。任意スキーマのコード、重み、資料、観測・訂正版の参照を、この段階では独立解決しない。ハッシュ一致は学習履歴、資料の当時の可視性、会社適合、漏洩防止、根拠の真正性の確認ではない。manifestの中に`verified:true`と書いても検証済みへ進まない。

## 時間順序とライブ登録

```text
申告した情報利用可能締切 ≤ trained_at ≤ created_at ≤ 実first_saved_at
参照した観測版の実first_saved_at ≤ created_at
観測設計のdesign_recorded_at ≤ created_at
```

上記は既知の構造化時刻の順序を確認する。実保存はUTC・microsecondsに正規化し、callerが要求本体へ`first_saved_at`を持ち込めないようにする。同時刻は許容するが、観測行が既に同一DBで参照可能であるという実行順も必要になる。任意manifest内の主張を読み取って「実際の情報利用可能時刻まで検証した」とはしない。

liveでは現在版が次の条件を満たす必要がある。

- dispatchが存在しない。`failed`や`unknown`も試行済みなので、新しい事前予測の登録には使わない。
- repliesが空、verificationは未記録または`pending`。識別不能・状態変化・定義不一致も判定済みとして拒否する。
- external_changesとassessmentsが空。観測後の変化・訂正を含む設計へ事前予測を後付けしない。
- 実登録時点が既存の返信期限・状態確認期限を越えていない。

syntheticは観測区分と一致させ、過去の結果を含む架空観測への登録をliveの事前予測と呼ばない。どちらの区分でも未来の生成時刻、参照版が実保存される前の生成、未知版・旧版・SHA不一致を拒否する。

同じID・同じ要求の再送は最初の保存本体・実保存時刻を返す（`added:false`）。既に登録した予測は、その後の送信・返信・判定で再送を失敗させない。初回登録時だけ現在版・未観測条件を点検し、別内容の同IDは拒否する。再送の実行時計を初回実保存より前に戻すことも拒否する。

## 出力と未実装の範囲

`register`と`show`は要求本体、要求SHA、実初回保存時刻、導出した`observation_binding`、モデルcommitment SHA・初回保存時刻、検証範囲と制限を返す。`register`の新規保存だけ`added:true`。`list_as_of`は予測の実`first_saved_at <= as_of`を満たす一覧であり、過去の`created_at`を申告しただけの予測を保存前の一覧へ出さない。

状態は常に`candidate_prediction_only`。保存済み観測の参照照合とmanifest内容ハッシュは確認するが、`training_provenance_verified:false`、`calibration_verified:false`を維持する。liveの登録条件を通過しても、それは送信・観測の後付けが台帳上見つからなかったという範囲であり、後から記録される実際の発生時刻も含めた採点適格性の保証ではない。

後続では、実際の独立stateラベル・signalの選択、公開原文・訂正・期限との照合、実保存を含む時間順序の再点検、使った版とSHAの評価履歴が必要になる。今回の登録機能だけで[接続契約案](probability-prediction-contract.md)全体を実装済みとは扱わない。学習・採点・EVSIへの自動採用・投資判断も行わない。

検証：`.venv/bin/python -m unittest discover -s tests -p test_prediction_store.py -v`。不変再送、現在版・他社・SHA・時刻、全行列、モデル版の付替え拒否、synthetic一致、未知型、外側transaction、モデル保存後の失敗rollback、再open、実保存as-of、既存Decimal flags保持を対象にする。
