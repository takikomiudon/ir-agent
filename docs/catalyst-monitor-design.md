# 公表予定と結果資料を分ける材料監視：最小設計

本書は設計であり、実装・DB移行・予定の登録は行っていない。目的は、数カ月〜1年の研究で「次にどの公表資料を確認するか」を整理すること。予定が来ただけで発表済みとせず、発表を確認しても仮説成立や売買判断へ自動変換しない。最初の成果物はread-onlyのmonitor outputだけとする。新しいGET、通知、日次job、仮説、IR質問、発注は追加しない。

## 保存原典とプロジェクトへの適応

Anthropicの[catalyst-calendar原文](../third_party/anthropic/skills/catalyst-calendar/SKILL.md)を全文読み、以下を確認した。[manifest](../third_party/anthropic/manifest.json)の固定commitは `574ed3624aebd0418c7e96cd101262f30210ab26`、取得は `2026-10-10T15:54:00.343952+00:00`、3,111 bytes、SHA-256は `12ac4ae7659ab848a8910dfceadab5b21479f23c8d3e0c57a3f5bf814bcf8186`。保存ファイルのバイトhashも一致した。参照資料として読み、原文のメール・外部カレンダー連携等は実行していない。

| 原文位置 | 保存原文の引用 | 採る手順 |
|---|---|---|
| Step 1 | “List of companies to track (tickers or names)” / “Time horizon (next 2 weeks, month, quarter)” | 対象会社と表示期間を明示する。原文の期間例を既定値にはしない。 |
| Step 2 | “Quarterly earnings date and time (pre/post market)” | 決算発表を材料として、日付と時刻の有無を保持する。説明会と別イベントにする。 |
| Important Notes | “Earnings dates shift — verify against company IR pages and Bloomberg/FactSet closer to the date” | 予定が変わる可能性と再確認の必要を残す。何日前という固定値や、追加サービスの契約は導入しない。 |
| Important Notes | “Archive past catalysts with the actual outcome — builds pattern recognition over time” | 予定、実施を支持する資料、結果資料の対応を後から辿れるようにする。結果から元予定を書き換えない。 |

下記のschema、時点・保存来歴の点検、浮動日付、差分hash、保留状態は本プロジェクトの適応である。原文がこれらの完成したソフトウェア仕様を提供したとは表現しない。原文の影響度H/M/Lやpositioningの欄から、独自の優先度・売買方針は作らない。

## 既存機能との境界

- [thesisの契約](workflow.md)は `catalysts` を補足情報として保存できるが、[validate_thesis](../src/ir_agent/models.py)はそのイベント構造・日程変更・実施を検証していない。自由記述を自動で正式予定へ移さない。
- [Harness.daily](../src/ir_agent/harness.py)はactive会社の利用可能な仮説・未点検source・情報訂正・`next_review_date`から既存の研究jobを作る。材料予定の到来を契機にする実装ではない。monitorはwatch会社・仮説なしの記録も表示できるが、active化やjob作成は行わない。
- `next_review_date`は既存のJSTによる仮説点検期限。会社のイベント日付とは別であり、monitorが期限を書き換えたり、予定日をそこへ代入したりしない。
- source到着の検出・分類・保存来歴は既存の[availability](../src/ir_agent/availability.py)、[intake](../src/ir_agent/intake.py)、[source_origins](../src/ir_agent/models.py)を再利用する。監視用の新receipt台帳や分類器を作らない。
- 財務値の抽出やモデル採用は既存normalizer/model-inputs/判断系の仕事。monitorは「この資料をどの論点について読むか」までで止める。

## 実例：ニッスイの保存済み公表予定

[保存レビュー](../research/ir-case-studies-2026-10-15/1332/statement-calendar-followup/review.json)と[原source bundle](../research/ir-case-studies-2026-10-15/1332/statement-calendar-followup/source-bundle.json)を起点にする。カレンダーsourceは `case-public:4ca42c264c3f7af4506f664ad01edbcf4c738bf920ea3efcd32a686fabec4edb`、URLは `https://www.nissui.co.jp/ir/calendar/index.html`、初回取得は `2026-10-15T04:22:56.478724+00:00`、`published_at:null`。raw SHAは `ac2bc17427bf1a8cf5fc149ac59ec0b3ca147b85f193a71bfb95c05fbd2122b8`。

