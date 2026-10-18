# 数値仮説前のレビューをジョブとして処理する

明示したcaseだけを登録し、新しい保存資料や根拠付き管理日の到来で定性レビューを起票する。Anthropic thesis-trackerの新資料／pillar点検と四半期レビューを研究段階へ適応した。価格・EPS・倍率を補って金融thesisを作らない。通常の`daily`と読み取り専用の[研究監視](research-stage-monitoring.md)も利用できる。

```bash
.venv/bin/python scripts/demo_qualitative_research.py
```

このデモはメモリ内DBと一時ファイルだけを使う。分類→定性レビュー→case version 2を処理し、重複起票0・金融thesis0を確認する。

## 登録と起票

```bash
.venv/bin/ir-agent --db PATH qualitative register CASE_JSON --expected-version 0 --research-root ROOT
.venv/bin/ir-agent --db PATH qualitative queue --case-id CASE_ID --limit 10
.venv/bin/ir-agent --db PATH qualitative show CASE_ID
```

`queue`の`--case-id`は複数回指定できる。全社を暗黙に対象にしない。`as_of`は省略時の現在時刻を推奨する。当日の日付だけを渡すと日本時間の日末が未来になり、拒否され得る。

登録JSONは`case_id, company_id, issue_id, synthetic, enabled, recorded_at, case_ref, manifest_ref, management_review`を持つ。`case_ref`と`manifest_ref`は`{path, sha256}`。ROOT内のUTF8原文を凍結し、queue／claim／completeで再照合する。caseの会社・論点・synthetic区分は後から変更しない。明示的な再登録は最新versionとのCASで設定を改版し、進捗だけの更新とは別の`config_revision`になる。 設定改版では既読を自動継承しない。必要な引き継ぎは根拠付きbootstrapで明示する。Bが増えただけなら再登録は不要。

`management_review`は未設定ならnull、設定する場合は`{date, timezone, basis_ref, basis_quote}`。日付を含む引用と固定fileを要する。研究管理日を会社予定・著者の反証期限・売却期限と扱わず、次の日付を自動補完しない。

既読の引き継ぎは任意の`bootstrap_reviews`配列で宣言する。各要素は`{source_id, source_snapshot_sha256, reviewed_at, review_ref}`。当該時点の原典DAG・公開性・実保存・分類、原文SHAとreview_ref中のID/SHAを照合する。これは担当者の既読申告であり、意味の認証や過去の予測の事前性を証明しない。無指定は空配列で、引き継がない。

初回保存不明の旧資料も、検証済みlegacy_presenceによりreviewed_at以前の存在を確認でき、全原典DAGの当時/現在の公開性・分類・来歴が通る場合は定性レビューに使える。[限定修正の受入](../research/ir-qualitative-known-by-availability-2026-10-15/parent-acceptance.json)を参照する。first_saved_at:nullとfirst_save_known:falseは保持し、存在確認前の既読や新着を認定しない。未読legacyは現在のpending reviewとして読み、完了時点で既読を記録する。read-only研究監視の初保存/arrival診断は従来どおりで、現在の読解可否とは分ける。

## workerの結果

既存の`claim`／`renew`／要求receiptを使う。`packet.kind == qualitative_review`、`stage == author_condition_review`を確認し、金融研究やintake分類の結果を返さない。

結果JSONは次の5項目だけを持つ。

- `summary`と時点付きの`recorded_at`。
- `source_reviews`：全pending sourceを一度ずつ、`source_id, snapshot_sha256, read_state, outcome, basis_quote, rationale`で記録。read_stateは`reviewed`、outcomeは`supports, counterevidence, unchanged, irrelevant, unresolved`。保存原文からの逐語引用を必須にする。未解決でも確認した内容を記録でき、全文や将来見通しの正しさを認証するものではない。
- `case_observation`：`issue_id, outcome, rationale, evidence_source_ids`。outcomeは`supports, counterevidence, unchanged, unresolved`。支持・反証候補には凍結pending資料の根拠が必要。
- `management_review_update`：`{mode: retain}`、`{mode: set, management_review: ...}`、`{mode: unset, reason: ...}`のいずれか。期日到来jobでretainは禁止。setは完了日の現地日付より後の根拠付き日付、未設定に戻す場合は理由を明示する。

