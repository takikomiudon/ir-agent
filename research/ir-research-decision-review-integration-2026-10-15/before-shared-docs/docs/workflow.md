# 入力仕様と運用

CLIは `.venv/bin/ir-agent --db PATH COMMAND` の形で使い、結果をJSONで返す。仮想環境を有効化済みなら `ir-agent` だけで呼び出せる。`PATH`は運用全体で共有するSQLiteファイル。主担当が更新し、反証担当は同じ入力をレビューする。

## 取り込み

`ingest FILE` のbundleは `schema_version: 1` と、任意の `companies`、`sources`、`theses` 配列を持つ。取り込みは一つのトランザクションで、途中の失敗時は全体を戻す。同じ資料・仮説版の再取り込みは冪等。IDを同じにしたまま内容を変更することはできない。

| レコード | 必須フィールド |
|---|---|
| company | `id`, `name`。`status`は既定値watch、`held`は既定値false。証券コードは数値にせず4桁英数字の文字列。excluded/special_modelには`screening_reason`が必要 |
| source | `id`, `company_id`, `title`, `url`, `source_type`, `retrieved_at`, `content`。`published_at`は不明ならnull。`requires_research`は開示なら既定値true |
| thesis | `company_id`, `version`, `recorded_at`, `statement`, `pillars`, `invalidation_conditions`, `evidence_ids`, `current_price_jpy`, `valuation`, `next_review_date` |

時刻はオフセットを含むISO 8601、日付はYYYY-MM-DD。source_typeは `public_disclosure` / `market_data` / `ir_reply`。本文は原文の文字列として保持し、対象期間・単位・連結範囲・会計基準等は `metadata` に入れる。資料を読み直した日時で初回取得日時を上書きしない。

仮説はv1から連番で追加し、出典は同じ会社の利用可能な資料を参照する。`exit_conditions`や`catalysts`などの補足フィールドも保存できる。売却検討価格・検証期限は根拠とモデル入力とともに記録する。

会社一覧を再取得しても既存のstatus、held、screening_reason、ir_contactは保持する。選別結果は明示的に変更する。

```bash
.venv/bin/ir-agent --db PATH company set-status COMPANY_ID --status active --reason '事業モデルと検証する仮説を確認した'
.venv/bin/ir-agent --db PATH company set-status COMPANY_ID --status excluded --reason '専用の評価モデルが必要'
```

これは業界名だけで自動除外する機能ではない。業界・事業の選別は技能が根拠と例外条件を確認して記録する。

## 日次job

```bash
.venv/bin/ir-agent --db PATH daily --limit 10
.venv/bin/ir-agent --db PATH claim --worker analyst-1 --lease-seconds 900 --measurement-kind observed
.venv/bin/ir-agent --db PATH packet JOB_ID
.venv/bin/ir-agent --db PATH renew JOB_ID --worker analyst-1 --expected-attempt ATTEMPT --lease-seconds 900
.venv/bin/ir-agent --db PATH complete JOB_ID --worker analyst-1 --expected-attempt ATTEMPT --result RESULT_FILE
```

`daily`の既定評価時刻は実行時点。`--as-of YYYY-MM-DD` は日本時間のその日末、オフセット付き時刻ならその時点を使う。公表・取得・仮説の申告記録日時が対象時点より後の情報は入力に含めない。保存来歴を別台帳で照合し、後着の仮説や全原典が以前のPIT入力へ混入することを防ぐ。旧行の初回保存不明は推測せず、今回の存在確認時刻より前の利用を保留する。公表時刻不明の資料は初回取得より前には利用しない。これは資料利用の制約であり、完全な過去時点の投資成績検証機能ではない。

通常の日次処理では既定時刻を使う。日付指定は日末の入力になるため、当日の途中で完了する調査には使わず、過去日または正確な時刻を指定する。

`--limit`はその呼び出しで選ぶ会社数。全workerの1日あたりの利用額を制限する機能ではない。変化なし・期限前の会社を再調査しない。未点検の開示、期限到来、保有銘柄を優先する。価格資料は通常 `requires_research=false` とし、日々の全銘柄日足だけで全社の詳細調査を起こさない。

定期起動で新規jobの件数を制限する場合は`daily --new-only --limit 10`を使う。既存triggerはstatus付きskippedへ返し、新規だけがselected/jobs_createdへ入り、上限枠を使う。deferred_countも新規候補の繰越だけを表す。無指定では従来どおり既存jobもselectedへ再表示する。既存packetやsuperseded jobを書き換える機能ではない。

数値thesis前の研究管理日は `daily` に接続されていない。[別枠の継続監視](research-stage-monitoring.md)のread-only reportで、明示case一覧の新保存・既存未確認・管理日・根拠不足を担当workerが点検する。intakeによる分類だけで著者条件への比較を完了したとせず、selectedが空でもskippedと研究段階の対象を確認する。関連確認後は旧manifestを残し、次の版へ結果を反映する。外部の定時起動・Web更新取得は別途必要である。

`claim`はjobオブジェクトまたは空ならnullを返す。戻り値の `attempts` を保存し、その確保で行うrenew/completeの `--expected-attempt` に渡す。再確保では世代が増え、同じworker名でも古い世代は更新できない。現在のjobを再取得して世代だけを付け替えず、新たなclaimのpacketと前提から作業を再開する。同一会社は同時1lease。期限を過ぎたjobは再確保できる。packetは作成時の固定入力で、後から取り込んだ資料は混入しない。仮説の版が変わった古いjobはsupersededになる。

定性jobでは`packet JOB_ID --view qualitative-worker`を明示できる。元case文書と新規sourceを保持し、引継ぎ証拠の重複全文をfile/hash参照へ置き換える。原packetは既定表示で維持し、この閲覧表示で現在のleaseや完了権限を認定しない。

RESULT_FILEの必須キー：

- `summary`：変更の理由と結論。
- `evidence_ids`：packet内の参照資料。packetにある全てのnew_source_idsについて調査結果で扱う。
- `counterarguments`：非空の反証リスト。
- `proposed_action`：watch / buy_review / hold_review / exit_review / unresolved。注文を表さない。
- `thesis_update`：完全な次版の仮説。company_idは同一、versionは元の版+1。recorded_atはpacket.as_of以後かつ完了時刻以前とし、点検日を調査日・保存日より後にする。

新しい相場や株数を確認した場合は、その根拠と `current_price_jpy` / 計算入力を次版に反映する。SDKの株価取り込みは保存済み仮説を自動上書きしない。

## 質問と返信

`question add FILE`は、`id`, `company_id`, `thesis_version`, `created_at`, `topic`, `question`, `target_parameter`, `evidence_ids`, `branches`を受け取る。priorityは0〜100、既定値50。公式窓口のURL・確認日等を補足フィールドへ保存する。同じ会社・topicの下書き／返信待ちは重複登録できない。質問には保存時点の仮説全体も付けて固定する。

