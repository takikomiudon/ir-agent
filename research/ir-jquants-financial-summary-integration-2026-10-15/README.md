# J-Quants 財務summary baseline追加

既存会社scopeに限定して1開示日分のSDK財務summary rowを保存するopt-inを追加した。個別会社サイトのPDFとは別のデータ経路で、会社マスター/状態変更や金融モデル採用は行わない。[利用・契約](../../docs/jquants-financial-summary.md)、[検証記録](validation.json)、[SDK実装根拠](sdk-contract-evidence.json)を参照する。

`normalize_jquants_financial_summary` と `fetch_jquants_financial_summary`、および `sync --provider jquants-financials --date DATE` を追加した。CLIは既存company IDだけをscopeへ渡し、空又は非canonical scopeはAPI前に停止する。単日bulkで `ClientV2.get_fin_summary_cursor(date_yyyymmdd=DATE)` を1回だけ呼び、cursorは渡さず保存もしない。SDKの内部paginationを1 HTTPと数えない。range/銘柄別parallel/master要求を増やしていない。

SDK2.8.0のmethod型、deprecated旧method、111列、日付変換とpagination実装を先に読み、元bytes/SHAとlicenseを `sdk-evidence/` へ固定した。既存cliとadapter exportの変更前完全bytesは `before/` と [manifest](before-files.json)にある。

Code/DiscDateを確認し、対象外普通株・別種証券を理由と件数付きでskipする。対象rowのDiscDateが要求日と異なる場合は停止する。row JSONはSDK受領時の値を既存JSON helperで保存し、欠損/NaN/空/ダッシュ、期/予想/非連結fieldを区別する。SDK前のHTTP数値tokenや精度、金額単位、連結範囲、予想の正しさを認証しない。公表時刻はnull、取得時刻はSDK復帰後ローカル受領時計とし、wire完了時刻と呼ばない。

新provider `jquants_financials` / dataset `fins/summary` は旧株価providerと分離し、既存quote normalizerの拒否も検証した。既存の6種金融モデル・decision・intake分類・定性jobは変更していない。sourceはpublic_disclosure/requires_research true、意味確認未了/金融入力未採用のまま。

新focused **19件**と既存adapter regression **24件**が成功した。全入力は架空で、実SDKのDataFrame変換もin-memory fake transportだけを使った。CLIでの登録/再登録はtemp synthetic DBだけで、会社行の名前・status・heldの不変、重複sourceの非増加、scope外skipを確認した。初回CLI fixtureのschema_version欠落と旧返却count keyの誤記は修正済み。全文test suiteは主担当が1回実行する予定で、producerは実行していない。

実金融データ受領・ネットワーク要求/認証呼出・実運用DBアクセス/書込み・契約・モデル採用・外部送信・注文は0。現在のprovider利用権/coverage/最新予想、SDK前段の原HTTP、PDF全文、live接続、スケジューリングは未確認。主担当の最終受入待ち。

主担当の受入を完了した。独立レビューは[34項目・指摘0](independent-review.md)、全件検証は[1,444件・36.744秒成功](parent-full-suite.json)。検証中の実DB124資料のSHAは不変。[受入記録](parent-acceptance.json)は変更コードと検証根拠を固定する。上のproducer時点の未受入記録は当時の状態として保持する。live接続・金融入力採用・外部schedulerは未実施。
