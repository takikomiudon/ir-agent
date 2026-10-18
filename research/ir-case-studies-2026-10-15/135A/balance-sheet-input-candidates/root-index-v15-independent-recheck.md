# v15索引の限定独立点検

記録: 2026-10-15T15:26:44.164845+00:00。旧v14の18entry/82factsはv15先頭18entryとdeep-equalで、新規は135Aの1entry/2factsだけ。再計算件数は19entry・84records・15社・17会社/原source組で、top-levelと親recordの数値に一致した。全84factをper-fact指定優先/entry既定のartifact path・SHA・sourceIDへ解決し、索引に記載された各fact fieldは保存bundleと一致した。

1点だけ表示説明の修正が必要。v15の `layout_note` は旧v14のまま「18entry、previous17entry/75facts、新7facts」と記す。実際の19entry・旧18entry/82facts・新2factsと不整合である。数値recordsやcountsは正しく、旧v15/親recordを保持した別v16でこの説明と版chainだけを訂正する必要がある。旧ファイルは変更していない。

現預金/現金同等物の2表示は同じ既存135A原source・2026-08-31の138百万円残高で、加算資産や独立裏付けではない。モデルcash採用はfalse、株/debtのraw候補も新しい数値へ昇格していない。

親recordのindexSHA、旧indexSHA、既存独立レビューSHA、件数は対応した。index→親recordはpathのみ、親record→indexはSHAで、相互hash循環ではない。親の実DB原source一致/派生未importは親のread-only確認記録として参照し、この点検でDBを再確認したとはしない。

原PDF/元bundle再監査・API再実行・GET・DB/Store・コード/テスト・旧producer/source変更・金融/IR採用は0。詳細は [root-index-v15-independent-recheck.json](root-index-v15-independent-recheck.json)。
