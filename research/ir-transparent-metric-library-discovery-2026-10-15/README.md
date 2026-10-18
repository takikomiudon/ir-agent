# maxgfr/crible：指標定義と再利用条件の入口確認

**公開の定義文書・計算コード・データ出典へ進む具体的な候補を特定できた。日本株の実coverage、ROIC等の正しさ、公開入力だけでの再現性は未確認。** 既存候補4だけを最大4GETで調べ、4GETすべて200で終了した。他候補・検索・依存library・外部financial dataへ広げず、候補コード本文は取得・読取・import・実行していない。

固定commitは `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7`（default mainの1件commit metadata）、treeは `75acd2016e99c176ac177c56bf1ec75406073454`。recursive treeは283entry、truncated=false。root README.mdとLICENSEは各1候補で、treeのliteral blob URLから取得しGit blob SHA-1とdecoded byte数を再計算照合した。[fixed-selection.json](fixed-selection.json)に元候補・commit/tree・README/LICENSEを固定。

## 確認した記載と未確認

| 論点 | README／licenseが示す範囲 | 今回は示せないこと |
|---|---|---|
| 日本株coverage | README:181,241–247は世界117国・多数の上場銘柄universeとUS/EU中心の財務coverageを説明。README全文では日本固有のmarket・銘柄・会計coverageを確認できない。 | worldwide listing検索可能性は、日本銘柄の財務・株式分母・期・通貨・JGAAP/IFRS入力が充足する証拠にならない。日本非対応と断定もしない。 |
| 指標の透明性 | README:193–198はFinanceToolkit利用と自前モデルを分け、公式名称の指標定義文書へのliteral linkを置く。223–225はmagic-formula rankの構成をEBIT/EVとreturn on capitalとして説明する。 | このreturn on capitalを税引後ROIC/NOPAT方式と同一視しない。EV調整、資本分母、税、TTM/年次/単Q、会計範囲の実定義は未読。文書存在の説明は実装正しさ・再現性の検証ではない。 |
| 欠損 | README:215–217は複合rankのpillarで欠損をNULLに保つ処理を説明する。 | 全財務指標・生データ・全providerの欠損処理が同じと一般化しない。 |
| 出典 | README:181–203はuniverse/data提供元、local mirror、データの2tierと利用条件文書を案内する。 | 全入力が原典まで追跡可能、private前処理不要、無料または利用許可取得済みとは確認していない。zero API keys等の宣伝はAPI不要・provider規約免除・日本株財務検証済みを意味しない。 |
| 再利用 | [LICENSE.upstream.txt](LICENSE.upstream.txt)はMIT本文、copyright 2026 maxgfr。ソフトウェア・関連文書の利用/複製/変更/配布等を認め、著作権と許諾文の保持を条件とし、保証をしない。 | repoのMITはYahoo等のデータ・商標・依存物の利用許可を一括付与しない。コード未読なので個別file/依存物の追加条件も未監査。導入・転載・金融方針への採用は今回0。 |

上記は独立maintainerの説明で、Greenblatt本人の実装承認や日本株適用許諾ではない。取得README中のinstall/agent instructionsは分析データとして保持し、実行していない。

## 次に必要なliteral source候補（最大3、未取得）

| path | 固定Git blob SHA | 選択理由 |
|---|---|---|
| docs/INDICATORS.md | b111f51c9d4b19602cf8acb654c297b874e178af | READMEが式・解釈・留保の文書と明示。ROIC/return on capitalの違い、EV/EY・F-score、税・期の定義を先に確認する。 |
| src/crible/compute/ratios.py | f92d8ab900bec291390dd7668fac66c70f0109d7 | 固定treeのliteral計算path。定義に対応する分子・分母・期・税・null伝播が本当に公開実装されているかを限定確認する候補。ファイル名だけで実装内容は認定しない。 |
| docs/DATA-SOURCES.md | fd3ca97772825e81328357c6b853265545adbd9e | READMEがprovider・利用条件・データtierの監査文書と明示。公開入力と会社/期/単位対応、再現経路、coverage不足の切分けに必要。 |

literal API blob URLとtree由来は[next-source-candidates.json](next-source-candidates.json)。この3つを読めばprivate前処理依存の不足を解ける**可能性を具体化した**段階で、解消済みではない。式の研究と、既存日本株sourceへの実入力binding・売買規則の採用は別。ライブラリ導入を提案・実行していない。

## 原証拠・規則・取得範囲

[guard.json](guard.json)に既存候補4のSHA、holds-v8の12 exact hostとの照合、GET予算と固定routeを保存。api.github.comは保留外。既存GitHub robotsの完全404（106bytes、SHA edbd0367cec893df36f67acb56c3aa23810be28850977c35e0fedaf64aad286b、完了2026-10-15T23:01:26.802572+00:00）を再利用し、新robots GET0。404を明示許可とはせず、既存未配置扱いを適用した。UAは再利用captureと同じCodex-IR-Research/0.1を維持した設定値で、wireの独立確認ではない。

GET順はmainのcommit list（sha=main/per_page=1、patch本文を求めないmetadata）→固定tree recursive=1→literal README blob→literal root LICENSE blob。個々のHTTP entity・SHA・byte数・開始/応答/終了時刻・response metadataを01–04 captureとraw/へ保存した。rawはrequestsのresponse entityであり、content-decodedの場合があるためwire転送bytesとは言わない。decoded README/LICENSEも原bytesのまま保持。

[readme-evidence.json](readme-evidence.json)に最小の逐語quoteと位置、[validation.json](validation.json)に4raw/SHA・blob SHA再現・完了時計・source SHAを記録。英語の生成原文引用は90words未満。新search/route変形/retry/redirect追跡/他host・repo/依存取得・実行/DB/共有file編集/新金融値/質問/外部送信は0。この有限確認を終了する。