保存原文 `calendar-year-and-events`、文字位置 `2668:2891`：

> IRカレンダー 都合により変更する場合があることを、予めご了承ください。 最新情報 2025年度 2024年度 2023年度 2022年度 2021年度 2026年度（令和8年度） 2026年4月～2027年3月 日程 タイトル 関連資料ダウンロード その他コンテンツ 02月05日（予定） 2027年3月期第3四半期決算発表 11月10日（予定） 2027年3月期第2四半期決算説明会 11月06日（予定） 2027年3月期第2四半期決算発表

| 別々に保持するイベント | 対応する暦日 | 時刻 | 会社日程のtimezone |
|---|---|---|---|
| 2027年3月期第2四半期決算発表 | 2026-11-06 | null | null / 未確認 |
| 同第2四半期決算説明会 | 2026-11-10 | null | null / 未確認 |
| 同第3四半期決算発表 | 2027-02-05 | null | null / 未確認 |

年は「2026年度、2026年4月〜2027年3月」と月日の対応から記録者が解釈したもの。年次対応の根拠引用も残す。2月を2026年にしない。日本企業であることだけから日程のtimezoneをAsia/Tokyoと確定しない。11月6日の予定を11月10日の説明会の実施根拠へ使わない。

同社1Q短信の「四半期連結キャッシュ・フロー計算書は作成しておりません」は保存済み事実であり、次回資料で確認する論点にできる。ただし、2Qで必ずCFが公表される、数値が改善する、予定どおり発表されるとは記録しない。今回のmonitor設計は将来の実施や2Q資料を確認していない。

## 最小API案

```python
report_catalysts(
    connection,
    event_requests: list[dict],
    *,
    as_of: str,
    now: str,
    calendar_window: dict | None = None,
    previous_report: dict | None = None,
) -> dict
```

同じSQLiteのsources、record_availability、source_classifications、必要な公開性訂正を読む。DBを書き換えるStore constructorやDDLは呼ばない。読取adapterは既存RecordAvailability.atとsource_origins等を再利用し、全親の会社・時点・公開性・synthetic区分を点検する。構造は既存read-onlyレポートと揃え、同一snapshotで読み、外側transactionをcommit/rollbackしない。CLI化する段階でmode=ro/query_onlyを付ける。今回はAPI設計まで。

`as_of`と`now`はoffset付きの厳密timestampだけ。`as_of<=now`を要求し、APIのas_ofで既存cutoffの日付→JST日末変換を呼ばない。`now`は実行器が取得する実時計、テストだけ注入可とする。`calendar_window`は表示用 `{date_from,date_through}` の明示された暦日範囲で、時点のcutoffとは異なる。nullなら全イベントを表示する。範囲外や日付不明のイベントも別欄に保持し、集計母数から消さない。

`event_requests`は記録者が作る以下の構造だけを許す。日程mappingはこの実行時に渡された解釈であり、過去に事前登録されていた証明にはならない。初版は `mapping_prospectiveness:unverified` 固定。手動の `first_saved_at` や `verified:true` を入力してこの制限を解除できない。

| 欄 | 記録者が入力するもの |
|---|---|
| `id`, `company_id`, `synthetic` | 明示イベントID、会社ID、架空/実案件の区別。IDだけで同じイベントと判定しない。 |
| `kind`, `label`, `period` | 初版kindは `earnings_release` / `earnings_presentation` のみ。対象期は原文ラベルを含むdescriptor。発表と説明会、2Qと3Qを分ける。 |
| `claims[]` | `id`, `kind`, `source_id`, `source_snapshot_sha256`, `basis_quote`。sourceのURL/会社/時刻はDB原文から読む。入力された自己申告の上書きを許さない。 |
| schedule claim | `kind:schedule`, `raw_date_label`, `date`, `time:null|時刻`, `timezone:null|明示されたzone`, `date_context_quote`, `supersedes_claim_id:null|id`。延期・変更は元claimを残す新claimとし、根拠が「変更」を支持するか別レビューを残す。 |
| cancellation claim | `kind:cancellation`, `supersedes_claim_id`。資料から予定が消えただけで取消と記録しない。 |
| occurrence claim | `kind:occurrence`, `occurred_at:null|offset timestamp`, `occurred_on:null|暦日`, `explanation`。実施を支持する文言・表題・対象期を引用し、記録者が対応理由を説明する。 |
| `result_links[]` | 対象sourceとsnapshot SHA、引用、対象期の対応理由、`role:financial_result|presentation|qa`。その資料をこのイベントの結果として読むという手動対応を記録する。 |
| `followup_topics[]` | 原文参照付きの、次の公開資料で確認する論点。数値予測・モデル更新・質問送信の命令を入れない。 |

