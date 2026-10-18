# JPX公表・適用予定構成とのIR窓口の交差（現構成未認証）

JPXの**2026年8月7日公表・8月31日適用予定**の200行と、保存済みIR窓口台帳をコード完全一致で突合した。予定日経過を実施/現在構成の証明にせず、指標採用・割安判断・売買・投資順位・研究処理能力の推定はしない。

| 保存集合との交差 | 社数 |
|---|---:|
| JPX公表予定構成 | 200 |
| 保存全社台帳3686への一致 | 200 |
| IRメール/フォーム確認済み候補1819 | 121 |
| うち個人受付明示の固定343 | 23 |
| 全社台帳未収録 | 0 |

[個人受付明示23社](fixed343.csv)／[受付候補121社](ir-accepted.csv)／[全予定構成200社・保存status付き](published-plan-all.csv) をUTF-8 BOM付きCSVで保存した。窓口URL・方式・メール・受付status・個人条件・制約・確認日時・元CSV行・source_record、DB保存coverageが参照できる。[intersection.json](intersection.json) は元コード/JPX会社名/台帳会社名・原典span・全入力SHA・定義も保持する。社名をjoinに使わず、コードだけをNFKC→外周trim→大文字化して4文字英数字のまま照合した。166Aも変換/整数化しない。表示順は原PDF順で投資順位ではない。

受付候補外79社は **未確認42、暫定32（candidate12・unconfirmed20）、確認済みだがrestricted1、取得エラー保留4**。保留は2154・3964・3989・9682。窓口不存在/投資除外にはしない。121社の個人条件はexplicit23・not_stated98で、未明示を許可/拒否へ読み替えない。1819はcompleted+confirmed+candidate集合で、全台帳のconfirmed1844やexplicit355をそのまま使わない。保存窓口は10月11〜13日の調査時点であり、今回現在受付の再検証は0。条件と回答保証の限界を残す。

公式200行はroot受入済み原典 `ir-jpx-smallmid-constituents-2026-10-16/constituents.json`（取得08:19:45.150439UTC）を使用。公表日・適用予定日・取得日・現在構成未認証を別fieldで保持し、JPX原文/旧窓口/共有docsは変更しない。

[coverage-snapshot.json](coverage-snapshot.json) は **2026-10-16T08:25:15.753988+00:00** の実DBをmode=ro/query_only/closingで一括確認した結果。210source/26case heads/48versions、main SHAは前後とも `cbf81671f41ec320a4b08c96df53520e5300ffffbc5530e10bcba1d88f60b7a8`。200社中public_disclosure保存あり4社（1518/1723/1975/5480）、nativecaseあり3社（1518/1723/1975）。publicsourceには原典・派生fact・indexHTMLを含み、金融採用/読了ではない。未受入file-only研究はDBcoverage外なので、source0を未調査/公表資料不存在とはしない。

[read-only再現script](join-readonly.py) は凍結したmembership/台帳/coverageだけを読み、JSON+3CSVをbyte単位で再現する。GET/DB接続/書込はしない。DBsnapshotの再観測とは別で、SQL定義はsnapshotに保存した。

```bash
python research/ir-jpx-smallmid-ir-universe-intersection-2026-10-16/join-readonly.py --check
```

今回の新会社GET/DBwrite/Store/旧file・production編集/金融採用/送信0。この7fileでfreezeしroot受入を待つ。
