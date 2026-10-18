# 現在表示の仮説版整合

全1077テスト成功（34.187秒）。株価の時刻条件がfreshでも、会社の仮説が更新されていれば、旧版への判断を現在候補として表示しない。金融入力や方針の閾値を変更せず、保存reviewの版と現在DBの最新版を機械的に比較する。

不一致/解決不能はrequires_thesis_reviewと現在action unresolvedへ回し、historical_resultと旧版/現版を表示する。情報・版・価格の保留を併記し、その順に優先表示する。旧IR分岐の新仮説への自動適用や再計算はしない。新review側の既存版guardも維持する。

[別担当の再確認](independent-recheck.json)で価格がfreshのv2→v3、current view/evaluation・両再送・CLI show・inboxの保留、旧exitと全DB dump/total_changes不変を確認した。[成功ログ](tests.log)とコードhash、元の未修正再現も保持する。実台帳は変更せず、実送信・注文はない。

このcheckは現在DBのraw最新版との版照合であり、金融妥当性・過去状態の完全再現・将来版の採用可否を検証した意味ではない。次はAWS/Google公式指針に沿うclaim/renewの要求receiptを実装する。