scheduleの `time` と `timezone` は両方既知の場合だけ絶対時点を作れる。時刻だけ既知なら原文を保持し、絶対時点はnull。明示されたIANA timezoneがある場合でもDSTで曖昧/存在しない時刻は自動補正せず保留する。claim ID重複、別会社の親、循環supersedes、非対応kind、bool/list等の不正型、無効日付・非有限JSONは通常のValueError。参照source欠損やtable不足はイベントを落とさずunknownで返す。

## 独立した出力状態

トップレベルは `status:monitor_only`、`as_of`、`checked_at`、`coverage`、`events`、`limitations`。`source_sections`に `available|missing_table`、既知の行数を出す。既知空0とtable不在nullを区別する。入力0イベントも正常だが、「全社に予定なし」の認定ではない。

イベントごとに次を分ける。一つの総合trueでまとめない。

| 出力 | 状態/意味 |
|---|---|
| `source_binding` | `matched|mismatch|unknown|unavailable`。SHA・引用・会社・来歴の機械的一致。日程や実施の意味を正しいと認定したことにはしない。 |
| `historical_usability` | as_ofの資料・初回保存/known-by・当時分類/公開性。理由と使用/保留claimを併記。 |
| `current_use` | nowで見える保留/訂正。過去の原文・当時viewを変更せず、現在利用を別に止める。 |
| `schedule` | `supported_claim|conflicting_claims|cancelled_claim|unknown`。選んだclaimと旧claimを返す。根拠不明な後続claimを最新版というだけで採用しない。 |
| `timing` | `exact_instant|floating_date|unknown`。`scheduled_at`、`scheduled_date`、timezone、`relation_to_as_of`を別々に返す。 |
| `occurrence` | `supported_claim|not_established|conflicting_claims|unknown`。支持引用があっても `semantic_review_required:true` を保つ。 |
| `result_documents` | `available_candidates|held|unknown|none_linked`と各linkの来歴。none_linkedは会社が資料を出していないという意味ではない。 |
| `change_check` | `initial|changed|unchanged|baseline_unusable`、変化種別とfingerprint。時計の進行と新根拠/対応変更を区別する。 |
| `followup_topics` | 未解決の公開資料確認論点。存在するだけでは追加調査やIR質問を起動しない。 |

`exact_instant`では明示予定時刻との前後だけ計算できる。予定時刻に達しても `occurrence:not_established` のまま。`floating_date`では `relation_to_as_of:unknown_timezone`、`due:null`。UTC日末、JST日末、取引所引けを補わず、表示期間内かを暦日文字列として並べるだけにする。過ぎたように見える暦日でも「未発表」「延期」「期限超過」を確定しない。

結果資料の到着は「保存資料に新しい候補がある」という事実。予定発表と同じ会社/期の財務資料が来ても、結果linkだけで実施を自動確定しない。実施を支持する引用をoccurrence claimにも明示した場合だけ、その主張を別出力に載せる。資料の引用一致は意味上の支持・イベント実施時刻・財務値採用まで証明しない。

## 時点、後着、分類未確認、訂正

1. as_ofより未来の公表/取得、trusted first_saved_at/known-byは当時viewに利用しない。published_at不明は取得前に使わない。source receiptのlegacy_presenceは正確な初回保存に変えず、既存RecordAvailabilityのunknown/available条件を維持する。
2. 本文日付が過去でも後着保存なら、過去as_ofでは保留。次回現在レポートでは候補にできるが、当時知っていた予定や実施へ遡及しない。
3. classificationはrecorded_atとfirst_saved_atの両方がcutoff以前の最新版本を使う。未分類/unresolved/必要kindと不一致は `needs_classification_review`。本文到着、分類済み、日程の意味確認を同一にしない。
4. source_typeがpublic_disclosureというだけで全親の公開性を省略しない。引用元にir_reply等がある場合、既存の公開性訂正を当時/現在で別に見る。最新の保留を古いmapping時刻で回避しない。実案件へsyntheticの第二原典を混ぜない。
5. 将来のsourceや引用を持つ無効claimも診断対象として残すが、schedule/occurrenceの採用根拠へ混ぜない。未解決・欠損が全イベントを消すフィルターにならないようにする。
6. データ欠損tableを作らない。source原文全文や機密reply原文をレポートへ複製せず、ID/hash/位置/短い公表引用/理由だけを出す。

