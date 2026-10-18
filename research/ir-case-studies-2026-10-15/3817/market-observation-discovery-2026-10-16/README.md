# 3817 公式株価リンクの有限市場観測調査

会社公式IRライブラリーの既取得literal「株価 (Yahoo!ファイナンス)」から、最大4 GETで新しい市場価格観測を試みた。旧1975の通貨調査や他providerには進んでいない。

1. stocks.finance.yahoo.co.jp/robots.txt →301、明示Locationはfinance.yahoo.co.jp/robots.txt。
2. そのrobots →200、完全179B。両actualhostをholds-v8と照合し、固定UAに対して対象株価pathが許可されることを確認。
3. 公式literal stocks.finance.yahoo.co.jp/stocks/detail/?code=3817 →301、Location https://finance.yahoo.co.jp/quote/3817。
4. そのexact URL →301、Location **/quote/3817.T**。4枠終了のため未試行。

各遷移は自動redirectを使わず、直前の明示Locationから1回ずつ取得した。最後の相対URLを同hostへ解決した https://finance.yahoo.co.jp/quote/3817.T は保存候補であって、株価本文の取得済みや推測による先回りではない。

**価格本文は取得0**。価格、本文に結び付いた円/通貨、会社コード、価格日/時刻/timezone、遅延、終値ラベルは全null。HTTPの取得時計をquote asofにしない。Graham計算/閾値/金融入力採用をしていない。方式を先に固定したという根拠はrootからの指示で、保存済み3817公式libraryの範囲に価格表示がなかった事実と区別し、市場全体を対象にしたunbiasedな前向き試験とはしない。

raw4entity/HTTP全時刻・SHA・robots根拠と、未試行Locationを保存して凍結。新source・DB/Store・共有/旧file編集・IR送信0。取得回数上限を変更せずrootへ返す。
