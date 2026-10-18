# 7525 — 比率定義を会社一次資料で確認する入口

保存済み公式IRページの実リンクから、既存論点 `7525-author-watch-original-product-ratio` に必要な4入口を整理しました。新GET・DBアクセスは0です。

| 入口の保存表示名 | 保存された解決済みURL | 次に確認すること |
| --- | --- | --- |
| 中期経営計画「GP2026」 | https://www.rix.co.jp/ir/management/midterm_plan_presentations/ | 会社原定義、KPI分類・範囲、目標/実績の版 |
| 長期経営計画「LV2030」 | https://www.rix.co.jp/ir/management/vision/ | 売上構成比の範囲・分類対応、同一定義か |
| 決算説明会資料 | https://www.rix.co.jp/ir/lib/presentation_material/ | 実在する資料タイトル・対象期・公表日・PDFリンク、比率の算式/注記 |
| IRカレンダー | https://www.rix.co.jp/ir/lib/calendar/ | 対象年度を明示した会社公表予定。研究管理日や売却期限とは分ける |

4件とも2026-10-11保存の公式IRページ `.../20261011T212141168571Z/02.json` のanchors（123/122/128/150）です。[routes.json](routes.json)に元JSON/text SHA、literal hrefとresolved URL、リンクラベルおよび本文の引用offsetを残しました。JSONに保存されたhrefは確認していますが、元応答raw HTMLの独立再読取はしていません。

入口のURLから、計画PDFの実リンク・内容・対象期・連結範囲を推測しません。今回の保存公式evidence10 JSON内に4入口の対象本文はなく、現在の到達性、robots許可、資料の最新性も未確認です。IRカレンダーの古い保存文中の日付を現在予定として扱っていません。会社目標40%/55%を投資閾値や最低進捗へ採用していません。

次の公開確認は、オリジナル品の分子/分母、連結/単体、内部消去・子会社直販、自社/グループ/専売とブランド/PBの対応、OEM・外注・修理/サービスの算入条件と期・再分類です。これは公表資料を読む経路であり、IR質問本文・登録ではありません。

保存された窓口URL `https://www.rix.co.jp/ir/contact/` と2026-10-12の旧取得は別欄に保持しました。現在の受付条件・個人受付・送信可否・返信可能性は不明です。旧recordのprovisional等の状態を今回再判定したり、最新catalogの認定として扱ったりしていません。

[validation.json](validation.json)で4リンク/8引用と旧12入力の不変を検証しました。会社一次財務本文の取得、金融値・EPS式・モデル・確率・価格判断・予定日・IR草案/送信は追加していません。