## 変化なしの扱い

fingerprintはイベント識別、明示claimとresult linkの内容、参照snapshotと選択されたclassification/公開性・availability結果の根拠版をcanonical JSONで計算する。checked_atや出力順、時計だけで変わる文言は材料の変化に含めない。source URLが同じでも本文snapshotが変われば差分候補。同じ本文の再保存や、同じ予定を裏付ける追加sourceは証拠差分として表示できても予定変更とはしない。

`previous_report`は任意の比較用artifactで、入力母集団/設定/schema/参照as_ofが比較可能な場合だけイベントIDごとに比較する。過去版の真正性や事前保存を証明する台帳ではない。不一致や欠損はbaseline_unusable/initial。比較artifactの自己申告で現在のsource保留を解除しない。monotonicな比較時点を要求し、過去向き比較でunchangedを偽装しない。

同一根拠・同一mappingなら `unchanged` とし、`detail_research_requested:false` 固定。現在の保留発生、資料到着、日程変更、mapping訂正は理由付きchangedとして人が読む。初版はchangedでも自動jobを作らない。直前再確認が必要という原則は残すが、1日前等の任意の実行日・強制再GET間隔は足さない。

## 有限の受入ケース

| ケース | 期待結果 |
|---|---|
| 保存1332日程3行、正しい年次引用、実施根拠なし | 3イベントを別表示。11/6、11/10、翌年2/5はfloating_date。occurrenceはnot_established。 |
| 11/6 UTC 00:00とJST 00:00にまたがる実行 | timezone不明の予定は両方due:null。日付到来だけで実施/延期を作らない。 |
| 合成例でtimezone/時刻を原文が明示、予定時刻ちょうど | relationはat_or_afterになり得るが、実施根拠なしならnot_established。 |
| 新原典が11/6→11/9の変更を明示 | 両claimを保持し変更参照を表示。旧as_ofは11/6、現在は支持された11/9。単なる並立矛盾はconflicting_claims。 |
| 再取得で日程行が消えた、又は取得失敗 | 取消/延期を確定しない。既存日程と未確認事項を残す。GETの失敗診断自体はmonitorの仕事外。 |
| 新しい2Q資料を保存したが分類なし | 到着候補は見えるがheld。occurrenceや結果資料の検証済みにしない。 |
| 会社/期が合う2Q資料だけをresult linkへ指定 | available_candidatesになってもoccurrenceはnot_established。明示occurrence claimでのみ支持主張を表示。 |
| 11/6公表と書かれた資料が11/8に初回保存 | 11/7 strict as_ofでは利用不可。11/8以後は新候補で、11/6に知ったことにしない。 |
| 日付不明公表、legacy receipt、親欠損、source table不在 | 既存availability条件を守りunknown/理由を併記。0件の不存在認定をしない。 |
| 別会社/未来/非公開/syntheticの第二親、訂正保留 | 全親の理由を併記し現在利用を保留。当時viewの原文は変更しない。 |
| 同じ入力を翌日、又はJSONキー順を変えて実行 | 材料fingerprintは同じ。unchanged、詳細研究job0、送信/仮説/発注0。 |
| 予定は同じで新引用だけ追加、又は分類だけ改訂 | evidence/classification_changedとして区別。schedule_changedとしない。 |
| 空配列、既知空table、欠損table、不正bool/container/重複ID | 空は正常・分母0、欠損はunknown、malformedはValueError。DB bytes/transaction不変。 |

## 記録者の作業と、確認済みにできないもの

記録者は対象会社・期・発表か説明会か、原文に対応する日付と年次根拠、予定変更の元claim、実施を支持すると考える引用、結果資料との対応、次回確認論点を入力しなければならない。APIが企業の全サイトを読み、予定や実施を自動発見したとはしない。保存sourceを原文と照合することはできても、その引用が主張を十分支持する意味上の正しさはレビューを残す。

