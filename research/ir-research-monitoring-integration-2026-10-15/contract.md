# 研究点検対象report：初版契約

実装: `src/ir_agent/research_monitoring.py`、script: `scripts/report_research_monitoring.py`。採用設計は [read-only-report-design.md](../ir-research-monitoring-2026-10-15/read-only-report-design.md)。固定Anthropic thesis-trackerのStep 2（新データのpillar影響点検）と少なくとも四半期の点検を支える前段であり、金融判断式の追加ではない。

`report_research_monitoring(connection, case_requests, *, as_of, now, research_root)` は明示case一覧と保存DBの読取snapshotからreportを返す。existing Storeは初期化せず、`_ScheduleReader`と`RecordAvailability`経由の保存時刻/SHA/原典closure/公開性/分類を再利用する。DDL・DB更新・ネット・job起票・外部送信・予測作成は0。

## 入力

`case_requests`はJSON array。各entryの全必須keyは以下。未知field、重複ID/資料ID、誤型、無効な日時・日付・IANA timezoneはValueError。

```json
{
  "id": "synthetic-case",
  "company_id": "jp:TEST",
  "issue_id": "existing-author-condition",
  "synthetic": true,
  "recorded_at": "2026-10-15T10:31:00Z",
  "last_review_at": "2026-10-15T10:30:00Z",
  "case_ref": {"path": "case.json", "sha256": "<lowercase 64-hex SHA256>"},
  "source_inventory": [
    {"source_id": "saved-source", "source_snapshot_sha256": "<models.json_text snapshot SHA256>", "issue_review_status": "reviewed"}
  ],
  "management_review": {
    "date": "2027-01-15",
    "timezone": "Asia/Tokyo",
    "basis_ref": {"path": "cadence.json", "sha256": "<file bytes SHA256>"},
    "basis_quote": "2027-01-15"
  }
}
```

上例はshape説明で、hash placeholderを有効な入力と認めない。SHAの方式はfile=保存bytes、source=既存`models.json_text`のUTF8。case_refとbasis_refは同一fileでもよい。file参照はresearch_root内だけ（相対又はroot内絶対path）。`../`やsymlinkで外へ出るpathを読まずValueError。未存在fileやhash/引用不一致はcaseを消さず根拠不足へ置く。原文全文はreportへ出さない。

`source_inventory`は前回存在確認した集合で、論点への人の確認申告を`reviewed|not_reviewed|unknown`で残す。nullは前回集合不明、[]は既知の空集合。分類済み/前回時刻より前の保存だけからreviewedを作らない。`management_review`はnull可、date/timezoneもnull可。timezone未確認の既存記録にはnullを使い、dateの再設定・timezone推測をしない。初版はISO dateの全文字列が同じbasis_quote内にある場合だけdueを計算し、異表記しかない場合の意味変換はunknownに残す。これが妥当な管理日という意味確認は人の責任。

設計補足：entryの`recorded_at`を必須とした。manifestを新作した時刻を転記し、`last_review_at <= recorded_at <= now`を要求する。`recorded_at > as_of`の過去表示ではmanifestをheldにし、due=null。これは申告時刻検証であり、file/manifestの実firstsaveを証明しない。研究fileの個別schemaを推測parseした履歴再構築や、記録者による古い日時申告を防ぐ永続登録は行わない。初版は`manifest_prospectiveness=unverified`を常に残す。

## 出力・時刻

top-level: `schema_version,status,as_of,checked_at,cases,coverage,sections,jobs_created,limitations`。

case: `id,company_id,issue_id,status,manifest_check,source_changes,pending_issue_review_sources,sources,source_count,outside_scope_source_count,management_review_check,evidence_issues,reason_codes,pillar_impact,investment_action,meaning_review_required,manifest_prospectiveness,jobs_created`。

- source_changesは`new_saved_sources`と`previously_unlisted_sources`を別配列にする。firstsaveがlast_reviewより後（厳密な`>`）かを比較。保存到着はreceiptの事実であり、未分類/親欠損/現在保留でも新着自体は表示可能。source.statusとhistorical_usability/current_useを別に読むこと。古い公開資料の後着を新発表とは呼ばない。
- sourceの`issue_review_status`をそのまま残す。未確認の全資料をpendingへ置き、新着0で未確認を消さない。receipt欠損、legacyのfirstsave不明、source/親欠損・別社・synthetic混入、未来/後日保存、hash不一致、未分類/分類保留をunknown/mismatch/heldと理由へ残す。
- as_ofとnowはoffset付き、as_of<=now。保存資料はstrict PIT（as_of=knowledge_at）で点検し、現在の公開性・分類保留は別current_useへ残す。legacy presenceを実firstsaveへ補完しない。
- dueは指定IANA timezoneのas_of暦日>=既存date。日内の厳密な実施時刻・会社発表済み・売却期限を表さない。日時不足・根拠file不一致・manifestの未来申告ならnull。
- case総合statusは`insufficient_evidence`（不足あり）、`needs_manual_review`（到着/旧未列挙/未確認/dueあり）、`no_new_trigger_in_checked_scope`。理由・各fieldは並存。pillar_impact/investment_actionはnull、jobs_createdは0固定。
- sectionsのtable欠損/未対応schemaはunknown、row_count=null。既知空tableはknown/0。明示case0は正常で、全社監視済みの主張ではない。

## 初版の限界・運用

対象は明示会社の保存public_disclosureと、その参照親。IR返信とIR親は既存ScheduleReaderの初版scope保留を維持し、私的情報を予定/公開根拠へ昇格させない。分類状態は表示するが前回分類版を入力しないため分類変更差分の自動判定は行わない。著者の「近傍」やAND条件・期の対応・数値モデル入力採用を判定せず、担当workerが会社研究fileへ比較結果を追記する。前回資料集合・管理日・引用・timezoneは記録者の明示入力が必要。

scriptは`--db --cases --research-root`必須、`--as-of`省略は内部実時計。`--now`は提供しない。DBはmode=ro/query_only/BEGINで読み、欠損DBを作らない。libraryは外側transactionを保持し、それがなければ自分の読取transactionをrollbackするだけ。DBやfileの同時変更を監視するdaemon、fileとDBの横断atomic snapshot、Web巡回、全1819社coverage、自動schedulerは未実装。

検証対象は新規`test_research_monitoring.py`と`test_research_monitoring_cli.py`の合成/一時file/一時DBだけ。実135A/1518のreport実行と実DB照合は親が別途行う。
