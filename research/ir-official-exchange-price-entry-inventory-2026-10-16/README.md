# 保存JPX captureの公式株価入口

**公式JPXトップの保存actual hrefに、株価検索への経路がある。** `evidence/8697/20261012T005718978839Z/01.json $.links[45]` は「株価検索」→ https://quote.jpx.co.jp/jpxhp/main/index.aspx?F=stock_search をhref/url両方に保持する。同じhrefは保存公式institutional頁にもある。月末上場一覧頁ではこのhostへのリンクを見つけていない。

保存公式StockSearch 640A/641A/642Aにも「株価表示」の個社URLがあるが、旧captureにhrefフィールドは無くresolved URLだけ。query codeやURL構造を組み直して他社へ使うことはしていない。個社リンクは保存導線の記録であり、新しい研究対象選定ではない。

[inventory.json](inventory.json)に5親captureのSHA、元URL/取得時点、links位置、実hrefの有無と4個のunique経路を保存した。親の報告HTTP raw hashとJSONファイルのSHAは別で、元HTML byteを新たに回復したとはしていない。

限定した既保存検索では対象hostの本文取得・意味読了・閉鎖記録を特定できなかった。13host hold v9にはこのexacthostはないが、freshrobotsや現在の取得許可を確認した意味ではない。query1.finance.yahoo.com禁止は維持し、query2/ミラー/UA変更/同じendpoint別hostを候補にしない。JPXの入口が実際にどのデータを返すか・基礎vendor・取引所検証・通貨/価格/観測時刻は全て未確認。

既存J-Quants認証SDK/株価APIとは別の公開入口で、キー読取・APIcall・新GET・ブラウザ/JS/POST・DB/Store・旧ファイル変更0。ここでは元導線の有無だけを確認しfreezeする。