branchesは最低2つ。それぞれ `id`, `condition`, `interpretation`, `action`を持ち、actionは研究結果と同じ列挙値。必要なら完全な `valuation`を事前指定する。曖昧な回答を扱うaction=unresolvedの分岐が必須で、この分岐にvaluationは指定できない。

```bash
.venv/bin/ir-agent --db PATH inbox
.venv/bin/ir-agent --db PATH question show QUESTION_ID
.venv/bin/ir-agent --db PATH question mark-sent QUESTION_ID --sent-at ISO_DATETIME
.venv/bin/ir-agent --db PATH question close QUESTION_ID --reason no_response
```

`mark-sent`は実際の外部送信が確認できた場合だけ記録する。下書きの`close`はcancelledだけを受け付ける。no_response / declinedは、有効なsent_atを持つ返信待ちの質問に限る。cancelledは下書きと返信待ちの両方で使え、終了済みの質問は再びcloseできない。終了は評価額や仮説を変更せず、無回答の観測期限や期限まで受信を確認した証拠の代わりにもならない。送信済み質問への返信が遅れて到着した場合は、期限切れ後でも保存できる。

`reply add FILE`は `id`, `question_id`, `received_at`, `raw_text`を受け取り、原文を固定する。information_statusはpublic_clarification / unclear / potential_nonpublicで、既定値unclear。

`reply evaluate FILE`は以下を受け取る。

- `reply_id`, `branch_id`：保存済み原文と事前に固定した分岐。
- `basis_quote`：返信原文からの改変していない引用。
- `rationale`：分岐の選択とモデル変更の根拠。
- `recorded_at`, `expected_thesis_version`：評価日時と確認した仮説の版。評価日時は受信以後かつ実行時刻以前、再評価では前版の評価日時以後とする。
- `next_review_date`：明確な分岐を適用する場合に必要。
- `information_status`：任意の明示レビュー分類。省略時は返信の分類を使用する。
- `expected_evaluation_version`：初回は0、保留を再レビューするときは直前版。

public_clarificationかつ明確な分岐の場合だけ、事前に指定したモデル入力を反映し、同じ会社の新しい仮説版を追加する。曖昧な分岐はunresolved、それ以外の情報分類はheld_for_reviewとして価格を維持する。再レビューでは分類理由をrationaleに残す。質問後に仮説が変わっていた場合は適用を拒否する。最新の情報と元の回答を照合し、主担当が仮説を再検討する。

`reply show REPLY_ID`で原文と評価履歴を確認する。`inbox`は優先度順の下書き、返信待ち、未評価／保留返信を各カテゴリー最大20件返す。保留返信を新たな根拠なく毎日再評価しない。

## 評価計算

循環事業の利益率を点検する中間計算には `cycle-margin FILE` を使える。[Damodaranの原典と仕様](cyclical-normalization-spec.md)に従い、明示した年間営業利益率を等重みで平均し、指定売上高に掛ける。赤字の年も保持する。期間・単位・会計範囲をそろえ、全サイクルを含むかと現在事業への比較可能性は別途確認する。年数、除外年、正常利益、再投資、割引率、投資判断を自動採用しない。

```bash
.venv/bin/ir-agent --db :memory: cycle-margin examples/cyclical-margin.synthetic.json
.venv/bin/ir-agent --db :memory: cycle-margin examples/cyclical-margin.toyota-author.json
```

合成例とToyotaの歴史的な著者例は計算検証用であり、実企業の現在の予測ではない。結果は `intermediate_only` / `adoption: unresolved`、財務的な確認は `unverified` のまま。平均利益率と売上加重利益率を混同しない。

正常化の後段では [再投資の仕様と適用範囲](cyclical-reinvestment-spec.md)の `stable-reinvestment FILE` を使える。明示された次期税引後・負債支払前営業利益（NOPAT）、同じ安定期の年成長率gと新規投資ROCから、再投資率g/ROC、再投資額、FCFFを分けて返す。次期NOPATへ成長率や税率をもう一度掛けず、ROCや税/NOLを推測しない。現実企業への適合・採用は未検証のまま。

```bash
.venv/bin/ir-agent --db :memory: stable-reinvestment examples/stable-reinvestment.synthetic.json
.venv/bin/ir-agent --db :memory: stable-reinvestment examples/stable-reinvestment.exxon-author.json
```

初版は著者例の正NOPAT・正g・正ROCの範囲に限定する。g=0は数学的に定義できるが初版では未対応、ROC=0は除算未定義で、両者を区別する。再投資率が1を超える場合の負FCFFは保持する。半期CFOをNOPATや将来FCFFに代入したり、g/ROC再投資に設備投資・WCを重ねて控除したりしない。Exxon例は2009年の著者表示入力の分解であり、現在の会社予測ではない。

保存資料の宣言SHA・バイト数・本文対応は `scripts/verify_case_source_bundle.py BUNDLE --repository-root REPOSITORY_ROOT` でオフライン照合できる。対応するcapture形式は同スクリプトが明記した2種類だけ。未知の形式はunknown、空bundleはemptyで、CLI終了0だけを一致と解釈しない。資料の真正性、引用の意味、金融入力の採用は別に確認する。

valuationはscenarios配列。各scenarioは `name`, `method`, `inputs`を持つ。通常のweightedモードは `probability` も必須で、確率は0〜1で合計を正確に1にする。確率を未設定にする場合は末尾のunweightedモードを明示する。JSONの小数は文字列で入力でき、計算はDecimalで行う。

- eps_multiple：`eps_jpy`（1株JPY）、`pe`。両方正。
- dividend_discount：`dividends_per_share_jpy`（空でない年末予想DPS配列）、`cost_of_equity`（予測期）、`terminal_cost_of_equity`（安定期）、`terminal_dividend_per_share_jpy`（明示n+1期DPS）、`terminal_growth_rate`。5入力だけを受け取る。[原典と適用限界](financial-equity-valuation-spec.md)を参照。
- dcf：`fcf_jpy`（会社全体の年末のアンレバードFCF予測配列）、`discount_rate`, `terminal_growth_rate`, `cash_jpy`, `debt_jpy`, `shares_outstanding`。金利は0.10=10%、割引率は成長率より大きくする。株式価値が負になるモデルはエラー。
- dcf_explicit_terminal：上の6入力に `terminal_fcff_jpy` を加えた**7入力だけ**を受け取る。[原典と時点の仕様](explicit-terminal-fcff-spec.md)に従い、明示したn+1期のFCFFを `(discount_rate − terminal_growth_rate)` で割り、n期分割り引く。分子へ成長率・税・再投資を再適用しない。予測配列は空にせず、金額は会社全体のJPY、割引率は予測期/安定期で同じという限定を残す。負FCFFは保持し、負株主価値のエラーは現行どおり。
- dcf_explicit_terminal_equity_bridge：明示終価の7入力に `non_operating_assets_jpy` と `minority_interests_jpy` を加えた**9入力だけ**を受け取る。[著者式と仕様](explicit-equity-bridge-spec.md)に従い、営業CFの現在価値へ現金・非営業資産を加え、負債・少数持分を控除して株数で割る。調整額はJPY・非負で、ゼロも明示する。簿価/時価、持分範囲、重複やその他請求権は出典付きで別途確認する。

