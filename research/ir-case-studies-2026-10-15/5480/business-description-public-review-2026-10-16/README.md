# 5480 中期計画の静的入口を確認

保存済み実リンク `https://www.nyk.co.jp/investors/plan/` を対象に、fresh robots200と本文200の2GETを完了。robotsは `/mt/` を禁止するが選択経路は許可。HTML本文22,982Bを全保存し、残1GETは使わず停止した。

本文の実確認は「中期経営計画2026-2028」「PDF2.9MB」「適時開示資料（2026.5.8）」と旧2023計画への入口表示まで。**中計PDF本文は未読**で、事業の変更・顧客/収益説明・数値目標・リスク/前提・対象期の具体的開始終了は未確認。ナビの製品名を中計の事業本文に置き換えない。日付ラベルはリンク先資料の表示であり、この入口の公表/更新時刻ではない。

same-hostの実href `./pdf/plan2026-2028.pdf`（capture.GETs[1].html_visible_text.links[84]）を保存したが取得していない。外部ssl4.eir-parts.netの資料リンクは既存hold対象で、アクセス0。PDF/JS/feed/旧annual503/市場/会社概要の再取得はない。

既存Damodaran適応C1の全サイクル/規模・比較可能利益率、C2の需要/製品mix/原料/固定費、C3のROC/再投資/資金調達は全てunresolvedのまま。会社計画の存在を実績や正常値とせず、将来growth/EPS、現在局面、反証閾値へ代用しない。Anthropicのscreen→fundamental workと既知懸念点検は方法引用として区別し、会社についての新しい仮説・IR草案を作らない。

既存builderから入口HTMLのsource候補1件を生成しwhole再現を確認した。builder-bundle.jsonのwatch/unheld stubは構造入力であり、source-only-bundle.jsonはcompanies=[]、source自体はwhole同一。DB firstsave:null、金融入力・case更新・送信・売買採用なし。raw/text/引用offset/source-map/validation/manifestを保存し、root受入待ち。
