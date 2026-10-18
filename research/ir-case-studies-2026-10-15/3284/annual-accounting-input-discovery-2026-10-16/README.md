# 3284 フージャースホールディングス：年次入力の有限探索

公式IRライブラリーまでは取得したが、年次決算短信PDFの実リンクは静的HTMLで見つからず、年次実績EPS・BPSは未取得で終了した。**2 GET / 上限5 GET**、両方HTTP200。余った3回は使用していない。

保存済み公式rootの `$.links[20]` が示す `/ir/library/` を使用。fresh robotsは同pathを許可し、明示AI拒否なし。今回HTMLは最新資料・四半期一覧を空のE-IRコンテナとJavaScript参照で表す。静的PDFリンク3本は行動憲章等で、決算原本ではない。JS/feed/provider/search・別経路探索は本タスク対象外のため進まなかった。資料の不存在やサイト障害を意味しない。引用は [source-quotes.json](source-quotes.json) のraw HTML位置、取得証跡は [capture.json](capture.json)。

既存会社caseの重複は作成前の `research/ir-case-studies-2026-10-15/3284/` 範囲で未発見。窓口台帳は2026-10-11確認の `confirmed / individual_access=explicit` という履歴であり、現在受付確認や送信適格認定ではない。固定23社の調査順で、投資順位ではない。

会社の年度・連結/会計基準・普通株基準・分割・EPS/BPSの値は未確認。負値を観測して式定義外となったケースとは区別し、投資永久除外にしない。年次原本source候補は作成していない。価格取得・normalizer・金融評価・IR草案/送信・DB/Store・既存ファイル変更は0。

本文完了時刻は 2026-10-16T10:17:06.311744+00:00。公表日/公表時刻/DB初回保存は不明であり、取得時刻で補完していない。詳細は [review.json](review.json)。この有限作業は停止・固定し、追加取得や新phaseは提案しない。
