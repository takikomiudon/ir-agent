# 2983 アールプランナー：Astris掲載入口の限定確認

最大2GETを使い、robots200と会社別入口HTML200を保存した。入口の静的 `application/json` に4件のレポート題名・掲載日表示・literal PDF URLがある。**レポート本文は取得しておらず、著者独自予測・評価式・目標値が使えるかは未確認**。今回の到達点は次の本文確認経路の発見である。

| 掲載日表示 | 題名 | 索引の説明 |
|---|---|---|
|2026.10.01|27年1月期2Q決算アップデート|会社予想を上方修正、下期にはなお上振れ余地|
|2026.06.24|27年1月期1Q決算アップデート|価格を引き上げながらシェアを拡大|
|2026.03.30|26年1月期4Q決算アップデート|2027年1月期も過去最高業績を見込む|
|2026.01.28|カバレッジ開始|デザインへのこだわりが実現する成長と収益の安定性|

上表は索引データの表示であり、PDF公表日・表紙・対象期や予測内容の確認ではない。10月1日はこの静的一覧4行内の最大表示日だけを意味する。「会社予想を上方修正」という説明も著者独自予測の存在証明ではない。作者個人・委託報酬・公正倍率・算式・目標株価・反証期限はいずれもnull。8151の著者予測を2983へ転用していない。

a要素は6件、PDF hrefは0件だった。一方、既存8151 `build_artifacts.py` のオフライン `Extract` クラスを再利用すると、HTML中の `script[type=application/json]` 1件から `hubdb_rows` 4件を厳密JSONとして読めた。JavaScript/main()は実行せず、APIや推測URLを使っていない。`02.embedded-script.txt` に原文字列、`02.embedded-reports.json` に解析結果、`inventory.json` にJSONpath・原HTML offset・literal PDF URLを保存した。各PDFは別host `www.astrisadvisory.com` であり、同hostのrobots・アクセス・本文は今回未確認。download_linkも追っていない。

公式起点は旧2983会社IR snapshotの `$.links[27]`（アストリス）で、当時はresolved URLだけが残る。今回の取得で旧会社HTMLのliteral hrefを復元したとはしない。旧台帳のconfirmed/not_statedと現在の送信適格性も別である。会社の投資順位づけ、数値モデル・IR草案・送信・DB登録は0。

`source-bundle.json` はcanonical `jp:2983` の入口HTML1sourceのみ（companies/theses空）。source.contentは保存可視テキスト、索引JSONは原HTMLと別抽出へ結ぶ。robotsは金融sourceに入れない。published_atと実際の初回保存時刻はnull、retrieved_atは本文完了16:35:17.693061UTC、raw_saved_atはこの取得処理のローカル保存記録として区別する。Last-Modified、copyright、索引の日付を公表時刻へ代入しない。

raw/text/captureの各相対パスはこのdirectory基準。rawはrequestsが受け取ったresponse entity bytes（Content-Encoding展開後の可能性あり）で、wire captureではない。固定UA・継承proxy/CA・TLS検証・共有2秒lockを使用し、各URL1回、自動redirect/retry/JS/API/PDF/別host取得0。旧入力4fileと既存7capture関連fileのSHA不変、schema・18quote spans・静的JSON再解析・robots exactpath/UAをオフライン照合した。これは保存と対応の点検であり、予測精度・現在適格性・財務入力妥当性を保証しない。
