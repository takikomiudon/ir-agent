# 3962 チェンジホールディングス：年次入力の有限探索

**年次原本PDFは未取得。3 GET / 上限5 GETで終了**した。fresh robots、決算短信一覧、有価証券報告書一覧は全てHTTP200。両一覧は空のE-IRコンテナで、静的HTMLのPDF実hrefは0本だった。残2回は使用していない。

`work-queue.json` と固定343 CSVの3962行・既存窓口記録を照合し、作成前の会社研究folderに重複なしを確認した（DB確認ではない）。保存済み公式root `$.links[22]` の決算短信と `$.links[25]` の有価証券報告書という2つのliteral導線を使った。後者は最初から保存されていた明示導線であり、空一覧から推測して追加した経路ではない。

今回のrobotsは `/mt/` のみを禁止し、2取得pathは許可、明示AI拒否なし。一覧のJavaScript参照は保存データとして確認したがGET・実行なし。feed/provider/search・別経路・再試行へ進んでいない。この結果を資料不存在やアクセス障害とは呼ばない。6引用のraw HTML Unicode/UTF8位置は [source-quotes.json](source-quotes.json)、原バイト・時刻は [capture.json](capture.json)。

年度・連結/会計基準・実績EPS/BPS・普通株の平均/期末分母・株式分割基準はnull。負値の式定義外、guard不正、投資永久除外とも区別する。金融source候補は作成していない。公表日/DB初回保存不明を取得時刻で埋めない。

[review.json](review.json) に取得結果と入力pinsを保存。価格・normalizer・金融評価・IR草案/送信・DB/Store・既存ファイル変更0。旧窓口確認は2026-10-11の履歴であり現在の送信適格性を認定しない。この有限作業を固定して停止する。
