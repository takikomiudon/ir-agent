# 2471 公式事業説明literal：robots取得保留で有限終了

対象は保存済み実リンク `https://www.spool.co.jp/investor/library/integrated_report.html` 1件。既存保存本文の重複は確認されず、www.spool.co.jpはholds-v8の12exacthost対象外だった。

fresh robots1GETがHTTP503・完全91Bで終了し、本文は `upstream connect error or disconnect/reset before headers. reset reason: connection timeout`。規則が不明なので選択本文GETは0、残2GETを使用せず停止した。再試行・過去robots流用・UA変更・JS/feed・閉じた年次資料・別provider/市場経路への切替はない。これは会社の拒否や資料不存在の確認ではない。

事業・顧客・収益説明・会社が示すリスク・資料対象期/時点は全て未確認。統合報告書というリンク名を内容へ置き換えず、業界タグ・低ボラで除外したり、営業仮説・forecast・閾値・IR草案を作らない。

Anthropic原文のscreenからfundamental workへ進む手順と既知懸念の点検、projectの方法引用と会社事実を分ける規則を参照した。方法は会社の事実や推奨ではない。quotes.jsonには方法引用とtransportエラー引用を別roleで保存。

source-candidate.jsonは未作成状態を示すファイルで、ingest用source bundleではない。成功200の会社本文がないため既存source builderを実行せず、proxyエラーを会社開示sourceにしない。DB/Store・旧file・公開code/docs・金融採用・IR送信は0。原raw/text/HTTP時計、選択根拠とinput pinsを保持し、この有限試行を閉じる。
