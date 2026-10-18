# 5988：年次B/S・P/Lの公表14値を構造化

保存済み有報p63/64/65の両期14値を、既存 `normalize_disclosed_facts` APIでreported_factへ構造化した。原会計名を保持し、百万円→JPYの明示換算のみ。営業利益をEBITへ改名せず、税率/NOPAT/ROC/EY/EV・評価額の計算や金融モデル採用を行っていない。

| 原会計行 | 前期/当期のraw表示（百万円） | 原頁/引用 |
|---|---|---|
| 流動資産合計 | 64,398 / 58,140 | 物理63・印字60 / Q63 |
| 有形固定資産合計 | 33,572 / 35,836 | 同上 |
| 流動負債合計 | 12,218 / 33,541 | 物理64・印字61 / Q64 |
| 営業利益 | 2,382 / 1,470 | 物理65・印字62 / Q65 |
| 税金等調整前当期純利益 | 3,402 / 763 | 同上 |
| 支払利息 | 14 / 254 | 同上 |
| 法人税等合計 | 1,549 / 769 | 同上 |

B/Sは2025-03-31と2026-03-31の時点。P/Lは前期2024-04-01〜2025-03-31、当期2025-04-01〜2026-03-31の連結年次flowとして区別した。法人税等合計は会計上の税費用で、現金税/正常税率/営業税率ではない。百万円表示の端数処理/未表示精度はこの表引用だけでは未確定で、JPY換算を未丸めの正確経済額としない。会計基準は各表引用内で独立再確認していないnullを保持し、既読p26の会社説明を旧fact/sourceへ追記していない。

`normalization-input.json` の/sourceは `tax-disclosed-facts/normalization-input.json` の/source全文・全metadata・ID・公表/取得欄をobjectとしてそのまま再利用した。native/canonical両serializationのSHAも一致。primary原本IDは `case-public:5d5a98a7770af91318e9bb24fd4bdac483b20cb5fc96a79f58474dbd77f57365`、raw SHA `813f6500cd7716a3b527273c6817aeb507800030063847c35963cac4c72c74e4`。

派生IDは `disclosed-facts:1fce07909a0b48066cb45e14c7b72920922a97f859d1efe6b3589f49dd23c94b`。**2026-10-16T00:02:48.027200+00:00は派生bundle生成時刻/派生source retrieved_atであり、実DB firstsaveではない。** 抽出担当のreview時刻00:02:48.023432とは別に保持し、会計値の作者は会社と区別した。実DB接続は0。

`quotes.json` は同一原全文からの連続3引用で、単位・前当期の見出し・日付/期間・対象行を含む。文字/UTF8 byteの半開offset、各factの列/行、既読画像SHAを保持。`normalized-bundle.json` は原典1＋派生1の標準bundleで、company/thesisは空。既存v25の107factとID及び同社同概念同期間の重複0を照合し、索引や既存13fact/33行discoveryは変更していない。

`reproduction.json` / `reproduction.log` に、モデル入力audit内部と共通の `reproduce_disclosed_fact_source` による実再現を保存した。status=reproduced、原文SHA/原snapshot SHA一致、financial_inputs_verified=false/meaning_review_required=trueを維持する。`audit-source-paths.json` は標準派生sourceの各value_path参照メモで、金融parameter割当や完全model-inputs requestではない。audit用の仮valuationや未設定値を作らず、モデル意味/現在適合の検証・採用は親の別手順に残す。

`validation-normalization-stage.json` は実API処理直後のreceiptで、reproduction.log末尾の当時validation SHAに対応する。最終 `validation.json` に全input/成果物のSHAと凍結状態を残す。stdoutの新規temp logを一度専有dir隣へ作成し、直ちにこのdirのreproduction.logへ移動した。既存file変更やGET/入力値の失敗ではなく、成果物は現在このdir内だけにある。

新GET・実DB・normalizer/その他sourcecode・共有docs/索引・原source編集・IR質問/外部送信・金融モデル採用はいずれも0。独立意味レビュー/実DB保存は未実施で、本成果を凍結して引き渡す。