結果は既存の`complete JOB --worker ... --expected-attempt ... --result FILE`で保存する。case進捗・結果・job完了・attempt完了は原子的。古いcase版／担当者／世代／期限、引用不足、変更した再送を拒否する。同一完了結果の再送は最初の結果を返す。

確認中に到着したBはAの凍結packetへ加えない。Aを完了した後はBだけを次の対象にする。同社のintakeも既存leaseの排他に従う。外部manifestは書き換えず、現在の進捗と次管理日は台帳の新versionに保存する。金融thesis、分類、金融用source_reviews、会社status、IR送信、注文は定性completeから更新しない。

## 接続済みの範囲

[1,396テストと実適用](../research/ir-qualitative-job-integration-2026-10-15/README.md)で、実DBの12case・62資料を引き継ぎ、新規job0・既存全テーブル不変を確認した。既存の[manifest v19](../research/ir-research-monitoring-integration-2026-10-15/actual-case-requests-v19.json)は当時の記録として保持する。今後の台帳進捗は`qualitative show`で読む。

このCLIは保存済み資料から仕事を作る。Webの定時取得、LLM実行、外部scheduler、IR送信や発注を設置する機能ではない。定時起動する側は、公開資料の保存→intake完了→対象caseのqueue→worker処理の順を使う。

[1980の新公式PDFによる実処理](../research/ir-case-studies-2026-10-15/1980/issuer-quarter-followup/README.md)では、intake後に新sourceだけを定性packetへ固定し、完了後case v2・既読3・再起票0を確認した。これはbootstrap後の進捗であり、旧manifestの62資料は書き換えない。

`qualitative queue --limit`は新規作成するjobの上限。既存triggerはskippedへ返し、上限枠を消費しない。deferred_countは上限で繰り越した新規候補だけを数える。[2case・limit1の修正確認](../research/ir-qualitative-queue-fairness-2026-10-15/README.md)で後続caseの進行を確認した。既存daily/intakeのselected件数とは区別する。

workerが固定入力を読む際は`packet JOB_ID --view qualitative-worker`を使える。元case文書・新規sourceの全文とSHAを維持し、引継ぎmanifest全文の重複を参照へ置き換える。原packetは無指定のpacketで保持し、投影は現在のleaseや完了権限を認定しない。[実資料の表示比較](../research/ir-qualitative-worker-view-2026-10-15/README.md)を参照。

後続の[5831金融構造点検](../research/ir-case-studies-2026-10-15/5831/financial-structure-followup/README.md)を13番目のcaseへ登録し、既読2件・管理日未設定・新規job0を確認した。現在のheadは台帳から読み、初回bootstrapの12case/62資料は履歴として保持する。

新しいpacketの`prior_review`は、同一case/論点/versionの直前完了結果からsummary・観測・結果/sourceのSHA・日時を固定する。元caseの条件と後続観測を区別する。参照不正は当該caseを保留し、旧packetには現在の観測を補完しない。worker表示の`not_in_legacy_packet`は過去にそのfieldがなかった意味である。[1,409テストと実参照照合](../research/ir-qualitative-prior-review-2026-10-15/README.md)を参照。

根拠の一時変更などで旧jobが`superseded`になった場合、現在のcase・source・公開性が適格に戻ったことを確認して新しいpacketを起票できる。`supersedes_job_id`で旧jobを結び、旧packet/attemptを復活・編集しない。保留継続中は起票せず、既存pending/leased/completedは重複させない。[独立レビューと全1,425件の検証](../research/ir-qualitative-independent-code-review-2026-10-15/README.md)を参照。

[専用の担当依頼](../.agents/skills/jp-equity-ir/references/roles.md#定性レビューjobの担当に渡す依頼)ではkind/stageから先に振り分け、前回観測と元条件、5項目結果契約、独立点検と単一writerを明示する。[5831の管理日設定](../research/ir-case-studies-2026-10-15/5831/management-review-setup/README.md)は設定改版時の5既読と前回観測の明示引継ぎ例で、外部の定時起動を設置した例ではない。
