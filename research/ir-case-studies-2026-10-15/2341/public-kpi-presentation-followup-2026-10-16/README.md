# 2341 公開KPI説明資料の対応期確認

保存済み旧contact `20261011T044737201257Z/07.json → $.links[18]` の公式「説明会資料」一覧を取得した独立phase。初回robots200（117bytes、2026-10-16T06:14:19.420676+00:00観測）の許可規則・rawSHAを再照合して再利用。最新holds-v8非該当、通常proxy/TLS・固定UA・redirect/retry/JS0。**上限2 GET・実1 GET**、一覧HTTP200完全46,653bytes。

今回保存した静的一覧の先頭は **2026年4月20日・2026年2月期** の説明資料/ファクトシート、次は **2025年10月20日・2026年2月期第2四半期**。今回の **2027年2月期第2四半期（2026年10月8日短信）** に対応する掲載行/正確PDF literalは見つからない。期を取り違えて前年Q2や直近通期の資料を取得せず、残り1 GETを消化しない。ファイル名を生成せず、別一覧・過去Q1・JS探索も行わない。

sourceは今回必要だった一覧HTML1件のみ。PDF本文0・全文PDF/意味画像0頁。HRtech全体とワガシャ売上の解釈、KPI定義、費用bridgeは本phaseで追加確認できていない。資料ラベルを財務本文とせず、`financial_content:false` は内容判断だけでnative分類ではない。初回表紙の「説明会後、掲載予定」を公表済み/開催実施済みへ自動変更しない。他の場所も含む非公表/不存在は断定しない。

`source-quotes.json` に先頭掲載行の逐語・Unicode/UTF8offset/native source SHA/rawSHAを固定。全原raw/visible text/HTTP時計と既存literal出典を保存し、一覧更新日・正確公表時刻はunknown。過去掲載資料の日付は新sourceの公表日ではない。汎用byte verifierはnot run/unknownのまま。

旧initial/segment producerと受入履歴は不変。新GET以外DB/Store/code/旧file変更/金融採用/新予測・価格/IR0。この一覧1件で有限freezeしroot受入を待つ。
