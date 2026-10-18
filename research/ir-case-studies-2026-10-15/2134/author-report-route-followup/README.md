# 2134 北浜キャピタルパートナーズ：JPRレポートへの経路確認

**会社の公開告知1頁と本体の実URLまで確認した。本体は未取得で、著者予測・評価式・委託報酬は未確認。** 告知をレポート本文と扱わず、数値・事業適合・投資適格性・金融モデルへの採用は0。

会社PRは2026年8月24日付で、同日にJPR（ジェイ・フェニックス・リサーチ株式会社）の当社アナリストレポートが公開されたと説明する。告知自体は会社作成であり、「独立系」「第三者機関」という会社の記述を独立性の検証結果にしない。JPR代表者名をレポート執筆者へ移すこともしていない。

PRのPDFリンクannotationからpdftohtml XMLで次のhrefを取得した（推測や本文改行の連結ではない）。

`https://j-phoenix.com/wp-content/uploads/2026/08/2134_kitahama-capital-partners_analystreport_2026-08-24.pdf`

本文のURLは2行に分かれるため、source.content引用はそのままの改行を保持する。クリック先は別のXML hrefとして `02.pdf-link-extract.xml` と `report-route.json` のSHA・fieldへ結び、本文に存在しない連続URLのoffsetを作らない。

ネットワークは会社host robots200→指定PR PDF200→本体host robots301の3GETで停止した。後者は規則未確認で、受信Locationを記録するだけとし、redirect追従・別host・本体GET0。最大4GETの残1は未使用。会社hostのrobots許可は別hostへ移していない。missingrobots404方針は確認対象に含めたが、今回使用していない。

意味確認はPRの1頁だけ（上限2頁以内）。本体の意味確認0頁（上限4頁以内）。作者個人・会社計画転載vs独自将来予測・公正倍率・目標値・EVC等の算式・反証条件/期限・費用支払いはいずれもnull。未取得を全体不存在や評価手法不成立とはしない。現在送信適格性も未確認のまま、旧1819台帳のOct11 confirmed/not_statedだけを保持した。

source-bundleはcanonical jp:2134の会社公開告知1sourceのみ、companies/theses空。金融入力は未検証、robotsもレポート本体もsource化していない。pubnull、会社告知の表記日2026-08-24は日精度metadata。本文完了17:25:39.932478UTCとローカルraw保存を分け、歴史的初回保存は不明とする。ファイル名から本体公表時刻を推定しない。

固定UA Codex-IR-Research/0.1、継承proxy/CA・TLS、40秒/10MiB、共有2秒lock、各URL1回を使用。JS/API/URL構成/再試行/自動redirect/診断0。元旧resolved URLの日本語pathをそのまま要求し、prepared requestによるpercent encodingはcaptureのresponse_urlに別保存する。旧literal href欠損は未復元。

rawはresponse entity bytes（Content-Encoding展開後の可能性）でwire captureではない。raw/text/snapshot/capture/画像はこのdirectory基準。再抽出・画像SHA・5本文引用offset・XML実href・schema・旧入力SHAを有限確認した。実DB/Store/旧資料/コード/索引/監視/IR草案・送信は変更0。汎用byte verifier対応や財務全体は認証していない。
