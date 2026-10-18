# 7388 FPパートナー：年次入力の有限探索

**年次原本PDFは未取得。3 GET / 上限5 GETで終了**した。保存済み公式root `$.links[28]` のIR別ホストと、その保存IR入口 `$.links[30]` のactual href `/ir/results/` を連結し、未試行の決算短信一覧を取得した。

IR別ホストのfresh `/robots.txt` は302で、literal Location `https://ir.fpp.jp/404.aspx` を予算内の手動1 GETで確認すると完全404だった。既採用の1723 missing-robots処理を適用し、その404 HTMLをrobots規則や明示許可と呼ばない。自動redirect/同URL再試行0、他hostへ許可を移していない。

決算短信一覧はHTTP200で取得したが、静的HTMLはIRPOCKETの空select/divとJS参照のみ、PDF実href0本。JS/feed/provider/search/別経路は取得しない。既知hold `www.xj-storage.jp` へのscript参照も追っていない。これは決算資料不存在や原本取得時のHTTP障害の証明ではない。残2 GETは未使用。

固定23社公表順の調査であり投資順位ではない。queue・固定343 CSV・元record SHAを照合し、作成前の会社研究folderに重複なし。旧窓口確認は2026-10-11の履歴で、現在受付適格性の認定ではない。年度・連結/会計基準・実績annual EPS/BPS・普通株の平均/期末分母は未確認null。負値の式定義外や永久投資除外と区別し、業界名からmethodを選ばない。

[capture.json](capture.json) に原バイト・各応答完了/保存時刻、[source-quotes.json](source-quotes.json) に3 raw引用のUnicode/UTF8位置、[review.json](review.json) に導線・robots分岐・入力pinsを保持。公表日/DB初回保存は不明で取得日へ置換しない。金融source候補・normalizer・価格・金融採用・IR草案/送信・DB/Store・既存ファイル変更0。この有限作業を固定して停止する。
