# 1813 不動テトラ：初期資料確認は短信本文取得保留

保存済みの実経路 `https://www.fudotetra.co.jp/ir/library/earnings/` を確認。robots200で実UA **Codex-IR-Research/0.1** とwildcardに対する対象一覧の許可を確認し、一覧も200だった。ただし受信HTMLでは年度selectと`xj-mainlist`が空で、正式短信の対象期・日付・PDF実hrefは取得できなかった。`XjStorageLoaderEarnings.js`への参照はあるが、取得・実行・API推測はしない。

**2GET／最大5GETで終了。** 本文未取得のため残予算は使わない。再試行・自動redirect・JS・別経路診断は0。通常proxy/TLSを維持しRPS0.5、第2GETから親指定の共有lockによる2秒間隔を使用。XJ配信hostは同日保存済み全禁止guardを参照し、新GETは0。

| 確認項目 | 今回の結果 |
|---|---|
| 事業 | サイトナビに土木・地盤改良・ブロック環境の名称。財務上の区分や利益driverは未確認 |
| 対象期・会計基準・連結・単位 | 本文未取得のため不明 |
| 実績／会社計画・予想の版 | 不明。索引200を直近決算の確認としない |
| CF作成有無・一時損益 | 不明。本文未取得を「未作成」「一時損益なし」に読み替えない |
| 次の公開確認 | 許容された正式短信本文で期・日付・実績と予想、CF、注記・事業説明を確認。次公表日はnull |

業種や値動きの推測で除外せず、会社予測・評価・投資判断・IR草案は作成していない。今回の限定経路で外部著者の予測・評価式を確認したわけでもない。

- [review.json](review.json)：確認範囲と未達依存。
- [source-bundle.json](source-bundle.json)：`schema_version:1, companies:[], sources:[…], theses:[]`。`jp:1813`の実取得index-only本文1件、`financial_content:false`。robotsは除外。
- [source-quotes.json](source-quotes.json)：6逐語引用、原HTML／抽出本文のoffsetとSHA。
- [link-provenance.json](link-provenance.json)：旧保存URL・JSON位置と今回capture。失われた旧hrefは補作しない。
- [access-guard.json](access-guard.json)：実UAのrobots判定と既存XJguardの参照。
- [transport-manifest.json](transport-manifest.json)、番号capture、`raw/`・`*.txt`：受信entity bytesと本文。gzip展開後の保存バイトであり、compressed Content-Lengthとは別。
- [validation.json](validation.json)、[baseline.json](baseline.json)：final metadataによる共有stable_source_id再現、source契約・引用・SHA、旧入力16件不変。

metadataのパスは`saved_case_directory`基準、それ以外の入力参照はrepo-root基準。独自providerの汎用byte verifierはunknownのまま。DBアクセス・旧資料／production変更・送信は0。
