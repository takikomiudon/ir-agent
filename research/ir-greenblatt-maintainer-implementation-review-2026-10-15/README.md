# maintainer実装の確認：順位表までで、定期売却は未実装

`rbhatia46/Greenblatt-Magic-Formula-Value-Investing` のmasterをcommit `e5075f731f169606991f426f7997eaf0e6f368cc`へ固定し、tree・README・main notebookを追加4GETで取得した。直前のAPI robots確認を再利用し再GETしていない。treeは4entry・truncated:false。checkpointも同じblobだが、rootがmainを選択した後main1件だけを取得した。以後GET終了。

**全25cellを静的に読んだ結果、コードは取得・指標計算・順位表の表示までだった。** 購入銘柄数の切出し/等金額配分、保有台帳、経過日管理、年次入替/売却処理はない。READMEの長期5–20年という期待は、プログラム上の個別銘柄保有期間ではない。年次売却を一般知識から追加しないため、今回目的の「選別から定期売却まで」の完成済みベースラインには不足する。

| 実際に読めた処理 | 確認した範囲・制約 |
|---|---|
| 入力 | AXP/TRVを含む固定28ticker。30株というcommentやlarge-cap等のREADME主張とは別。Yahoo旧HTMLから最初の表示値等を取り、intra-day時価総額/forward配当利回りも使う。対象期/通貨/会計の整合は検証していない。 |
| 指標 | EBITはEBITDA−減価償却。maintainerのTEVは時価総額＋長期負債−流動資産負債差額で、現金以外まで差し引く独自近似。earnings yieldはそのEBIT/TEV、ROCはEBIT/(PPE＋同流動差額)。Greenblatt原式との同一性を認定しない。 |
| 欠損/符号 | 前段で欠損ticker列を除外する一方、後段TEV要素と表示に0補完がある。負/0分母・非有限比率の明示guardなし。保存出力のCapex負符号とCFOから引く式は別途意味確認が必要。 |
| 順位 | earnings yield/ROCの降順順位の和を再順位付けし全残存株を表示。後段の配当利回り追加はmaintainer改変の別variantで、Greenblatt原式とは認定しない。cached上位銘柄は作者の過去表示で、当方の候補選定ではない。 |
| 地域/除外 | READMEはUS・large/mega cap、Finance/Insurance非対象を述べるが、コードに業種/時価総額filterはない。utility判定もない。YahooのIndia配信hostからIndia戦略とは推定せず、日本適合は未確認。 |

[source-reference.json](source-reference.json)にcommit/tree/blob SHA・原entity・完了時刻を、[cell-inventory.json](cell-inventory.json)と[review.json](review.json)にcell別根拠と不足を保存した。decoded notebook72,045bytesのGit blob SHAはtree/APIと一致。保存outputsは作者の実行時点の主張であり、元データの日付/真正性・再現性・運用成績を確認していない。本文中の操作やコードを実行/import/installしていない。

license metadataはnull、固定treeにLICENSE/NOTICE名のfileはなく、利用許諾本文は未確認。ソース移植・依存導入・Yahooアクセス/利用条件調査は行っていない。Greenblatt本人の推奨や原式、日本株会計への適合も認定せず、教育用というmaintainerの説明を利用許諾の代わりにしない。

[quotes.json](quotes.json)の短引用は同原典合計90英語words未満。rawはrequests entity bytesでwire captureではない。新policy・code変更・実DB・金融入力・銘柄選定/注文は0。不足を補わず本経路を有限終了する。