`dcf_explicit_terminal` は旧 `dcf` とは別method。旧DCFに以前からある未使用のterminal fieldは引き続き無視され、過去の保存値を新しい式で再解釈しない。新methodのterminal金額はモデル入力の出典監査pathと質問前の変更許可対象へ含める。旧質問のbaselineにないpathを返信後に追加せず、新しい仮説・質問として準備する。

株主価値調整も別methodで準備する。旧 `dcf_explicit_terminal` は厳格7入力のままで、新2項目を後付けしない。新methodの出力では `enterprise_value_jpy` は非営業資産加算前の営業資産価値で、4調整額と式を別表示する。IRで会社指標の定義を確認することと、その金額を評価へ採用することを区別し、質問前に許可したpathだけを変更する。

```bash
.venv/bin/ir-agent --db :memory: value examples/valuation-equity-bridge.synthetic.json --price 100
.venv/bin/ir-agent --db :memory: value examples/valuation-equity-bridge.toyota-author-display.json --price 3060
```

前者は仮想例で92.82円。後者は2009年の著者表示入力から3,944.09円で、著者表示3,943円とは終価段階から差がある。3,060円も当時の比較価格で、現在相場ではない。未表示精度を逆生成して一致させず、現在の企業予測・売買判断・過去の前向き成績へ転用しない。

入力の出典と仮定を技能が記録する。割引率や将来成長率の自動推定は行わない。シナリオの評価額・確率加重評価額・上昇余地・シナリオ内の最大下落幅を返す。金額と百分率は出力時に小数2桁へ丸め、確率0の提示シナリオもストレスとして下落幅計算に含む。

新methodの `terminal_fcff_jpy` は入力精度を保つ文字列で返し、`forecast_periods` は整数。終価・終価PV・予測CFのPVは2桁表示で、価格条件の境界は既存の丸め前計算を使う。合成例は `.venv/bin/ir-agent --db :memory: value examples/valuation-explicit-terminal.synthetic.json --price 100`。この例の終価翌期80百万円はJPYへ明示換算した80,000,000円で、未設定確率は補わない。

## スケジューラへの接続

公開の決算予定は [材料監視の最小機能](catalyst-monitor-design.md)で、明示した会社・対象期・原文引用と対応付けて点検できる。

```bash
.venv/bin/python scripts/report_catalyst_schedule.py --db PATH --events research/ir-case-studies-2026-10-15/1332/catalyst-schedule-requests.json --date-from 2026-11-01 --date-through 2026-11-30
```

初版は日付のみ・時刻/timezone不明の予定を読み、原典・初回保存・当時と現在の分類を照合する。表示期間外も残し、`source_bound_candidate` は機械的な根拠一致を表す。`due:null`、`occurrence:not_established` を維持し、予定日が来ても発表済みにしない。意味・期対応・全予定の網羅・mappingの事前保存は未確認。元の[候補記録](../research/ir-case-studies-2026-10-15/1332/catalyst-schedule-candidates.md)にはfollowup論点も残すが、実行用JSONは対応する7欄だけを明示投影した別ファイルである。変更/取消/実施/結果採用・差分・通知・自動jobは追加しない。

外部のタスク起動基盤から、必要ならsync、次にdailyを実行し、同じDBを使うCodex workerへjp-equity-irの手順を渡す。受信した返信はreply add後にinboxからレビューできる。

CLIはモデルAPIを呼ばないため、シェルでdailyを定時実行するだけでは調査は進まない。Codex workerの起動、モデル利用額、再試行、DBを保持する場所は運用基盤側で設定する。このクラウド作業環境が常時稼働する前提にしない。

複数workerは同じマシン上の同じSQLiteファイルを共有する。別マシンのローカルDBは協調しない。分散運用が必要になった場合は共有DBやタスク基盤へ置き換える。

## 出典付き方針で判断を点検する

[判断方針と採用元](decision-policy.md)を参照する。`reply evaluate` の `precommitted_action` は質問前の分岐の提案、`action` は価格条件も点検した結果である。固定した判断契約がない従来の質問は、モデル更新後も `action: unresolved` と `decision_status: missing_decision_contract` を返す。旧履歴の表示も原文を保持したまま `legacy_branch_only` とする。単体の計算には `decision`、質問の寄与の事前比較には `ir-plan` を使う。

```bash
.venv/bin/ir-agent --db :memory: decision examples/decision.json
.venv/bin/ir-agent --db :memory: ir-plan examples/ir-plan.json
```

両方とも入力を評価してJSONを返す。仮説・質問・評価履歴をDBへ追加する操作や、実際の返信の受信・分岐適用を表す操作ではない。サンプルは架空企業・架空価格・テスト用の任意の閾値であり、投資方針の推奨値ではない。`synthetic_example` 出典を含む設定は `synthetic: true` の入力でしか使えない。

`decision` の入力：

| フィールド | 内容 |
|---|---|
| `as_of` | オフセット付きの評価時刻。日付だけは使わない。 |
| `thesis` | 既存の完全な仮説オブジェクト。記録日時・次回点検日・根拠IDを含む。 |
| `policy` | `id`, `version`, `recorded_at`, `parameters`, `parameter_sources`。設定のスナップショットを結果にも残す。 |
| `context` | `held` 真偽値、レビューした `thesis_status`（intact/invalidated/uncertain）、`information_status`、根拠 `evidence_ids`。 |
| `sources` | 仮説の全根拠と価格根拠の保存済みsourceオブジェクト。同一企業・記録時点での利用可能性を検証する。IR返信の `metadata.information_status` が公開情報の補足であると確認できない場合は保留する。 |
| `quote` | 同じ企業の `company_id`, `source_id`, `price_jpy`, `currency: JPY`, `observed_at`, `retrieved_at`, `price_path`, `observed_at_path`。 |

