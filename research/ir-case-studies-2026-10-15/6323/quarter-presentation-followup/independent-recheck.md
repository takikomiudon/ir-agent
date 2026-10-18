# 6323 四半期説明資料の独立確認

取得・source整合と指定1/17/19/20頁を確認しました。raw/text/captureの不一致はありません。**暦/期basisの記述に1件、読取範囲を超える意味表現があります。**

p20は2026/2027/2028「年」の軸と「2028年Q1→2027年Q4」を表示しますが、この4頁だけでは暦/会計期basisやQの月範囲までは明示しません。reviewの`quarter_literal`、p20 quoteのlayout_note、validationのcalendar_yearという呼称は、年ラベルから暦年basisまで認証済みと読めます。旧broker期への実変換はなく、metadataのbasis未検証flagは保持されています。元fileを直さず、別basis確認の適用範囲付き追補で解決できるfindingとして固定します。

sourcebundle metadataにはcalendar/暦年の追加意味ラベルはありません。contentの原抽出p2には「暦年」が1件ありますが、指定頁外なので本taskではその意味・適用範囲を読んでいません。原sourceの書換えや、暦年ではないとの断定は行いません。

p17の先行手配・在庫・代替調達は会社の対応方針です。p19中国上海の写真/増強と、ベトナム施策は別site。p20の前倒し・第1期完成/稼働は予定で、実績ではありません。完成イメージと床面積ベース試算を、完成写真・実効能力・利益寄与に変えていない点は適切です。

1GETのliteral URL、同host robots200再利用guard/固定UA/path判定、原2,743,620bytes/SHA、29頁機械再抽出とsource本文の完全一致、11本文引用offsetと1manual右列引用の画像SHA/bboxを確認しました。公表精密時刻・歴史的first-saveは不明のままです。

[詳細記録](independent-recheck.json)にfindingと証拠を保存。旧21file・保護5入力は不変。新GET・DB/Store・code/旧source・索引/監視・IR変更は0です。新たな期対応や投資判断はしていません。
