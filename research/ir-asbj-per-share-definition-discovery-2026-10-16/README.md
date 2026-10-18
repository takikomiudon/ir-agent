# ASBJ一般BPS定義：有限導線確認

**BPSの一般定義本文は未取得。** 合計4GET（上限5）で、財務会計基準機構FASFの本文とASBJ入口への実リンクを確認した。個別文書URLを組み立てず、残1GETは未使用で停止した。

1. `www.asb-j.jp/robots.txt` は302でliteral `https://www.fasf-j.jp/` を示した。
2. 新hostの`www.fasf-j.jp/robots.txt` を200完全取得し、同hostの対象パスが既存parserで許容されることを確認。
3. literal FASF rootは302で`/jp/`。
4. 同host literal `https://www.fasf-j.jp/jp/` は200。本文は「公益財団法人 財務会計基準機構」、実リンク`ASBJ 企業会計基準委員会`→`https://www.asb-j.jp/jp/`を含む。

FASFのrobots許可を元ASBJhostへ移さず、元robotsのredirect先200HTMLを勝手に空rules/明示許可としない。元hostの規則は未確定のため、最後のASBJ入口GETを実施しなかった。禁止回避・別provider・検索・JS/API・Cloud診断へ進まない。

日本基準における普通株純資産の分子、NCI/新株予約権控除、自己株式/期末分母、該当適用指針第4号等の範囲・改訂を原本確認済みにはしない。PDFは0、意味/画像頁は0。3817当期BPSや優先株ゼロ・provider total_equityの同値・金融入力を認証せず、新gate/率/仮定/IR草案は0。

raw/時点/実Location・短い主体引用・実リンクpointerはcapture/quotes/reviewに保存。公表/DBfirstsave不明はnullで、HTTP時刻へ置換しない。研究時刻2026-10-16T13:40:37.813477+00:00。GET以外のDB/Store/旧編集0。固定後は編集しない。