価格と時刻のpathは保存source内の位置を示す配列。例示では `price_path: ["metadata", "price_jpy"]`、`observed_at_path: ["metadata", "observed_at"]`。JSONとして保存した原文の中を参照する場合も、`["content", "C"]` のように指定できる。価格・観測時刻はそのフィールド、取得時刻はsourceの取得時刻と一致しなければならない。sourceが観測時刻を持たない場合に都合のよい時刻を補わない。`normalize-quote` または `quote from-source` はJ-Quants保存原文の未調整終値Cを正規化する。日足の日付しかない場合は日本時間00時の下限と `observation_precision: day` を保存し、実際の引け時刻とは扱わない。判断方針が明示的に `allow_date_precision: true` を指定した場合だけ受け入れ、鮮度はこの下限から保守的に計算する。元資料と派生資料の連鎖を検証し、派生価格は原文から再生成して照合する。

必須パラメーターは以下の6項目。任意の `allow_date_precision` は真偽値で、指定時は同様の出典が必要。数値の既定値は持たない。[実運用用の未設定ひな型](../examples/decision-policy.template.json)をコピーし、採用する方針に沿って設定する。

| パラメーター | 定義 |
|---|---|
| `minimum_upside_pct` | 新規購入を検討するための、明示した費用控除後の最低期待上昇率（百分率）。安全余裕率とは別の定義。 |
| `maximum_downside_pct` | 提示した全シナリオ内の最低評価額に対する下落率の上限（百分率）。実損失の上限やVaRではない。確率0のストレスも含む。 |
| `entry_cost_pct` | 新規購入にかかる費用率。既存保有には仮想の再購入費用を課さない。 |
| `exit_cost_pct` | 売却費用率。税や市場影響を自動推定しない。 |
| `max_quote_age_seconds` | 評価時点から観測時刻までの許容秒数。取引日数ではない。 |
| `target_scenario` | 退出の目標評価として採用するシナリオ名。 |

各値には `parameter_sources` の同名キーで `kind: user / external_policy / synthetic_example`、`reference`、`rationale` を付ける。出典ラベルの入力だけで採用やその内容の正しさを自動証明するものではない。実際の採用者・採用日時・対象・単位は方針記録に残す。

情報の公開性・仮説の有効性・根拠・価格鮮度を確認した後、反証による退出、目標評価への到達、シナリオのリスク条件、保有継続、新規購入条件の順に点検する。未保有では、期待評価の売却費用控除後の額を購入費用込みの価格と比較する。保有では現在価格を基準とし、新たな購入費用は加えない。目標価格は、選んだシナリオの評価額を売却費用控除後の手取りが満たす価格である。取得原価からの損益計算は行わない。境界の比較には表示用の小数2桁へ丸める前の計算値を使う。

未設定、根拠不足、古い株価、期限到来済みの仮説、曖昧・非公開疑義の情報は `unresolved` と理由を返す。矛盾した企業・時刻・値、不正な設定は検証エラー。形式が正しいことは、仮説や将来予想が正しいことの証明ではない。

`ir-plan` は上記の入力に既存形式の `question` を加える。追加フィールドは次のとおり。

- `question.parameter_paths`：回答で変更を許す入力の一覧。例：`scenarios.base.inputs.eps_jpy`。シナリオ名のドットはこの表記で扱わない。
- `question.public_answer_status: not_found`：公開資料を先に点検して未解決であることを記録する。未記録なら追加レビュー対象。
- 各明確な分岐の `thesis_status`：その回答が得られた場合の仮説の扱いを質問前に固定する。

方針の記録日時は質問作成以前でなければならない。許可していない倍率・確率・入力の変更は保留する。異なる明確な回答が異なる判断を生むなら `decision_distinguishing`、どの明確な回答でも判断が同じなら `no_decision_change`、設定・点検が足りなければ `needs_review`。これは情報価値の金銭的な推定や質問の送信許可を表さない。曖昧・無回答の分岐は評価額を変更しない。

架空の返信を既存ハーネスへ取り込み、価格条件付きレビューまで通す実行例は `.venv/bin/python scripts/demo_ir_decision.py`。メモリ内DBのみを使い、架空の送信済み状態を記録する。外部への送信や注文は行わない。


## 質問前の方針固定と判断履歴

`policy add FILE` は判断方針をID・連番の版で不変登録する。同じ版の同じ内容は再登録でき、内容の変更は次版が必要。実案件では、質問の作成前に登録した方針を使う。記録日時だけを遡って事前採用したことにできない。

```bash
.venv/bin/ir-agent --db PATH policy add POLICY_FILE
.venv/bin/ir-agent --db PATH policy show POLICY_ID --version 1
```

質問JSONに次を追加する。`quote` は上の価格根拠オブジェクトで、資料は先に同じDBへ取り込む。

```json
{"decision_contract": {"policy_id": "ADOPTED_POLICY_ID", "policy_version": 1, "quote": {}, "synthetic": false}}
```

登録時に仮説・保有状態・方針全体・ハッシュ・事前比較を質問へ固定する。回答によって変更を許す `parameter_paths`、公開回答の点検結果、各分岐の `thesis_status` も必要。下書きは不足を記録して保存できる。`mark-sent` は既存の外部送信の記録であり、固定契約付きの質問では、送信時の価格鮮度・保有状態と `decision_distinguishing` を再確認する。古い価格を都合よく更新するため既存の質問を書き換えず、変わった前提を点検する。

返信評価へ任意の `decision_quote` を渡す。公開性を確認した明確な回答は新しい仮説版を追加し、固定方針と実際の保有状態で判断履歴を同じトランザクションに保存する。新しい株価がなければモデル更新は可能だが、判断は `unresolved` とする。無効な価格根拠などのエラーでは更新全体を取り消す。応答が好材料でも価格が既に目標評価に達していれば `exit_review` になり得る。

```bash
.venv/bin/ir-agent --db PATH reply evaluate REPLY_EVALUATION_FILE
.venv/bin/ir-agent --db PATH decision-review show REVIEW_ID
.venv/bin/ir-agent --db PATH decision-review add FRESH_REVIEW_FILE
```

`FRESH_REVIEW_FILE` は `reply_id`, `expected_thesis_version`, `recorded_at`, 任意の `decision_quote` のみを持つ。返信の適用後に相場だけを再点検し、仮説の版や返信適用回数を増やさない。方針の上書きは受け付けず、質問時の方針版を使う。仮説が別の調査で進んでいれば古い返信からの再判定を止める。

保存する判断履歴には、質問・返信・評価・仮説・方針の版、保有状態、入力、出典IDと本文ハッシュ、計算結果、保留理由を含む。架空の一連の操作は `.venv/bin/python scripts/demo_ir_policy_workflow.py` で確認する。外部送信も注文も行わない。

## 窓口台帳と価格根拠の取り込み

```bash
.venv/bin/ir-agent --db PATH contacts import research/ir-recovery-2026-10-13/contact-candidates.csv --dry-run
.venv/bin/ir-agent --db PATH contacts import research/ir-recovery-2026-10-13/contact-candidates.csv
.venv/bin/ir-agent --db :memory: normalize-quote examples/quote-source.json
.venv/bin/ir-agent --db PATH quote from-source MARKET_SOURCE_ID
```

