# 構造化資料の定性レビュー10job：初回の実測

直近の[claims.json](../ir-structured-facts-qualitative-review-2026-10-15/claims.json)にある**10job・各generation1のexact attemptだけ**を、既存のlease台帳投影APIとcapacity reporterで計測した。対象段階は `lease:qualitative_review:author_condition_review`。18保存sourceを既存著者条件と比較する定性jobであり、10社の全投資分析・数値仮説・IR判断が完成したという意味ではない。

観測as_ofは実時刻 `2026-10-15T23:56:01.196870+00:00`。計測窓は半開区間 **[2026-10-15T22:47:30.438013+00:00, 2026-10-15T22:54:06.866615+00:00)** とした。始点は最初の実claim記録、最後の実completionは `22:54:06.866614+00:00`。窓末ちょうどのイベントを別計上する既存契約に従い、最後の完了を含めるため終点を1microsecond後へ置いた。営業時間・日末は補っていない。

| 実測項目 | 結果 | 意味 |
| --- | --- | --- |
| 窓内の完了 | 10attempt・10会社ID | この段階の完了イベントのみ。全工程完了ではない。 |
| 計測窓の長さ | 396.428602秒（約6分36秒） | 10claimの最初から10completionの最後を含む窓。 |
| 1attemptのlease経過p50 / p90 | 395.990073秒 / 396.048264秒 | 10サンプルのnearest-rank。分析active時間や将来予測ではない。 |
| lease経過の最小 / 最大 | 395.931140秒 / 396.070180秒 | ほぼ一括の確保/完了時刻に基づく。 |
| attempt別lease経過の合計 | 3960.006894秒 | 同一workerの重複を含む予約区間の合計。実作業合計ではない。 |
| 同workerの占有区間union | 396.428601秒 | 重複を除いたlease占有壁時計。実作業/能力ではない。 |
| 同workerの重複計上差 | 3563.578293秒 | 上記の「合計−union」。重複していた壁時計そのものや並列人数ではない。 |
| 異なるworker IDの最大同時数 | 1 | 台帳のIDに基づく値。実際に作業した分析者/サブエージェントの同時人数は不明。 |

`worker_id` は元の **codex-structured-facts-qualitative-review** を10件とも維持し、サブエージェント別IDへ付け替えていない。同じworkerでleaseが重なるため、実作業の分担・待ち・反証時間をこの台帳だけで分離できない。

active_seconds・tokens・costは全10件で未計測null。worker秒予算・費用予算も未指定null、待ち行列時間・期限超過・実際の分析者並列数も不明のまま。report内の `known_whole_attempt_sum: 0` は既知サンプルなしという合計であり、「実作業0秒/費用0」の観測ではない。会社上限は **null / capacity_status: not_estimated**。会社数/日・worker増員による能力・将来処理量へ換算していない。

[all-attempts-projection.json](all-attempts-projection.json)にはas_of時点の全81attempt投影とauditを保存した（除外0・orphan0、現snapshotで未計測job3）。そこからclaimsのjob_id/generationで取得した10attempt IDだけを抽出した根拠が[cohort-selection-audit.json](cohort-selection-audit.json)。10件の終端resultは既存APIの現在job snapshot照合にすべて一致した。他cohortの71投影を当cohortへ混ぜていない。

既存API `build_attempt_measurements` と `report_research_capacity` を利用し、入力は[cohort-capacity-request.json](cohort-capacity-request.json)、無改変の出力は[capacity-report.json](capacity-report.json)。[cohort-boundary-evidence.json](cohort-boundary-evidence.json)に境界の元header/eventとclaims SHA、[observation-summary.json](observation-summary.json)に抜粋と参照コード/docのSHAを保存した。reporterが返す汎用 `next_measurements` は元出力として保持するが、このcohortの再計測や将来能力推定を新taskにはしていない。

DBは `data/ir-research-2026-10-15.sqlite3` をmode=ro/query_onlyで2snapshot読取（境界確認、既存投影API）し、Store初期化・schema変更・実DB書込みは0。[db-read-verification.json](db-read-verification.json)の読取前後main SHA256はともに `2a36bf74a54c61905bb44926692d2ec89570c66315d0ebbd0bbb4b13f4ad93ce`。読取区間は `23:56:01.194898`〜`23:56:01.469072 UTC`。APIのcommitted snapshot fingerprintはmainファイルSHAとは別定義で保持している。

エラー0。新GET・コード/共有文書変更・DB更新・外部送信は0。この1cohortの初回観測として有限終了し、同義の再計測や会社上限推定を続けない。
