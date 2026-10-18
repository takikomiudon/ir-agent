# 7525 — 公開FAQで比率定義が既答かの限定確認

保存公式IRページのactual `links[148]`「よくあるご質問」→ `https://www.rix.co.jp/ir/support/faq/` を1GET（200）で確認しました。同日取得済み同社robotsの原バイト・SHA・固定UAで当該path許可を再照合し、robots新GETは0。最大2新GETの残1件は使わず、就職FAQ/一般問い合わせ/回答内リンクへ広げていません。

本文の3分類・10問の回答を読みました。決算・財務の分類は会社創業、発表予定、資料の所在、株式分類はコード/単元/手続/優待、その他は決算期/関連会社/SDGs・ESGです。比率の連結・単体、グループ内取引、GP2026/LV2030で範囲が共通かの定義は**今回読んだFAQ範囲で未確認**です。会社全体で非公表とは断定しません。

[quotes.json](quotes.json)に3セクションの回答本文を丸ごと引用し、見出しと合わせ4件の原文offset/SHAを保存しました。[review.json](review.json)で草案3点への対応を分けています。既答による廃止/修正を要する定義は見つかりませんでしたが、それだけで送信・正式登録へ進めません。研究用preflight-v2は変更していません。

[source-bundle.json](source-bundle.json)はcanonical jp:7525の公式IR-support FAQ1source、取得時点は本文完了、公表時刻nullです。新providerのgeneric verifierはunknownを保持し、局所raw/text/captureSHA・Parser再現・引用・旧入力不変の点検は[validation.json](validation.json)に分けました。最新比率、利益/EPS/評価モデル、著者閾値、IR草案変更/登録/送信、DB/production/旧資料変更は0です。
