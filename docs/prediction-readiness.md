# 予測と観測の読み取り専用準備状況監査

予測保存と現在の観測を結合し、事前性・参照・欠損・保留を一覧にする。**採点は行わない。** 参照の一致や観測上の状態確定だけでは、原文との独立照合、学習来歴、時間漏洩の不在、校正を検証したことにならない。

原則は[予測保存と実観測の接続契約](probability-prediction-contract.md)に従う。同契約が区別する原典のproper scoring ruleと、本プロジェクトのID・版・実保存時刻の契約をそのまま区別する。ここに採点式、尤度の推定法、金融条件、重み、必要標本数を追加していない。

## 実行

```bash
.venv/bin/python scripts/report_prediction_readiness.py \
  --db data/ir-research-2026-10-15.sqlite3 \
  --as-of 2026-10-15T18:00:00+09:00
```

既存DBをSQLite `mode=ro`と`PRAGMA query_only=ON`で開き、`BEGIN`からの一貫した読み取りsnapshotを使う。`Store`のconstructor、schema作成、書込み、採点器、SDK、ネットワークを呼ばない。DBのJSONは既存`models.parse_json`で読み、重複キーや非有限定数を拒否する。対象tableが存在しない場合は未知として返し、既知の空tableと区別する。会社tableを持たない独立観測DBも読み取れる。

## 純粋APIと入力

[prediction_readiness.py](../src/ir_agent/prediction_readiness.py)の公開APIは次のとおり。

```python
audit_prediction_readiness(snapshot: dict, *, as_of: str) -> dict
```

`as_of`はオフセット付き日時。`snapshot`のsectionは次の3つで、欠落はtable未知、空配列は既知0件を表す。各行の`record`は保存JSONをdecodeしたobjectであり、callerの入力を書き換えない。

| section | 行のfield |
|---|---|
| `observation_versions` | `observation_id, version, design_sha256, record, first_saved_at` |
| `predictions` | `id, observation_id, observation_version, model_id, model_version, request_sha256, record, first_saved_at` |
| `models` | `model_id, model_version, commitment_sha256, record, first_saved_at` |

観測行の`record`は観測本体、予測行は`ir_predictions.data`の保存結果、モデル行は不変のmodel/training commitmentである。sectionや行の型、必須field、重複ID/版、不正日時は通常の`ValueError`とする。可視観測の構造・ID・design不整合も監査自体を失敗させ、壊れた母集団を黙って縮めない。可視予測本体の不正や参照/hashの不一致は対象予測の`invalid_prediction_reference`として残す。

## 可視性と左結合

実`first_saved_at <= as_of`の観測版から最新versionを選ぶ。そのrecordを既存`observations.summarize_observations`へ渡し、記録時点の可視性、最初の期限内返信、同時刻衝突、期限までの受信確認済み無回答、遅延、公開性保留、分類訂正、外部影響、state未判定を再利用する。新しい信号選択規則は作らない。

可視予測は`first_saved_at`とrequestの`created_at`の両方が`as_of`以前のもの。元の観測を左側の母集団とし、予測がない観測、未送信、到達失敗・不明、無回答確認不足、未判定、保留を残す。複数予測がある場合も観測数を増やさず、その観測の`predictions`配列へ列挙する。現在の可視母集団へ結合できない予測は`orphan_predictions`へ別表示する。未来の観測版が後から過去の監査へ入ることはない。

## 参照と事前性の点検

- 予測のrequest ID、DB参照ID/版、観測snapshot SHA、design SHA、保存側の会社・質問・cohort・状態/signal定義・対象期間・synthetic区分を照合する。current観測の設計も予測時の参照と一致する必要がある。
- 予測保存器のrequest/manifest検証と矩形行列検証を再利用する。全signal×全state、有限な0〜1、各stateのsignal合計が十進値で厳密に1であることを点検し、補完・平滑化しない。
- request SHAとmodel/training commitmentを照合する。model tableがない場合は未知とし、manifest hashの一致を学習履歴の独立確認とは扱わない。
- 観測設計の実保存が予測生成より後、生成が予測実保存より後、予測実保存が観測期限より後なら不整合として残す。
- **後追い保存された送信記録も再点検する。** 現在可視の全観測版を辿り、実送信試行時刻や実受信時刻が予測`first_saved_at`より前なら`invalid_prospective_timing`とする。予測保存時のrecordにdispatchがなかったことだけでは事前性を認定しない。先に判定済みのoutcomeも同様に検出する。
- 時刻が同一の場合は、それだけで実行順を証明できない。`no_detected_violation`は検出した時間違反がないという意味であり、事前性の独立検証済みフラグではない。

stateが判明した後にsignalを変更した訂正は、`signal_classification_leakage_candidates`へ訂正ID・対象版・時点を残す。これは結果を見た再分類の候補であり、担当者が実際にstateを見たとの断定や、訂正の自動採否ではない。現在の記述的観測viewへ訂正が適用されても、予測評価に採用できる保証は追加しない。

## 出力の意味と限界

全体は`status: prediction_readiness_only`。table既知/未知、可視観測・予測数、予測なし観測数、孤立予測、送信/応答/検証状況の件数、各観測のcurrent版・SHA・実保存時刻・既存view・各予測の理由を返す。

個別予測の参照や時点に問題がなくても、最大の状態は`needs_evidence_binding_review`。`evidence_binding_verified`、`training_provenance_verified`、`calibration_verified`は常にfalseである。観測の`eligible_for_descriptive_table`や保存された自己申告のverified欄を、採点可能・校正済みの証明へ変更しない。原文・state根拠・学習履歴の独立照合は別途必要である。

この監査は`score_categorical_forecast`を呼ばず、条件付き行を採点へ渡さず、評価履歴も保存しない。予測や観測が0件でも監査は正常に終了するが、IR予測の成績や投資判断の有効性は確認されていない。

[有限テスト](../tests/test_prediction_readiness.py)は後追い送信/受信、as-of前後、欠損table、予測なし、孤立参照、会社/synthetic/SHA/矩形不整合、無回答・外部変化、state判明後のsignal訂正、入力不変性、DBファイルhash不変、重複JSON/NaN拒否を確認する。
