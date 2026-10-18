1975実intake後の正式v33接続確認です。旧proposal／builder／pinsは歴史のまま変更せず、[正式v33](../../../../disclosed-fact-index-v33.json)を別に作成しました。旧v32の36parent／171fact全objectを保持し、受入済み9表示値の1parentだけを追加しています。全体24社180fact／37parent／39派生source／30会社原典pair、実台帳37派生173fact、台帳外8331／9702の2派生7factです。

原PDFと派生を含む実1975の4source全object・native snapshot・現行分類・availabilityを、[実受入](../../../../../ir-1975-initial-with-facts-intake-2026-10-16/parent-acceptance.json)および[source-firstsave](../../../../../ir-1975-initial-with-facts-intake-2026-10-16/source-firstsave.json)とRO照合しました。4件の実初回保存は2026-10-16T04:37:22.269407+00:00。原HTTP時刻と派生処理時刻はそれぞれ元の値で、初回保存とは区別します。別の説明資料は実4source照合に含むだけで、新しいfact parentには混ぜません。

観測DBはSHA11b6ad2c…、190source／189分類／107全job完了、104attempt／208event／104receipt、pending／leased0、case21head／42版／125既読です。1975 native case登録前のsnapshotとして固定し、後日のcase増加を先取りしません。詳細は[validation.json](validation.json)に記録しました。

raw factの原source bindingをindexの派生source overrideへ転記せず、旧個別overrideも全保持しました。Q1実績と当時会社予想、DPSの当年合計セル・年度両端／基準日／GAAP／連結null、DDM採用false等は受入bundleと同じです。現在予想や金融入力への採用はありません。

[finalize_index.py](finalize_index.py)はSQLite URI mode=ro／query_only／contextlib.closingのみを使用し、Store／normalizer／reproducerを呼びません。DB前後SHA・旧proposal／全依存pins不変を確認。GET／実DB書込み／共有docs／production code／旧index変更0。root独立レビュー待ちで停止します。
