# 2341：公表数値索引v36へ実資料を接続

**root受入済み派生資料をlive read-onlyで照合し、共有v36を新規作成した。** [索引v36](../../../disclosed-fact-index-v36.json)は27社214fact・40parent・42派生source・33会社原典pair。そのうち40派生207factが実保存・分類済み、対象外8331/9702の2派生7factはfile-onlyのまま。

旧v35の39parent/202fact全objectと個別artifact/source overrideは不変。受入済み[file-only準備候補](../index-connection-preparation/README.md)も全bytes不変で、falseのまま履歴として残した。正式v36の新entryだけimported_into_actual_database:trueにし、その他12factsのid/concept/kind/period/scope/unit/valueは全て候補と一致。原fact.source_idの原短信IDをindex overrideへ移さず、新factはenclosing派生IDへ解決する。

2341の中間実績（千円P/L・通常EPS）と当時通期会社予想5値、中間DPS0・年間予想total5.00、配当日付/基準日/GAAP/連結null、税/NCI・特別益・自己株式の範囲をそのまま保持した。新正規化/再計算/予測・正常利益/金融採用は0。

## 実照合したもの

mode=ro/query_only/contextlib.closing、Storeなしで原短信と派生の全JSON objectをaccepted bundleへ照合した。2資料の最新分類全input fields（kind/financial_content/basis_quote/rationale・version・native SHA・inputs_verified:false）とavailabilityのsnapshot/firstsave/presence/basisを、元要求およびroot実intake受入へ照合した。派生actual source.content内12factsもproducer全factsと完全一致。

- 原典: case-public:5bba6d…、native7d1775…、実firstsave2026-10-16T06:27:32.516249+00:00。
- 派生: disclosed-facts:706384…、native8de58b…、実firstsave2026-10-16T06:38:21.789206+00:00。
- 両方trusted_insert。原HTTP取得/派生処理時刻、公表日精度とは別で、元source metadataをこのために書き換えていない。

全42解決先について実保存/分類snapshotを確認し、40実source/207factsと対象外2source/7factsを数えた。対象外の会社・fact・source列は旧v35と完全一致。source2件だけの確認を全42の財務的意味認証へ拡張していない。

DB main SHAは `206575b65cfba0876b277656bc253f02cd43cc4116d107058c42d61d33b86c5b` のまま。live snapshotは205sources/204classifications/114全完了jobs、111attempts222events111receipts、case24heads46versions142reads。2341native case登録前という時点を明記し、後の状態を先付けしていない。pending/leased0。WAL modeのためmain SHAだけに頼らず、SQL全27表の型付きrow multiset fingerprintとsqlite_master schema digestも前後で完全一致を確認した。rawDB copy/backupは作っていない。

v35のactual_research_source_connectionsは別のhistorical snapshotとして全field保持した上で、v36のcurrent connection counts/receiptsを更新した。過去の201source観測を現在の205sourceへ遡って書き換えた記録にはしていない。actual-source-proof.jsonに2source原物/分類/availability、全42解決先、全27表/schema、件数を保存した。

## 実行と固定

build_index.pyは新sharedv36/validationが無い時だけ一度実行できる有限writerで、DBはread-only。受入最新src44filesと一致し、code-pins.jsonに保存した。source/bodyの再抽出、Store/normalizer/reproducer/GET/DB mutatorは呼ばない。共有fileに対する自動再実行/上書きはしない。

今回の書込みは新規共有v36とこのconnection folderだけ。旧v35/candidate/他社旧値・docs・production・DBは不変。source分類・仮説/ケース/ジョブ・金融方針・IR/注文を変更していない。manifestとproofを固定しrootレビュー待ちで停止する。
