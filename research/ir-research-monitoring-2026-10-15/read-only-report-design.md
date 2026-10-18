# 数値thesis前の研究点検対象：有限なread-only report案

結論：既存機能の再利用だけでは研究管理日の点検を返せないため、明示された会社別研究一覧を入力とする小さなread-only reportが有用。新registry/table/jobやvaluation guardの変更は不要。今回の成果は設計のみで、production・DB・旧artifactsを変更せず、新GETも行っていない。

## 採用元とproject適応の区別

固定原典 [Anthropic thesis-tracker](../../third_party/anthropic/skills/thesis-tracker/SKILL.md) SHA256 `6b4ce2967c5e01c6b42f5c140fa1e94dee2713b5d2de3eb71957ff5a5c11469b`：

> For each new data point or development:
> **Thesis impact**: Does this strengthen, weaken, or neutralize a specific pillar?

> Review theses at least quarterly, even when nothing dramatic has happened

原典は更新データとpillarの対応、定期レビューを求める。次のreportはその前段で「担当者が点検すべき保存資料・既存管理日」を列挙するproject実装案であり、著者条件への影響を機械判定する原典式ではない。毎日起動、2027-01-15という日付、DB receipt、statusはproject側の運用。株価・確率・数値予測・買い/売り閾値を定めない。

## 実例で確認した不足

| 保存記録 | 今あるもの | reportで確かめられること / 確かめられないこと |
|---|---|---|
| [135A case v2](../ir-case-studies-2026-10-15/135A/author-condition-followup/case-record-v2.json)、[manual check](135A-manual-check.json) | 実比較06:00:18、v2訂正06:06:51を区別。管理日2027-01-15。手作業確認時の保存15資料は全て実firstsave既知、実比較後の保存0、watch・thesis0 | 到着差分0を再現する入力候補。ただし15資料全ての著者条件への意味確認は済んでいないと明記されており、全件reviewed扱い不可。FY29の「近傍」やAND条件を判定しない。 |
| [1518 cadence](../ir-case-studies-2026-10-15/1518/author-condition-followup/review-cadence.json)、[manual review](1518-manual-review.json) | 会社3資料は07:53取得、08:03:35実保存、分類後に既存論点を別ファイルで比較。root点検08:22:13、管理日2027-01-15 | 3資料の保存・比較済み範囲を明示して次回の集合差分を出せる。研究JSON申告時刻やDB保存順だけでは未見情報による前向き検証・研究fileの実firstsaveを証明できない。 |

135A case v2のSHAは`2e566e72a04a89938357220715a10603a51ce1ce744207599ac921de6e81328b`、1518 caseのSHAは`763cb8ad2f001b7ed0eb7395508e1960a5c3b0c7715b00ab963b679c46dc1a1e`。v2の元分析時刻だけをfile作成時刻と誤読しない。

## 既存機能との境界

- `Harness.daily`（harness.py:128以降）はactive→利用可能thesis→新資料/next_review_dateの順で起票する。watch/thesis0を通すための変更や架空valuation投入はしない。
- `Intake.queue`と`intake` CLIは未分類の保存公開資料を既存lease/jobで分類する。分類済みは著者論点への比較済みを意味しない。再分類jobに定性研究を混ぜない。
- `inbox`は質問/返信、`policy` registryは採用済み判断方針、`observations`/`predictions`/`evaluation-protocol` registryは前向き観測/予測/評価設計。任意の研究file管理を保存するregistryとして転用しない。
- `report_catalyst_schedule.py`は会社発表予定の原典対応。研究管理日を会社予定日と偽って入力しない。会社予定の到来/発表実施と研究レビューdueは独立。
- 再利用するのは`parse_json`/`timestamp`/`json_text`、`source_origins`、`RecordAvailability.at/get`（読取のみ）、既存source/publicity/classification照合手順。Store constructorによるDDL・legacy receipt追加を避ける。実装時に既存private Readerをそのまま使うかは依存範囲を確認し、別の意味判定器を複製しない。

## 最小入力とAPI案

`report_research_monitoring(connection, case_requests, *, as_of, now) -> dict`。CLIは別の薄いread-only wrapper。DBは既存fileのみ`mode=ro`/`query_only=ON`、単一snapshotで読む。外側transactionをcommit/rollbackしない。Store初期化・新table・更新・GETなし。

`case_requests`は任意の研究JSONを推測parseする代わりに、人が次を転記・照合する小さな一覧。会社/論点の母集団をこの一覧として明示し、未入力1819社を監視済みとしない。

- `id`, `company_id`, `issue_id`：研究点検単位。単一会社に複数論点を許すがID重複は拒否。
- `case_ref:{path,sha256}`：参照研究fileの固定版。現在読んだfileとSHA一致を点検し、任意path/外部symlinkは読まない。
- `last_review_at`：研究で実際に比較した時刻の申告。fileのrecorded/corrected時刻と別。研究fileのtrusted firstsaveは現在未提供であり、この申告を事前コミットメント証明にしない。
- `source_inventory:[{source_id,source_snapshot_sha256,issue_review_status}]`：前回点検で**存在を確認した**保存source集合。`issue_review_status`は`reviewed|not_reviewed|unknown`。`reviewed`は担当者の意味確認申告であり、全社source一覧やintake分類から自動補完しない。原典親はclosureとして追うが重複資料を独立裏付けに数えない。
- `management_review:{date,timezone,basis_ref,basis_quote}|null`：既存採用日・IANA timezone・採用記録の参照。date/timezone欠損はdue=null。1518 cadenceにはtimezone明記がないので、135A manualのAsia/Tokyoを勝手に流用せず記録者が明示する。日付を再生成/繰越しない。

