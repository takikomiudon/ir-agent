# 1827 FISCOショートコメントの限定確認

2GET（上限4、新規ホストrobots込み）で終了しました。会社noticeは200でしたが、そこにあるFISCO元配信のrobots.txtが403を返したため、記事本文へのGET前に停止しました。再試行・JavaScript・自動リダイレクト・URL推測・原因診断・別転載への迂回は0です。

会社noticeは2026年7月21日付で、フィスコによるショートコメント「ナカノフドー建設：東南アジア中心の海外建設事業に強い中堅ゼネコン、PBR0.8倍台で推移」の掲載を案内しています。元配信への実hrefは `https://web.fisco.jp/platform/market-news/0009350020260721041` です。この1件だけを追跡対象に選び、別掲のYahoo・株探・investing.comにはアクセスしていません。

確認できたのは会社による掲載案内と題名の引用です。著者本文、個人著者、事業仮説、反証条件、観測期間、独自予測、数値の予測主体、評価算式、目標株価、退出条件、委託・報酬開示はすべて未確認です。「記載なし」とは判定していません。会社が引用した当時の「PBR0.8倍台」を現在のPBR、公正倍率、目標値へ転用しません。

別途取得済みの8月7日短信は、この7月21日noticeより後の会社資料です。未取得の著者本文がその数値を使った、予測した、または反証されたと結び付けていません。新しい投資仮説やIR草案は作っていません。

[provenance.json](provenance.json)は保存済み公式リンク、今回のFISCO実href、要求しなかった転載先、robotsの証跡を保持します。会社サイトのrobotsは[同日の既存capture](../initial-public-review/capture.json)の404とraw SHAを参照し、再GETしていません。`contents.xj-storage.jp` の既知の全パス禁止についても新GETは0です。FISCOの403はrobots URLへの観測応答だけを意味し、記事自体の応答や拒否原因を推測していません。

[source-bundle.json](source-bundle.json)は `schema_version: 1`、空の `companies` / `theses`、会社ID `jp:1827` のnotice1件です。非財務の `index_only` とし、robots/error本文や未取得の記事をsourceに含めません。sourceの取得時刻はnotice本文GET完了の `2026-10-15T08:52:11.052372+00:00`。要求開始、会社表示の日付、正確な公表時刻の不明を分けています。

[quotes.json](quotes.json)の2引用、raw/text/capture SHA、HTMLのオフライン再抽出、source IDと入力構造、指定旧15ファイルの不変を[validation.json](validation.json)で確認しました。既知providerの検証形式は仮装せず、金融上の意味・モデル採用は未検証です。DB・旧資料・コードの変更、送信、発注、全件テストはありません。本文未確認という限界でこの限定課題を終了し、残りGET予算は使いません。

新capture/raw/textの相対パスはこのディレクトリ基準、sourceの `original_*_file` と旧資料のパスはリポジトリルート基準です。保存rawはHTTP content decoding後の応答entityバイトです。
