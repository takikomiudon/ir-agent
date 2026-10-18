# 研究監視report：独立受入の焦点

設計と実manifestの読取だけを完了。コードはstable通知後に確認する。GET・DBアクセス・既存変更は0。この段階で実装の合否は判定しない。

| 重要な失敗ケース | 独立確認で残すべき結果 |
|---|---|
| **新保存0を全件点検済みと表示する** | 135Aはinventory15件＝reviewed5／unknown10。新保存0・due=falseでも10件を `pending_issue_review_sources` に残し、全件完了／無作業としない。intake分類やreceipt一致でreviewedへ昇格しない。1518はinventory3件・reviewed3件として区別し、135Aから未確認状態を流用しない。reviewed自体も担当者申告であり、意味・著者条件成立の独立認定ではない。 |
| **今回作成manifestを過去時点で利用する** | 両要求のrecorded_atは2026-10-15T08:59:27.621436Z。last_review_atは135A06:00:18.725090Z／1518 08:16:51.977386Zで、manifest保存の証明時刻ではない。recorded_atより前のas_ofでは将来版としてheldにし、caseを落とさない。case_refの固定SHA一致と、当時のmanifest存在・事前性は別。後日の同path改変はhash不一致として保持し、最新内容へ差替えない。 |
| **後着・未列挙・来歴不明を同じ0件に潰す** | 合成DBで「古い公表日だがreview後にtrusted保存」「review以前に保存済みだがinventory外」「legacy firstsave不明／receipt不明」を1件ずつ区別する。firstsaveがlast_review_atと同時なら新保存の『後』に含めない。全親の第二親だけがfuture／heldの場合も保留し、shared DAGをcycleと誤認しない。as_of後の現在公開性保留は過去を書換えずcurrent_holdへ残す。 |
| **管理日を著者指定・会社発表・売却期限と表示する** | 2027-01-15は既存研究管理日、Asia/Tokyoは今回rootが明示採用したproject運用。Anthropicの定期点検手順と具体日付・timezoneを区別する。合成時計で2027-01-14T14:59:59Zと15:00:00Zの暦日境界のみ点検し、due到来を会社発表実施にしない。date/timezone未設定はnull、無効値は不正入力とし自動補完しない。 |
| **単一statusで複数保留や未確認母集団を消す／read-onlyが書く** | pending＋new_saved＋due＋evidence issueが併存する合成caseで各理由・IDを保持。tableなしはunknown／row_count:null、存在して空はknown／0。case要求母集団はこの2件と明示し未入力1819社やWebを監視済みにしない。temporary DBのdump／bytes／total_changes不変・外側transaction維持、wrapperは既存fileをmode=ro/query_onlyで開き不存在DBを作らないことを確認。Store初期化・DDL・job・金融actionは0、pillar_impact/investment_actionはnull。 |

実manifestの現在の件数・case_ref SHA・calendar参照SHAはoffline一致を確認した。実DBとの再照合はまだ行っていない。stable後の少数合成再現を主とし、実DBを独立点検する場合は親の別途指示に従う。単一snapshotの正当retryは同じ結果を返し、将来のWeb取得・自動日次起動・著者条件への意味比較まで完了したとは表示しない。

入力固定（SHA256）：

- `research/ir-research-monitoring-2026-10-15/read-only-report-design.md`: `47025b2ec0be38e36df4d6f06b8e66a53728517015c75d037682cbe785a09065`
- `research/ir-research-monitoring-integration-2026-10-15/actual-case-requests.json`: `fdf4dfb19bac90e11b45e84697b7769e7a072e5ddb4bacfaafa3d5f75504277c`
- `research/ir-research-monitoring-integration-2026-10-15/actual-request-preparation.json`: `372c1731855a3fa34cfd52e4f9c201f15ffa545154592ad52c55d7320847c343`
- `research/ir-research-monitoring-integration-2026-10-15/operational-calendar-basis.json`: `be96f64fd125c32300d6d63ddc0422be67f2f4170bda7a35d531544e65c41f31`

計画作成UTC: 2026-10-15T09:03:02.964479+00:00。新しい金融閾値・管理日・予測・質問・registryを設計していない。