第1版は公開開示sourceだけを会社別に列挙し、価格・私的IR返信・他typeは別枠scope外件数として保持。新公開sourceを手入力で毎回列挙する必要はなく、対象会社のDB保存集合を読む。意味のある論点対応/新資料の採否は担当者が後から会社fileへ記録する。元2caseを黙って同一schemaに書き換えない。

## 時刻・差分・保留

全cutoffはoffset付き`last_review_at <= as_of <= now`。省略nowはwrapper実時計。sourceは申告published/retrievedだけでなく保存receiptのsnapshot SHA・known-byを照合し、`as_of=knowledge_at`のstrict PITで使えるものだけを利用可能集合へ置く。全親の会社・synthetic混入・時点・公開性も確認する。

- `new_saved_sources`：前回inventory外で、trusted first_saved_atがlast_review_atより後かつas_ofまでのsource。公開日が古い後着資料も該当し、Web上の新規発表とは呼ばない。境界一致は「より後」ではない。
- `previously_unlisted_sources`：inventory外だがfirstsaveがlast_review_at以前。見落とし/基準集合不足であり新着ともreviewedとも推測しない。
- `pending_issue_review_sources`：inventory内のnot_reviewed/unknown。新着0でも残す。inventory未設定/空の初回はbaseline未確立と明記し、すべてを既読へしない。
- `unavailable/unknown/mismatched_sources`：未来event/後日保存/receipt欠損/legacy firstsave不明/親欠損/会社不一致/同一ID別hashなどを理由付きで残す。legacy presenceのknown-byはfirstsaveに補完しない。同一ID別hashを通常更新や新着として採用しない。
- `classification_state`はas_ofに見える最新保存版の未分類/保留を併記。第一版は分類状態の表示までとし、前回分類版の入力契約を持たないため分類変更の自動差分は加えない。pillar影響を確認済みにせず、IR返信を根拠へ昇格させない。
- 管理日は指定timezoneに変換したas_ofの**暦日**と比較し、date以上で`due=true`（その日の精密時刻を表さない）。timezone未確認・日未設定ならunknown。会社発表実施/売却期限/催促送信を意味しない。

過去as_ofは保存sourceの利用可否を点検するだけ。研究fileの実保存履歴を欠くため、当時その一覧が存在したという歴史再構築は未検証。未来のrecorded/corrected版を過去fileと扱わずfile時点不足を保留する。新たな公開性訂正がある現在は独立`current_hold`を併記し、過去snapshotを書換えない。実装初版で訂正履歴を照合できなければそのsourceはunknownとし無視しない。

## 返却値と失敗時

全要求を残して`cases[]`、`counts`、`sections`を返す。各caseは`source_changes`、`pending_issue_review_sources`、`management_review_check`、`evidence_issues`、`reasons`を独立保持。総合は最大でも`needs_manual_review`、又は`no_new_trigger_in_checked_scope`/`insufficient_evidence`。複数理由を一つのstatusで消さない。`pillar_impact=null`、`investment_action=null`、`jobs_created=0`固定。

missing tableはunknown/row_count=null、存在して空はknown/row_count=0。source0と未確認を区別。malformed JSON、未知field、重複ID、不正日時/日付/timezoneはValueError。既知shapeでも欠損資料/不一致はcaseを落とさず理由付き結果。DB不存在は作らず失敗。原文全文は出力せずID/path/hash/時刻/理由まで。何も変化せず未確認もなくdue=falseの場合、追加preview/再詳細調査を要求しない。

## 次に実装するなら受入条件

1. 合成2caseでnewarrival・既存未確認・dueを独立列挙。watch/thesis0でもreportに残り、company/thesis/job/tableは不変。
2. source公開/取得が過去でもfirstsaveがcutoff後なら利用不可、last_review後の後着は新保存と表記。firstsave欠損/legacyは0件に潰さない。
3. inventory欠損・既知空・未分類・同ID別hash・親欠損/別社・synthetic混入・未来資料を保持。分類済みでもissue_review_statusは未確認のまま。
4. due暦日境界とtimezone欠損、case版hash不一致/未来訂正版を保留。管理日到来を発表済みとしない。
5. 同一snapshot再実行で同じ結果。DB bytes不変、外側transaction保存、table欠損でもDDL0。Web監視・対象外全社・著者条件成立・将来予測・金融採用を主張しない。

最小成果物は上記pure read-only module＋薄いscript＋有限合成test。最初は明示case一覧をworkerが読み、reportを見て担当者が会社別ファイルの比較へ進む運用で足りる。永続登録・scheduler・自動ジョブは、その運用で実際の不足が確認されるまで追加しない。
