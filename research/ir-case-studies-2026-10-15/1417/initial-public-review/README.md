# 1417 ミライト・ワン：初期公開資料確認は本文取得保留

IR入口と実href先の「決算短信等」は取得できた。ただし一覧の受信HTMLは年度選択・資料一覧の空要素とJavaScriptローダー参照のみで、対象期・表示日・正式短信PDFの静的リンクを確認できなかった。指示どおりここで終了した。

| GET | URL | 結果 |
|---|---|---|
| 1 | https://ir.mirait-one.com/robots.txt | 404。robots不在として記録 |
| 2 | https://ir.mirait-one.com/ | 200。IR入口と「決算短信等」hrefを確認 |
| 3 | https://ir.mirait-one.com/data/order02.html | 200。`xj-select-year_s`・`xj-mainlist` は空。PDFリンクなし |

最大6GETのうち3GET。通常proxy・TLS検証を維持し、global RPSは0.5、再試行・自動redirect・JS/API取得／実行・他経路への拡張は0。新たな接続診断も行っていない。

事業・対象期・連結範囲・会計基準・実績／会社予想・単位・CF作成有無・公表指標値は財務本文未取得のため未確認。月次受注、財務ハイライト、説明会資料等のナビゲーション名は資料・数値を確認したことにしない。CFを入手していないことと、会社がCFを作成していないことも区別する。業種や値動きを推測して除外していない。

`contents.xj-storage.jp` は本日保存済みの全禁止robots guardを参照し、このhostへの新GETは0。今回は1417の具体的PDF URL自体が未確定であり、そのPDFに対するHTTP拒否を観測したという意味ではない。

次の公開確認は、許容された本文取得経路で正式短信の期・日付を特定し、実績と会社予想、連結・会計基準、CFの有無を本文で確かめること。次公表日は不明のためnull。新しい質問・予測・評価モデルは作らない。

保存物：

- [review.json](review.json)：確認範囲・不足・終了理由。
- [source-bundle.json](source-bundle.json)：取得したindex-only本文2件だけ。各 `financial_content:false`。robotsは含めない。
- [source-quotes.json](source-quotes.json)：HTML本文／原HTML逐語引用8件・offset・引用SHA。
- [link-provenance.json](link-provenance.json)：保存済み入口経路と新しい実href、原HTML根拠。
- [transport-manifest.json](transport-manifest.json)、番号capture、`raw/`、`*.html.txt`：3応答原バイトと抽出本文。
- [access-guard.json](access-guard.json)：既存XJ制限の参照。新規取得資料ではない。
- [baseline.json](baseline.json)：旧入力25ファイルのSHA。

capture metadata内のパスは `saved_case_directory` 基準、それ以外の参照はリポジトリroot基準。独自providerは既存汎用byte verifierの未対応としてunknownを維持し、raw／text／capture SHAを個別に照合した。source ID作成は実DB登録・金融意味確認とは別。

DBアクセス・旧入力変更・コード変更・送信・売買は0。2つの索引を取得したことは財務本文のカバレッジ拡大ではない。
