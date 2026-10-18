# 会社原EPSとQUICK換算EPSの比較・実レビューjob

ダイダンの2026年8月5日付1Q短信は、2027年3月期の会社予想純利益273億円・EPS211.42円を表示する。9月14日付QUICKレポートも会社予想純利益273億円を使うが、EPS210.89円はQUICKによる計算値である。同じ純利益の表示と異なる株当たり表示を確認した。利益見通しの不一致、著者独自の純利益予測、予測の優劣とは扱わない。

会社原本の物理p1/2を本文・画像で確認した。[5引用](quotes.json)に位置と画像SHAを保存し、残る11頁は機械抽出のみ。[比較記録](review.json)では年度、連結日本基準、予想据置、1:3分割注記、発行済・自己株・四半期平均株式数を区別する。会社通期予想の厳密な株数分母と、QUICKの観測日・株数との対応はこの2頁から確定しない。四半期平均株数を通期予想分母へ代入しない。既に公表されている純利益・年度・原EPSをIRで再質問しない。

旧公式ページの保存URLから、当該hostの新しいrobotsと指定PDFを各1回だけ取得し、ともに200・完全本文だった。合計2GET、リトライ・redirect・URL推測・別host探索0。form hostは別でありアクセスしていない。経路・robot照合・取得時刻と原バイトは[route](route.json)、[guard](guard.json)、[capture](capture.json)に固定した。原PDF SHAは`32da4fb2ec4c70e07bc702c8771f9af810cbf457cafd1b9839b61c78fafbb672`。新規取得の歴史的な初回保存時刻は不明で、現在の取得完了18:50:59 UTCとDB初回保存18:51:52 UTCを区別する。

資料を実DBへ1件保存して分類後、実際の`qualitative_review` jobを確保した。新PDFだけを凍結入力にし、既存caseの出所区分を支持する観測として完了。これは事業の強気判断ではない。[結果](qualitative-result-input.json)・[完了receipt](actual-completion.json)によりcaseはv1→v2、既読2→3、再起票0。旧source・会社・分類・case版は保持した。管理日は既存の2027年1月15日Tokyoを保持し、会社予定や売却期限へ転用しない。

最初の分類結果は未対応の`earnings_release`という種別を使って拒否された。旧入力と[訂正記録](classification-rejection.json)を残し、同一job・同一attemptへ既存の`financial_statement`分類を返して完了した。再取得・二重登録・新intake jobは発生していない。

完了時点の実DBは117資料（公開116・市場1）、分類116、完了job49（intake48・定性1）、attempt46/events92/receipt46。caseは12社13版。保存来歴はlegacy28/trusted89。金融thesis・正式質問・返信・実policy・明示保有申告・送信・注文は0。この1件のleaseは全工程の処理能力や投資成績の実測ではない。今回の意味・新コードの独立agentレビューは未完了で、1396件テストの受入範囲を広げていない。