窓口CSVは確認日・引用・条件・原典参照とカタログのハッシュを取り込む。未選別の会社は `watch` であり、IR受付の存在は投資適格性を示さない。既存の会社名・選別・保有を保持し、同じカタログの再取り込みで確認日を更新しない。重複コードや不正な行があれば全体を `needs_review` として書き込みを止める。`quote from-source` は保存済み原文と派生資料を同じDBで参照できる状態にする。

## 質問の情報価値と前向きの観測

[採用した意思決定分析の出典](../research/ir-policy-adoption-2026-10-15/README.md)と[観測設計](ir-outcome-observation.md)を参照する。

```bash
.venv/bin/ir-agent --db :memory: information-value examples/information-value.json
.venv/bin/ir-agent --db :memory: observations summarize examples/ir-observations.json --as-of 2026-10-15T10:00:00+09:00
```

`information-value` は既存の有限状態の意思決定分析に沿い、明示した事前確率・状態別効用・費用・回答の条件付き確率からEVPIとEVSIを計算する。効用と費用は同じ単位で入力し、株価や利益から勝手に変換しない。回答の条件付き確率がなければ `needs_calibration` と完全情報の上限だけを返す。IRが真実を完全に伝えるとは仮定しない。例の確率・効用は架空であり実企業へ流用しない。

`observations summarize` は `records` 配列を持つJSONを入力し、指定時点で見える送信記録・受信確認・返信・後続公開資料による検証を集計する。無回答は期限まで受信を確認した場合だけ分類する。未検証、拒否、送信不明、遅延、途中の事業変化、定義不一致を分け、返信企業だけを母数にしない。同じ定義・対象期間・設計版を持つ群で観測頻度を返すが、この頻度をIRの正確性や将来の尤度として自動採用しない。


## 返信の公開性を訂正する

適用済みの返信も `reply classify FILE` で分類の訂正を追記できる。入力は `reply_id`, `expected_version`（初回0）, `information_status`, `basis_quote`, `rationale`, `recorded_at`。原文の該当箇所と理由を残す。同じ要求は再登録せず、別の訂正は最新の版を確認して追加する。受信原文・適用済み仮説・過去の判断JSONは書き換えない。

```bash
.venv/bin/ir-agent --db PATH reply classify INFORMATION_REVIEW_FILE
.venv/bin/ir-agent --db PATH reply show REPLY_ID
.venv/bin/ir-agent --db PATH decision-review show REVIEW_ID
.venv/bin/ir-agent --db PATH inbox
```

訂正がある判断は現在の表示で `unresolved` / `requires_information_review` とし、元の結果も履歴として確認できる。公開性の分類を戻すだけでは古い株価の判断を復活させず、改めて価格と前提を点検する。訂正の対象になった返信はinboxへ再掲する。後続の価格点検では、その時点で保存済みの分類訂正を依存先の返信も含めて確認する。適用済みモデルの自動差戻しは行わない。activeの会社で最新仮説が訂正対象の返信に依存する場合、`daily` は `reply_information_corrected` を理由に再調査jobを作る。新しい資料と仮説を点検して次の版を作る。

保有状態も初めて観測した日時と変更を保存する。過去時点の保有履歴がなければ `position_history_unknown` として判断を保留し、現在の保有状態を過去へ投影しない。架空の過去例だけは `decision_contract.synthetic_position: {"held": true, "observed_at": "2026-10-09T09:59:00+09:00"}` のように仮定を明示できる。実案件では受け付けない。

## 選別と不足資料の棚卸し

```bash
.venv/bin/ir-agent --db :memory: screen examples/screening.json
.venv/bin/python scripts/report_coverage_gaps.py --db PATH
```

`screen` は会社・評価時刻・保存資料・資料内の実フィールドへ結び付けた指標・明示された採用方針を受け取る。各規則は比較演算、閾値またはbenchmark、単位・定義・対象期間、鮮度条件と出典を指定する。相対比較ではbenchmark側も同じ定義・期間・観測時刻が必要。欠損は補完せず、`needs_policy` / `needs_data` / `unsupported_model` を分ける。条件を満たしても `candidate_for_research` であり、会社statusの自動変更や購入判断は行わない。

[モデル適合の原典確認](../research/valuation-model-routing-2026-10-15/README.md)に従い、金融機関の資本規制、景気循環の正常化、赤字成長の収益化と資金を点検する。業種名で一律除外せず、金融機関のPERも原典に反して禁止しない。必要な専用評価モデルは別途確認する。

`report_coverage_gaps.py` はSQLiteをread-onlyで開き、利用可能な公開資料・財務分類・相場・仮説・会社別の方針参照と欠損を全社分返す。保存済み資料だけを使い、全社への再アクセスはしない。未分類の公開資料は財務が検証済みとは数えず、内容分類を次タスクとする。policy registryが存在しても全社へ自動採用しない。未提供のセクションはnull、存在する空の台帳は0と区別する。


## 観測設計を事前登録し、結果を追記する

JSONファイルからの集計に加え、同じDBへ観測の初版と結果の各版を保存できる。`register` は単一の観測recordを受け取り、初回保存時刻と設計ハッシュを保持する。`append` は同じ設計を持つ完全な次版recordと期待版を受け取る。仮説、状態・信号の定義、対象期間、期限、前提資料、事前確率等は変更できない。

```bash
.venv/bin/ir-agent --db PATH observations register DESIGN_FILE
.venv/bin/ir-agent --db PATH observations append NEXT_SNAPSHOT_FILE --expected-version 1
.venv/bin/ir-agent --db PATH observations show OBSERVATION_ID
.venv/bin/ir-agent --db PATH observations summarize --as-of OFFSET_DATETIME
```

返信と外部変化は末尾にだけ追加する。受信確認と検証ラベルの訂正も新しい版へ保存し、過去の版は残す。実案件の観測を送信・返信・結果判明後に初めて登録し、事前に設計済みだったと扱うことはできない。架空の過去例はsyntheticを明示する。実案件・架空例とも未来の返信や結果を記録しない。

DBからの集計は各版の実際の保存時刻でも `as_of` を制限する。後から記録した検証結果を、当初から知っていたことにしない。記録数は尤度の校正成功を意味しない。返信・外部変化そのものの分類訂正を参照するイベントschemaは未実装のため、既存のイベントを書き換えず未解決を保持する。返信の公開性訂正台帳と観測台帳の照合も別途必要である。


## 訂正を日次の再調査へ回す

`daily` は最新の時点仮説と原典参照の連鎖から依存する返信を調べ、未点検の分類訂正があれば新着開示と同じ運用上の優先度で調査へ回す。packetの `information_reviews` にその時点で保存済みの履歴、`new_information_review_refs` に今回扱う最新の訂正版を固定する。訂正が後で追加されても、確保済みpacketへ混ぜない。

