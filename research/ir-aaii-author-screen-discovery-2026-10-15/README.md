# AAII公式・著者スクリーニング候補の有限調査

2026-10-15に、公式seed `https://www.aaii.com/` を起点とするGraham / NCAV / net-net本文候補の調達を試みた。事前に保存済み research / docs / third_party の該当URL・団体名を検索したが、同経路の過去取得記録は見つからなかった。中央収集保留v5の9 exact hostに当該hostはない。これは指定範囲の検索結果であり、全ファイル・全過去作業の不存在の認定ではない。

**fresh robotsの1GETで終了した。** `https://www.aaii.com/robots.txt` はHTTP403、完全受信963 bytesで、本文完了は `2026-10-15T22:02:52.624186+00:00`。保存本文は失敗を示すHTMLで、有効なrobots規則を取得できなかった。403をrobotsの明示的なDisallowや、未取得の記事自体の拒否応答と読み替えない。

公式root本文・記事・criteriaの取得は0。最大4GETのうち残り3GETは使わず、再試行、UA変更、別host、TLS変更、JavaScript/iframeの追跡、検索語の追加は行っていない。候補inventoryは空だが、AAIIに対象記事が存在しないという結論ではない。買い条件・売り条件・保有期間、米国等の対象市場、通貨・会計・財務定義、利用条件はすべて未確認。金融数値や原典の内容を記憶から補っていない。生成した原典本文の引用は0語。

[guard.json](guard.json) は事前範囲と保留索引SHA、[capture.json](capture.json) は正確なURL・HTTP状態・時刻・受信原本SHAを保持する。[outcome.json](outcome.json) は停止理由と未確認事項を区別する。rawはrequestsが受信したentity bytesであり、wire captureではない。UA `Codex-IR-Research/0.1` は設定値とprepared requestの値を記録したもので、独立したwire検証ではない。

本taskの編集先はこのfolderのみ。実DB・src・共有docsの変更、戦略採用、投資判断・売買・対外連絡は0。QuantConnect前2phaseの計5GETの証跡は変更していない。中央保留索引への追加は本taskでは行っていない。
