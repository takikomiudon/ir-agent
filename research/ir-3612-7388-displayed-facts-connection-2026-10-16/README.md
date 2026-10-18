# 3612・7388：表示3値の実保存

ワールドの年次1株利益171.36円、FPパートナーのEPS88.79円・BPS508.60円を表示factとして保存した。原典2件は既存のまま、新派生2件だけを追加し、intake2件を完了した。rootは該当画像、固定normalizerの全bundle再現、原典の既存DB objectとの一致を確認した。

3612は2026/2列・翌3月分割遡及調整/IFRS18反映表示を保持し、BPSは補完しない。7388は2025.11列・分割調整注記を保持する。日付端点や未確認の会計/連結/普通株・平均末分母を埋めず、7社Graham入力集合・計算・金融採用・新native case・正式IRは増やしていない。

実DBは255source（公開254/市場1）、254分類、全168job完了。既存27tableの全旧行とschemaを保持し、native32case/72版/187既読は不変。[実照合](actual-verification.json)・[root受入](parent-acceptance.json)・[入力と原典照合](root-preparation.json)を参照する。[索引v42](../ir-case-studies-2026-10-15/disclosed-fact-index-v42.json)への接続も完了した。35社250fact・52親entry・54派生source・会社/原典45組、実52派生243fact（対象外2派生7factはfile-only）。[接続のroot受入](index-connection/parent-acceptance.json)に従い旧v41全体・active connectionは履歴保存した。成功したconnect.py actualは再実行しない。
