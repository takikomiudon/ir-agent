# 1904の6factを索引v29へ追加

[v29](../../../disclosed-fact-index-v29.json)へ、受入済み1904の1parent/6factだけをappendした。[v28](../../../disclosed-fact-index-v28.json)の全32parent・144factはscope/period/valueを含む全fieldで完全保持し、旧fileを変更していない。現在の共有README/docsは更新していない。[親の独立受入](parent-acceptance.json)が完了し、v29/validationのbytesを固定した。

| 区分 | v29 |
|---|---|
| 会社 / fact / parent | 21 / 150 / 33 |
| 派生source / 会社・原典pair | 35 / 26 |
| 実保存・分類済み派生 / fact | 33 / 143 |
| file-only派生 / fact | 2 / 7（8331/9702、不変） |

追加の[normalized-bundle](../normalized-bundle.json)は、Q1実績3と年度会社予想3を別kind/期間のまま保持。会社予想は5月13日参照を8月6日に据置観測した履歴で、10月の最新性は認定しない。p7千円とp1百万円を混ぜず、後日の分割/配当や取得後の基準を移植していない。新DPSfact、DDM配当列、金融採用は0。

追加parentのsource_idは派生ID、各元factのsource_idは元引用source IDという契約を区別した。元factのsource_idを新たなfact別overrideとして写さず、既存fact別artifact/source_id overrideだけはそのまま優先する。索引の6factはid/concept/kind/period/scope/unit/valueを原bundleから保持する。

実DBはSQLite URI mode=ro・PRAGMA query_only=ON・contextlib.closingでだけ接続。原/派生source全objectの一致、索引の全33実保存派生にsnapshot SHAが一致する分類があること、171source/170分類/101completed jobs・pending/leased0、19head/39版/113既読を確認した。main SHAは前後とも `7ab7d8f54da46b0c95c3893be4454ec42b2f6aca903c2b440f94bfaf2ed1fa44`。Storeやschema初期化、実DB書込みはない。

[実source登録receipt](../actual-connection/actual-completion.json)と[定性完了の親受入](../qualitative-review/parent-acceptance.json)を索引のconnection_receiptsへ追記。実保存first-saveと派生retrieved_atもvalidationに分けた。これらは研究資料の保存・分類・限定比較であって、金融入力や予想の正しさの採用ではない。

`build_index.py` は既存v28 builderを参考にしたfile-only生成コード。実行は1回成功。既存出力があれば上書きせず止まり、追加のコード検証・GET・source生成・索引外の共有文書更新・投資判断は行わない。入力SHAと不変性/件数/実source照合はvalidation.jsonに保持した。

- v28 SHA: `f9bb65d68e4037eba3e75d1aec8223b4eb4f3c414e940f4b87487fcad5b88fe9`
- v29 SHA: `105c79dc46d1543b56d35f32c447dadd1da407a481ba4ecf1f540d2aa0e5f234`
- validation SHA: `29cc6247b81ac7f7907e4a02c6c7c09dc72e829d74aca868d542eeb87b539062`

旧1904固定file不変、新GET・実DB書込み・production code/共有doc変更・金融採用は0。別phaseの円銭対応には触れていない。