このmonitorで確認済みにできないものは、timezone不明の日程の絶対期限、全予定の網羅、資料がないこと、実際の発表時刻、結果の改善/悪化、仮説の反証成立、株価反応、IRの追加情報価値、売買条件、mappingの事前登録である。これらは未確認ならnull/unknownのまま返す。

後続実装は、上記の固定出力と少数合成ケース・1332のオフラインfixtureまでで区切る。DB永続化、scheduler、通知、分類推定、IR質問採否、モデル更新はこの単位に含めない。

## 接続した初版：schedule-only

上記は拡張を含む初期設計である。今回接続した[純粋な読取レポート](../src/ir_agent/catalyst_schedule.py)は、そのうち**日付のみ・timezone未確認の予定候補**に限定した。公開APIは次だけで、前述の全体APIを完成させたものではない。

```python
report_catalyst_schedule(connection, event_requests, *, as_of, now,
                        calendar_window=None) -> dict
```

入力eventのallowlistは `id,company_id,synthetic,kind,label,period,claims`。periodは `raw_label,fiscal_year_label,quarter_label,basis_quote,interpretation` の非空文字列descriptor。各eventにschedule claimを1件だけ許す。claimは初期設計のschedule項目に `basis_quote_location` を加え、全項目を明示する。位置不明ならlocationはnull。位置を渡す場合は `character_start,character_end,offset_unit,pdf_page,printed_page,saved_text_file,section` を指定し、本文またはform-feed区切りPDF頁内の引用と照合する。saved_text_fileは位置の記録であり、APIがそのファイルを開くことはない。

`date`は有効なYYYY-MM-DDまたはnull。`time,timezone,supersedes_claim_id`はnullだけを受ける。kindはearnings_release/earnings_presentationだけ。複数claim、変更・取消・実施、既知時刻/timezone、未知field、重複IDはValueErrorとする。原文日付・年度対応の意味はcaller mappingのままで、日付の数値文字列が原文の正しい解釈であると自動認定しない。

[1332候補fixture](../research/ir-case-studies-2026-10-15/1332/catalyst-schedule-candidates.json)のeventsから上記7項目を明示投影すれば使える。元fixtureのoccurrence_claims/result_links/change_verification/followup_topicsは今回の入力scope外なので、原artifactは変更せず、後続CLIで投影した別requestfileを使う。

既存read-only source readerのsource_graph、RecordAvailability、source_origins等を再利用し、全親と共有親DAGを辿る。公開開示以外のsourceは親を含め保留し、IR返信をpublic扱いへ格上げする機能は呼ばない。分類はas_of/nowそれぞれで実保存とrecorded_atを両方満たす最新版本を選び、source/body SHAと引用も結ぶ。rootはschedule分類が必要で、未分類・未解決・異なる分類は保留する。親も分類未確認を無視しない。

出力は `status:schedule_monitor_only`。全入力をeventsへ残し、`window_group:in_window|outside_window|date_unknown` とcoverageに表示母数を併記する。各eventはsource_binding、lineage_checks、historical_usability、current_useを分ける。機械的に結合できた場合も `status:source_bound_candidate`、`schedule.status:candidate_only`、`date_interpretation:caller_mapping_unverified`、`semantic_review_required:true`、`mapping_prospectiveness:unverified`を維持する。数値的な予定解釈や会社の全予定の網羅を確認済みにはしない。

時刻関連はdateがあればfloating_date、なければunknown。全件 `scheduled_at:null`、`due:null`、`relation_to_as_of:unknown_timezone`、`occurrence.status:not_established`、`result_documents.status:none_linked`。分類の更新による現在保留は過去as_ofの分類を上書きしない。source_sections/table_statusは読取時DBの構造・物理行数の診断であり、as_of時点の母集団件数ではない。既知空0と欠損tableのnull/unknownを区別する。

fingerprint、差分、予定変更採用、厳密時刻解決、実施確認、結果文書対応、自動jobは**未実装**。比較用previous_reportも受けない。DBへ書かず、Store初期化/DDL/GETを呼ばない。外側transactionを尊重し、外側commit/rollbackはしない。対象テストは[有限のschedule-only cases](../tests/test_catalyst_schedule.py)で、1332のsourceをメモリDBへコピーして試し、実DBは変更しない。