訂正がある調査の結果JSONには `information_review_refs: [{"reply_id": "REPLY_ID", "version": 1}]` を追加し、今回の全訂正を扱う。packet外の版や重複、未対応の訂正があれば完了を拒否する。次の仮説版・job完了・点検済み記録は同時に保存する。後続の訂正は別のjobになる。訂正の点検完了は公開性の自動的な肯定や、以前のモデルへの差戻しを意味しない。

inactiveの会社や、最新の仮説が当該返信へ依存しなくなった会社は、訂正だけを理由にactiveへ変更しない。以前の判断の保留表示と原文はそのまま残す。


## 投資仮説を作る前の資料分類

```bash
.venv/bin/ir-agent --db PATH intake --limit 10
.venv/bin/ir-agent --db PATH claim --worker classification-worker --measurement-kind observed
.venv/bin/ir-agent --db PATH packet JOB_ID
.venv/bin/ir-agent --db PATH complete JOB_ID --worker classification-worker --expected-attempt ATTEMPT --result CLASSIFICATION_FILE
.venv/bin/ir-agent --db PATH source-classification SOURCE_ID
```

`intake` は数値仮説がなくても、保存済みの未分類の公開資料から `kind: intake` / `stage: source_classification` の固定packetを作る。`watch` の会社も扱えるが、会社をactiveにしたり仮説を補ったりしない。既存researchと同じ会社単位のleaseを共有し、原文とsnapshotのハッシュを照合する。新しい資料は確保済みpacketへ混ぜない。

`intake --new-only --limit 10`も新規jobだけを上限へ数える。既存triggerをskippedへ返し、jobs_createdと新規繰越を明示する。無指定のselected再表示契約は保持する。[旧modeとの両立検証](../research/ir-new-only-queue-integration-2026-10-15/README.md)を参照。

`CLASSIFICATION_FILE` は `classifications` 配列だけを持ち、各項目に `source_id`, `expected_version`（初回0）, `kind`, `financial_content`, `basis_quote`, `rationale` を指定する。全packet資料を一度ずつ扱い、引用は原文のまま残す。kindはfinancial_statement / earnings_presentation / business_description / qa / schedule / contact_conditions / shareholder_policy / index_only / other / unresolved。財務に関する内容の有無はtrue/false/nullを区別し、タイトルだけで判断しない。これは実績・予測の数値やモデル入力を検証した記録ではなく、`inputs_verified: false` のまま保存する。

`complete` はpacket種別を識別し、初期分類では数値仮説の追加を要求しない。分類と完了は原子的に保存する。`report_coverage_gaps.py` は分類の保存時刻も確認して内容カバレッジを集計し、元source本文やmetadataを変えない。`daily` は従来どおり投資仮説のあるactive会社の点検を扱う。

## 日次処理の能力を測る

```bash
.venv/bin/ir-agent --db :memory: capacity examples/work-measurements.json
```

[計測契約](capacity-measurement.md)に従い、実際の段階・attempt・worker・開始終了時刻・実作業時間・利用量を記録する。架空サンプルは動作確認専用。欠損を0にせず、経過時間を実作業時間へ変換しない。同じworkerの重複時間、失敗、再試行、窓を跨ぐ作業を分ける。会社数の上限は自動外挿せず、実測した完了件数と不足する観測を返す。


## 原典に基づく配当割引モデル

```bash
.venv/bin/ir-agent --db :memory: value examples/dividend-valuation.json --price 200
```

この例のDPS・資本コスト・成長率・価格・確率は架空の検証値で、実運用の推奨値ではない。Damodaranの2段階DDMに沿い、予測期の資本コストで配当と終価を割り引き、終価分母には安定期の資本コストを使う。翌期DPSも両コストも必須で、自動補完しない。結果は1株当たりJPYで、cash/debt/sharesを混ぜて再調整しない。

質問の `parameter_paths` には、例えば `scenarios.base.inputs.dividends_per_share_jpy.0` や `scenarios.base.inputs.terminal_dividend_per_share_jpy` を指定する。回答から変えると約束した入力だけを適用し、資本コスト・永久成長率まで無断で変えない。既存の方針固定、価格点検、判断保存も同じように使う。実績配当から将来配当や配当可能額を自動推定せず、持続性・規制資本・買戻し・希薄化等の必要な前提を別途確認する。


## モデルに使う数値の出所を点検する

```bash
.venv/bin/ir-agent --db :memory: model-inputs examples/model-input-review.json
```

`model-inputs` は `as_of`, `company_id`, `valuation`, `sources`, `provenance`, 任意の `synthetic` を受け取る。計算器が実際に使う全数値path（シナリオ確率も含む）を列挙し、各pathの由来を点検する。`provenance` の各記録には `kind`, `reference`, `rationale`, `recorded_at`, `author` と、必要に応じ `source_id`, `value_path`, `unit`, `period` を指定する。

kindはreported_fact / issuer_guidance / external_estimate / explicit_assumption / synthetic_example。事実・会社予想・外部予想は、保存sourceの実フィールド位置を `value_path` で示し、その値と入力を照合する。同一企業、記録以前の取得、原典の連鎖、公開性も点検する。PDFの語句から都合よく数字を抽出したり、1期の会社予想を将来DPS列やシナリオ確率へ補完したりしない。明示仮定はauthorと理由を保存し、事実の数値一致とは区別する。

unweightedでは未設定の確率を `unset_probability_paths` に分け、`expected_value_available: false` を返す。未設定確率に数値の出典を付けたことにはしない。原典の一つでも `metadata.synthetic: true` なら、syntheticでない監査は保留にする。派生資料をreported_factへ再分類しただけで架空の原典を実資料へ昇格させない。

結果は `needs_review` / `source_values_matched` / `assumptions_declared` / `synthetic_example`。数値一致は単位・対象期・連結範囲・定義・予想の著者を意味上も検証したことではないため、常に `meaning_review_required: true` / `financial_inputs_verified: false` を返す。市場価格の鮮度やDBの最新の分類訂正をこの単体ファイル監査だけで確認済みとしない。数値や投資方針を採用する操作、仮説の保存、IRの適用とは別である。


## 確率を設定しないシナリオ計算

```bash
.venv/bin/ir-agent --db :memory: value examples/unweighted-valuation.json --price 100
```

`valuation.aggregation: unweighted` を明示すると、scenario.probabilityは省略またはnullだけを受け取る。各シナリオの評価額・上昇率、提示範囲のmin/maxと下落幅を返し、`expected_value_jpy` と `expected_upside_pct` はnullにする。均等重みや単純平均を補わない。省略または `aggregation: weighted` は従来どおり確率の厳密合計1を必要とする。

