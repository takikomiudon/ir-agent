# 3817 最終明示Location：追加1 GET

rootが保存済みGET4のLocationに限定して追加1 GETを許可した別phase。元の4応答・本文0というcutoffを変更せず、同actualhostのfresh robots200がexact /quote/3817.Tを許可することを確認した。

https://finance.yahoo.co.jp/quote/3817.T は200・完全461159B、本文完了2026-10-16T10:02:43.847879UTC。本文に**SRAホールディングス／3817／東証PRM／4,820／リアルタイム株価15:30**が結び付いている。これは価格の可視観測であり、円/JPY、価格の年月日、timezone、主価格の終値ラベルは未認証でnull。配当の円、値幅制限10/16、前日終値10/15、他欄の更新日時、HTTPDate、PTSの東証終値比から補わない。

providerのfooterは東証取引値をリアルタイム表示、出来高/売買代金を最低15分遅れと分けるが、主quoteの正確timestampや数値delay保証を新造しない。JS/APIを実行せず、初回HTMLの可視本文とliteral locatorだけを用いた。

原raw/textと3引用、親capture/SHA/追加許可の記録、旧14pins不変・HTML再現を保存しfreeze。合計5 GETで終了、追加延長・別providerなし。Graham計算・閾値・source正規化・金融採用・DB/Store・IR送信0。
