# 5988：2026年3月末の直接BPS 1値

保存有報の物理p103/印刷p100「１株当たり情報」にある、**当連結会計年度末2026-03-31の１株当たり純資産額2,672.60円**を1factだけ構造化した。同じ頁の前年度値やEPSを新factにしていない。既存5988の正規化6値（EPS/DPS 3値と今回の四半期財政状態3値）に同BPSの重複はなかった。

表の当連結会計年度列、BPS行、円単位を原文tokenのまま保持し、canonicalは`2672.60 JPY-per-share`。同頁の算定基礎表から、当期期末・普通株式の範囲を確認した。株数や純資産から再計算せず、表示小数2桁を未丸めの社内精度とは扱わない。2026年6月末や現在のBPS、現在PBR、本源価値・清算価値へ持ち越さない。

**会計基準の確認は未完了。** 当該p103は連結範囲を直接支持するが、日本基準という明示ラベルは同頁にはない。別のQ1短信の日本基準表示を有報へ移植せず、`scope.accounting_basis:null`と確認範囲内ではunknownの理由を保存した。今回の1頁制約で日本基準まで独立確認済みとは主張しない。隣接頁は不要だったため開いていない。この不足があっても既存normalizerは申告descriptorの不足を保持してtoken/単位を構造化でき、金融意味は未検証のままである。

## 原本と保存来歴

原典URLは `https://www.piolax.co.jp/jp/wp-content/uploads/2026/06/20260618_2025-q4_report.pdf`。既存ファイル`data/case-source-bundle.json`の`sources[18]`からprimary snapshotを完全copyし、推測でmetadataを再構成していない。実DBは開いておらず、同snapshotの実DB存在・同値はrootの後続確認対象とした。

- Primary ID：`case-public:5d5a98a7770af91318e9bb24fd4bdac483b20cb5fc96a79f58474dbd77f57365`。
- 原PDF：`../raw/813f6500cd7716a3b527273c6817aeb507800030063847c35963cac4c72c74e4`。SHAはファイル名と一致。
- 既存text：`../11.txt`、SHA `a9acbc3544e789cae8369d1e45f02747928fadda584c1839780a12a55fe4bd01`。primary contentと改行を含め同値。
- 既存transport snapshot：`../11.json`、SHA `9fe5f764785c119f413c66b7879c4b599060fd473a1e40f371f8f3f6c2a9f96a`。原metadataとの一致を確認。

保存済み取得時刻2026-10-15T01:12:38.091035+00:00を保持し、HTTP本文完了・実DB初回保存日時へ再解釈していない。公表日付metadataは2026-06-18、公表時刻不明の`published_at:null`を維持する。派生sourceは今回の処理時刻とし、原典取得時刻へ遡及しない。

## 成果物と検証

[normalization-input.json](normalization-input.json)、[normalized-bundle.json](normalized-bundle.json)、必要最小限の表ヘッダ・期・BPS行を保持した[quote.json](quote.json)を保存した。quoteには原text SHA、文字/UTF8 byte offset、表行列・物理/印刷頁、確認画像SHAを付けた。`images/physical-page-103.png`を視認し、右側の当期列の値と確認した。

既存normalizerと再現APIをメモリ内で使い、1fact・値`2672.60`、source schema、原primary同値、引用offset、原raw/text/transport SHA、原典1sourceだけの依存閉包、`reproduced`を確認した。全`financial_inputs_verified:false`、`meaning_review_required:true`、companies/theses空を維持する。値・対象期・列・会計範囲の意味は担当者の読取りであり、engineの独立認証ではない。

[validation.json](validation.json)に根拠と不足を記録し、作業開始前の既存5988ファイル73件のSHA不変を確認した。新GET・実DB操作・索引更新・既存file/本番code変更・金融採用は0。root受入待ちで凍結する。