unweightedの仮説も保存できる。固定方針と必要な価格・根拠があれば、既存の反証・目標到達・提示シナリオの下落幅による点検は続けられる。期待上昇余地を必要とする新規購入条件は `scenario_probabilities_not_configured` で保留する。未設定の期待値に依存するmetricはnullであり、0や不合格値として扱わない。[流れと入力の関係](ir-decision-flow.md)も参照する。

## 公表数値の原文を保った構造化

```bash
.venv/bin/ir-agent --db :memory: normalize-facts examples/disclosed-facts.json
```

`normalize-facts` は `source`, `review`, `facts` を受け取り、元資料と別IDの構造化資料を含むbundleを返す。DBへの取り込みや仮説の作成は行わない。原文の数値文字列、逐語引用、単位・期間ラベル、概念・対象範囲・分類、抽出担当者を保持し、明示的な単位換算だけを行う。対応はJPY、JPY-per-share、ratioで、例えば百万円から円、%から比率へ換算する。欠損・空欄・ダッシュを0で埋めない。

各factは `id`, `concept`, `kind`, `raw_value`, `raw_unit_label`, `unit`, `raw_period_label`, `period`, `basis_quote`, `definition`, `scope` を持つ。kindは `reported_fact`, `issuer_guidance`, `external_estimate`, `general_explanation`。periodは空でないオブジェクト、scopeは文字列または空でないオブジェクト。任意の `location` は空でないオブジェクトで、HTMLなら見出し・行・列をdescription等へ記録する。`pdf_page` を指定した場合は、保存本文の改ページと引用位置も照合する。

外部レポートでは、会社予想の転載を `issuer_guidance`、著者自身の予測を `external_estimate` として区別する。`basis_quote`、`definition`、`scope`、元sourceのmetadataに作者と原表の予測ラベルを保持する。`review.author` は抽出担当者で、予測の作者とは別である。原文上の帰属と表の列対応は担当者の意味判断として残り、kindの指定や引用一致だけで自動検証済みにはならない。表のヘッダと備考が必要なら、それらを含む連続した逐語引用を使い、離れた引用を結合して原文と扱わない。

同じ対象年度の旧予想と修正予想も、別IDと版・参照発表日を保つ。[1518の実例](../research/ir-case-studies-2026-10-15/1518/guidance-revision-facts/README.md)では、同じ通知に載る旧/新EPSと年間DPSを別factとし、旧値が過去にシステムで利用可能だったことへ遡及しない。原表が円・銭の複合表記なら、存在しない小数tokenへ改変しない。同例のDPSは00銭を人が確認した限定抽出であり、normalizerが銭を解析する機能や非ゼロ銭の処理を追加した意味ではない。

原典の初回取得日時は保持し、派生資料の取得日時は実際の処理日時にする。単位・期間・連結範囲・表の列・数値の概念がモデルと合うかは意味の確認として残し、`financial_inputs_verified: false` を維持する。会社の年間配当予想を将来DPS配列へ自動採用しない。[千葉銀行の保存原文による例](../research/ir-case-studies-2026-10-15/8331/extraction-notes.md)を参照する。

## 複数原典の来歴

複数資料から作った派生sourceは `metadata.original_source_ids: [SOURCE_ID, ...]` で全原典を示す。既存の `metadata.original_source_id` と併用でき、両方に同じIDがある場合は一つの依存として扱う。配列内の重複、不正な型・空文字は拒否する。

投資判断・質問契約・公開性訂正の再調査ではすべての親へ遡る。一つでも別会社、未取得、評価時点後、公開性未確認の原典があれば、その不備を単一の派生資料で隠せない。共有原典を持つ正常なDAGと循環を区別する。原典が一つのJ-Quants正規化は既存の契約を維持する。

`model-inputs` が既知の公表数値正規化providerを参照する場合は、元の本文から引用・数値・換算を再現する。派生値とモデル値を同時に変えても原文と合わなければ保留とし、実績・会社予想・外部予測の構造的な分類矛盾も検出する。本文の再現と、保存時に既定欄が追加され得るsnapshot全体のSHA確認は別に報告する。未知providerにこの形式を推測して適用せず、既知providerの未対応版は保留する。

## 観測中の返信・外部変化の分類を訂正する

観測の `assessments` 配列へ訂正を追加し、既存の `observations append FILE --expected-version N` で保存する。[契約](observation-corrections-design.md)に対象snapshotのSHA、対象別版とCAS、担当者、理由、原文と公開根拠の参照を定義する。元の返信・発生日・受信日時・事前定義・期限・旧版を編集せず、集計viewだけ有効な分類へ切り替える。

保存済みSQLiteの返信・質問・会社・受信時刻・本文SHA・逐語引用を独立に照合する。公開根拠は本文とsnapshotのSHA、全原典の企業・公開性・時点・公開性訂正を確認する。根拠不足の場合に保存できるのは、信号を変えず公開性を保留へ戻す訂正、または外部影響を未解決とする訂正だけ。callerが新規訂正に照合済みmetadataを自己申告することはできない。

```bash
.venv/bin/python scripts/demo_ir_observation_workflow.py --with-correction
```

この架空例は訂正前の有効件数1、訂正後0、原返信不変を示す。台帳の過去集計は実際の保存時刻でも制限され、後の訂正を過去へ遡らせない。観測の訂正はHarness側の投資判断・公開性台帳を変更せず、現在の記述的集計を予測精度の実証へ自動転用しない。

## 明示した確率予測の採点

```bash
.venv/bin/ir-agent --db :memory: score-probabilities examples/probability-scoring.json
```

`score-probabilities` は `categories`, `probabilities`, `observed_category`, `prediction_ref`, `observation_ref`, `definition_ref` の6項目を受け取る。全カテゴリの確率を明示し、0以上1以下・合計が正確に1であることを確認する。Gneiting–Rafteryの原式の符号を反転した多カテゴリBrier lossと、自然対数のlog lossを返す。[原典と尺度](probability-scoring.md)を参照する。

観測カテゴリへの確率0は `log_loss: {status: positive_infinity, value: null, unit: nats}` とし、epsilonや有限値で置き換えない。これは観測や値の欠損とは違う。Brierは全カテゴリの二乗誤差和で、二値のscalar定義の2倍になる。

出力は常に `calculation_only`。refは文字列として保持するだけで、この純粋計算器は予測が回答前に保存されたこと、対象観測の適格性、状態ラベルの独立性、モデルの校正を確認しない。実観測台帳からの採点対象選択と予測の事前保存は別の接続が必要である。合格閾値、尤度学習、母集団の精度、投資成績は算出しない。

## 候補となる信号予測を回答前に固定する

