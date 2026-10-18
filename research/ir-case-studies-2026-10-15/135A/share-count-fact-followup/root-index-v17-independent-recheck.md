# v17株数1件追加の限定独立点検

記録: 2026-10-15T15:37:25.236186+00:00。v16の19entry/84recordsはv17先頭19entryとdeep-equal。追加は135Aの株数1factだけで、20entry/85records/15社/17会社・原source組の再計算とtop-level・親recordが一致した。説明とrevision_basisも今回追加を正しく述べており、追加問題はない。

全85factをper-fact優先/entry既定で22artifactへ解決し、path・SHA・source/原sourceIDと掲載fieldが保存bundleに対応した。新10256000sharesは期末発行済普通株（自己株を含む）の表示で、net・期中平均・希薄化後・現在評価分母へ採用していない。自己株dashは不確定のまま。cash2表示の既存entryは不変で、再抽出・再加算や独立資産化をしていない。

親recordの新旧index/既存独立レビューpath・SHAと件数も一致した。index→親recordはpathのみで相互SHA循環ではない。実DB原source一致/派生未import/DB mainSHA不変は親read-only記録として参照し、ここでDB再確認したとはしない。

原PDF・API再監査、GET、DB/Store、コード/テスト、旧file変更、金融/IR採用は0。旧v15/v16独立結果も保持した。詳細は [root-index-v17-independent-recheck.json](root-index-v17-independent-recheck.json)。
