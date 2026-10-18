# 2983 著者資料の実台帳保存

元source object不変の2件を保存し、1つの会社intake jobで分類した。全旧source/分類/会社metadataは不変。global tosは会社sourceへ割り当てずfile-only参照（1723）、2983の英語NI単位は訂正追補を参照し元sourceを変更していない。

このbatch完了時は108資料・分類107・完了job43。[実保存記録](actual-import.json)に各sourceのtrusted first-save・旧行不変・DB SHA、backupとclaim receipt/packet/結果を保持する。分類lease1件は全研究の分析時間ではない。

[親の後続coverage](coverage-summary-at-parent-review.json)は現在108資料（公開107・市場1）、公開18社/財務内容17社。著者予測・条件の記録と金融モデル採用は別で、正式thesis/policy/IR/売買は0。会社同期間原本との比較はこのbatchの分類対象ではなく後段で扱う。
