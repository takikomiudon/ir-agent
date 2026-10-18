# 5988年次残高8factの独立レビュー

**原表示factとして8件を受入れ、指摘0件。金融profileへの採用は未確認のまま。** 抽出担当から独立して、原文と保存画像を照合した。新しい意味読解はp83上部C&E注記とp103普通株式対応純資産、既読p63資産合計/p104借入金等合計も対象行を再確認し、余分な頁を追っていない。

| 原表示（百万円） | 左 | 右 | 日付/列の扱い |
| --- | --- | --- | --- |
| 現金及び現金同等物 | 30,236 | 22,773 | CF期末残高対応注記の2025-03-31/2026-03-31 |
| 普通株式に係る期末の純資産額 | 90,446 | 64,854 | 同表の2025-03-31/2026-03-31 |
| 資産合計 | 105,464 | 101,415 | BSの2025-03-31/2026-03-31 |
| 借入金等明細・合計 | 615 | 24,575 | 当期首残高/当期末残高だけ。正確日付はすべてnull |

p104の `opening_balance/closing_balance` を維持し、前期BS末と自動同一視していない。p65の2025-04-01〜2026-03-31は別のscope内の年度文脈で、当該引用の文字/UTF8 offset・旧14fact参照を照合した。明細との対応はreviewer assertionであり、明細残高の精確日付へ転記していない。

普通株式対応純資産は直接印字の90,446/64,854で、BPS×株数や純資産−NCIから逆算していない。借入金等合計は直接615/24,575を残し、成分和で丸め補正しない。ダッシュ0化はない。C&Eと現金及び預金は同じ残高と扱わず、いずれもcanonical cash/equity/debt/assetsへの適合や金融採用を認定していない。

連結・前当期/左右列・原会計名、百万円→JPYの明示換算、4引用/8行の文字・UTF8 byte半開offset、画像SHAと標準value pathを確認した。原source全object・metadata・ID・取得/公表欄とnative/canonical別SHAは旧入力/標準bundleと一致する。会社の会計値と抽出担当を区別し、派生生成時刻を実DBfirstsaveへ遡及しない。accounting_basis:nullと未表示精度の留保を保持している。

共通 `reproduce_disclosed_fact_source` をオフラインで独立実行し、`reproduced / matched / matched_supplied_snapshot`、返却objectは保存receiptと一致した。旧107＋年次14の121factとのID・会社/concept/期signature重複0、旧141fileのSHAもすべて一致した。これら141fileは不変確認であり、全意味再読ではない。

[独立JSON](independent-review.json)に8fact checklist、全24参照SHA、原日付/金融採用の限界を保存した。期間対応を判断して埋めず、ROIC等の計算・金融profile採用・IR準備完了へ昇格しない。新GET・DB・元成果/共有文書/コード編集は0。