```bash
.venv/bin/ir-agent --db PATH predictions register PREDICTION_FILE
.venv/bin/ir-agent --db PATH predictions show PREDICTION_ID
.venv/bin/ir-agent --db PATH predictions list --as-of OFFSET_AWARE_TIMESTAMP
```

[保存契約](probability-prediction-storage.md)に従い、既存観測のID・版・snapshot/designのSHA、モデルID/版、学習情報締切・学習完了・予測生成の時刻、model/training manifestとSHA、全signal×stateの `likelihoods[signal][state]`、出所とsynthetic区分を明示する。未設定値の[ひな型](../examples/probability-prediction.template.json)は、そのまま投入できる予測ではない。確率を補って登録することはしない。

実案件では現在の未送信・未返信・未判定の観測設計へ登録し、実際のDB保存時刻を保持する。モデルの同じID/版でmanifestや学習内容を付け替えず、新版を使う。同ID・同要求の再送は、後で観測が進んでも最初の保存結果を返す。

登録結果は `candidate_prediction_only`。manifestのhash一致と、学習履歴・情報利用時点・校正の実証は違う。`training_provenance_verified` と `calibration_verified` はfalseを維持する。実観測の選択・採点、後日分類訂正による漏洩の点検、EVSIへの採用は[次の接続](probability-prediction-contract.md)として残る。候補予測の保存数を調べる `status.signal_predictions` は、校正済みモデル数や実返信数ではない。


## 保存予測と観測の準備状況を読み取り専用で点検する

```bash
.venv/bin/python scripts/report_prediction_readiness.py --db PATH --as-of OFFSET_AWARE_TIMESTAMP
```

[準備状況の契約](prediction-readiness.md)に従い、観測を母集団として予測を左結合する。予測なし・未送信・未判定・保留を消さず、後追いで保存された実送信・受信時刻が予測より前だった場合を検出する。分類訂正・無回答・外部影響は既存観測viewを使い、state判明後のsignal変更は漏洩候補として残す。

このscriptはStoreを初期化せず、SQLiteをmode=ro/query_onlyで開き、一貫したsnapshotを読む。table欠落による未知と、tableがあって0件である場合を区別する。出力は `prediction_readiness_only`、個別の最大状態も `needs_evidence_binding_review`。採点・根拠の独立照合・学習来歴・校正を済ませたことにはせず、scorerも呼ばない。


## 将来のジョブ試行を記録する

claimは将来の成功した確保から、leaseの開始・更新・完了・観測した期限切れを別履歴へ保存する。研究結果・資料分類と同じトランザクションで保存し、失敗した完了を計測上だけ成功にしない。旧ジョブには開始時刻を補わない。

`claim --measurement-kind observed` は運用者が実際の処理と明示する場合、`synthetic` は架空検証の場合に使う。省略時の `unknown` は区分不明で、観測cohortへ混入しない。この指定は計測の来歴であり、金融入力や分析内容を検証済みにするものではない。Pythonの `Harness.claim(..., measurement_synthetic=False / True / None)` が対応する。

lease経過はactive分析時間や全工程の所要時間と異なる。最小実装ではactive・tokens・費用はnull。claim/renewの要求receiptは[任意の要求ID付き契約](idempotent-job-requests.md)として接続した。IDなし旧呼出へ通信再送の保証を広げない。[標準の根拠と計測契約](job-attempt-measurement.md)を参照する。


## 過去時点の仮説と再研究を分ける

[保存来歴と二時刻の契約](historical-availability-design.md)に従い、`thesis --as-of` とdaily/claim/intakeでは、資料の申告日時だけでなくその時点のDB存在を照合する。後から取り込んだ古い日時の情報を当時から利用できたことにしない。

`thesis-view COMPANY_ID --as-of TARGET --knowledge-at TARGET --mode pit` はstrictな表示と不足理由を返す。`--mode retrospective --knowledge-at LATER_TIME` は後着情報を含むread-only再研究で、二締切を明示する。来歴不明と「当時データがなかった」は異なるため、recordだけでなくavailability_status/excludedも確認する。架空demoは過去のruntime時計を明示しており、実保存履歴の証明ではない。


## 保存した判断を現在の価格条件で表示する

[現在表示の価格鮮度](current-price-views.md)に従い、返信評価/価格reviewの返却とshow/inboxは実行時計でも既存の価格有効期限を点検する。歴史resultは保持し、期限切れは現在actionをunresolvedへ、inboxをrequires_price_reviewへ回す。新しいquoteで新reviewを作り、同じ返信を再適用しない。

情報訂正と価格再点検は併存する。`current_quote_check: fresh` は時間条件だけを指す。元の保存結果・現在表示・新しい再点検結果を区別し、表示時刻の変化を新しい仮説版と数えない。


## 保存予測の原文を採点前に照合する

```bash
.venv/bin/python scripts/report_prediction_bindings.py \
  --db PATH --bindings BINDINGS_JSON --as-of OFFSET_AWARE_TIMESTAMP
```

[原文照合の契約](prediction-evidence-binding.md#接続した最小apiとcli)に従い、観測版と明示mappingを指定する。省略時も全観測を残して不足を返す。元のquestion/reply、全親source、SHA/引用/保存来歴と公開性の過去/現在を分けて点検する。`source_binding_report_only`は採点許可ではなく、state意味・独立性・訓練・校正はunknown、scoreはnull。実案件の出力は私的本文を含み得るのでGit対象外のdata/へ保存する。


## 評価手順を不変の宣言として保存する

```bash
.venv/bin/ir-agent --db PATH evaluation-protocol register FILE --expected-previous-version 0
.venv/bin/ir-agent --db PATH evaluation-protocol show PROTOCOL_ID
.venv/bin/ir-agent --db PATH evaluation-protocol history PROTOCOL_ID
```

[記録契約](evaluation-protocol-design.md#接続したrecord-only-registry)は版/CAS/再送を保持する。空欄を補わず、返却protocol_commitment_onlyは事前性・独立性・規則妥当性・採点許可を確認しない。既存の原文照合、観測、予測、投資方針へ自動適用しない。


## 数値thesis前の定性レビューjob

明示caseの新資料・管理日を既存leaseへ接続する場合は[定性レビューの手順](qualitative-research-jobs.md)を使う。`qualitative_review` packetは金融researchやintakeと別の結果契約で、金融入力・投資action・正式IRを補完しない。既存の数値thesisを使う通常dailyも保持する。

## 金融機関の規制資本FCFEの中間計算

`ir-agent regulatory-fcfe examples/regulatory-fcfe.json`は、明示した年次NIと規制資本再投資を同じ主体/株主/通貨/単位で差し引く。DBを開かず、負値を切り上げず、資本政策・再投資予測や終価/株価を作らない。出典は未検証、採用は未解決のまま保持する。[入力契約](regulatory-fcfe.md)を参照。
