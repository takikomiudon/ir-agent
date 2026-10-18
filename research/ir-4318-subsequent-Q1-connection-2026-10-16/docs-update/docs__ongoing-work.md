# 継続作業の状態

更新時刻：2026-10-16T16:29:52.949443+00:00。利用者の停止指示があるまで目前のタスクから進める。過去の段階別記録は[移動前の全文](research-history-2026-10-16-through-1628.md)に保存した。このページの現在値を過去snapshotへ上書きしない。

## 利用者の指定

- 保有期間は数カ月〜1年。投資スタイルは指定なし、公開ルールとの適合を優先。
- 積立額は月1万円。証券会社はSBIを継続利用する想定。[回答原文と解釈](../research/ir-user-operating-constraints-2026-10-16/constraints-v2.json)を保持する。
- 現在残高・初期資金・1社配分・口座区分・S株利用設定は未確認。月額から補完しない。
- 既存著者の方針を優先し、予測・倍率・確率・投資閾値を独自に埋めない。サブエージェント利用は許可済み。
- IRの実送信・注文・有料契約・deploymentは指示されていない。

## 現在の実台帳と実装

実DBは `data/ir-research-2026-10-15.sqlite3`。最新の変更は[4318報告PLの接続](../research/ir-4318-reported-PL-connection-2026-10-16/parent-acceptance.json)。SHA256は `03ec438048a00efedaf91120eef087d34cd80523001d639b0b75fd56808c3d6d`。

| 項目 | 現在の状態 |
|---|---|
| 会社 | 1,819社。watch/held:falseを実保有申告としない |
| 資料 | 262件（公開261・市場1）、分類261・availability262 |
| job | 181件全完了（intake136・定性45）、attempt178・event356・receipt178 |
| native監視 | 34case・80版・198既読。4318はv5/config1・5既読 |
| 研究IR | 7388・135A・7525の3draft、全未送信/no_reply。返信・レビュー各0 |
| 金融判断 | 数値thesis・実policy・正式金融質問/返信・明示保有・研究判断記録・送信・注文0 |

[索引v43](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v43.json)は35社254fact・53親entry・55派生source。実53派生/247fact、対象外8331・9702の2派生/7factはfile-only。4318のPL4行は年次報告値であり、正常EPS・OIADP・TTMへ自動変換していない。表示差2千円の原因も未確認。

コードの最新受入は[全1,641テスト成功・独立必須指摘0](../research/ir-research-inquiry-worklist-integration-2026-10-16/parent-acceptance.json)。研究IRの全返信作業一覧を追加し、古い未レビュー返信を後の返信で隠さない。以後は資料/文書作業のみで、同じ全suiteを再実行していない。

内部管理日は2027-01-15が12case、01-16が22case（Asia/Tokyo）。会社の決算予定や売却期限とは別。外部scheduler・定時Web取得・LLMの定時実行は未設置。[研究段階の監視](research-stage-monitoring.md)と[日付のみの材料監視](catalyst-monitor-design.md)を再利用し、新情報なし・未確認なし・管理日未到来のcaseで同義のpreview/jobを増やさない。

## 採用済みの基礎と現在の限界

[研究ベースライン](research-baseline.md)は外部公表のJPX中小型200社→保存IR候補121社→個人明示23社を研究集合として使用する。1975は既存資料を再利用する接続例であり投資順位ではない。原一覧の適用予定と現在の構成認証を区別する。

[判断方針](decision-policy.md)のAnthropic等の仮説/反証/3シナリオ/四半期点検を研究手順に採用している。Graham Numberは7社の年次実績EPS/BPSから価格なし参考計算まで可能だが、原Grahamの全適格条件や売買規則の実装とはしない。Tweedyの価値到達時点検、Buffettのowner earnings、CarlisleのEV/Operating Earnings・退出条件は原文確認範囲と日本適合の不足を残す。研究手順・計算式の参照と、会社別金融入力・実行policyの採用を区別する。

[月1万円・SBIの実行条件](monthly-sbi-execution-research.md)は公式7GETを終了し、1株単位・積立との違い・対象市場・NISA成長枠・時間別約定・ネット取引の費用/spreadを確認した。本人への適用、銘柄別取扱い、余力、実約定は未確認。[市場との結合](../research/ir-SBI-market-IR-universe-fit-2026-10-16/parent-acceptance.json)では歴史一覧1,819社すべて東証3市場、追加市場除外0。現在上場/個別S株取扱いは未確認で、最低20保有等の著者条件を月額に合わせて変更していない。

## いま進めること

1. **研究IR3件と次の公開観測を接続する。** [3件の最少action比較](../research/ir-three-inquiry-next-observation-gap-2026-10-16/README.md)は受入済み。会社定義の確認後も、採用する方法がどの入力・条件へ使うかが残る。次は保存済み公式一覧だけで後発公表資料のcoverageを点検し、現在の質問の前提が変わっていないか確認する。 [既存確認パケット](../research/ir-three-draft-review-packet-2026-10-16/README.md)、[質問準備](ir-question-preparation.md)、現在のcase/inquiryを使い、回答で変わる比較、次の公表で検証できる事実、数値判断までに別途足りない入力を区別する。価格待ちだけで完成するとは決めない。新草案・独自順位・分岐の後付けはしない。
2. **4318の後発Q1を最小範囲で確認する。** 既存C3は後発資料本文が未取得。保存一覧の2026-07-31公表Q1 literalと完全robots/holdsをGET0で確認済み。単一PDFの新taskを上限1GETで確認中。対象期/年次との区別、会社予想の版、株式basisに必要な最少頁を特定してから有限取得する。年次EPS74.11/BPS345.24をQ1値で置換・年率化しない。
3. **株価は利用可能な正規データ経路が判明してから進める。** 利用者へ既存API契約の有無を任意確認中。新しい有料契約を前提にしない。利用可能になった場合も、同一銘柄/通貨/価格日・精度/株式basisを確認し、明示方針で採用する。
4. **将来の実返信を事前分岐と照合する。** 未送信3件は送信readyではない。受信時は原文・公開根拠・case版・対象期を別に確認し、曖昧/拒否/無回答を悪材料へ変換しない。金融入力が変わる場合は既存の正式金融契約へ進む。

## 閉じた経路を繰り返さない

公開GET前に[収集保留v9・13host](../research/ir-source-access-holds-2026-10-15/README-v9.md)を確認する。旧12hostにquery1.finance.yahoo.comを追加した。robotsの全体禁止でchart取得0。query2/別UA/ミラーで回避しない。

JPX公式株価検索は入口まで2GETで終了。動的検索の契約を確認できず、表示上の蓄積/加工制限も保持した。1975検索/価格取得0、JS/API/パラメータ推測へ進めない。cribleの取得・表示コードは参照のみで実行していない。[保存レポート5社の価格調査](../research/ir-saved-author-report-price-inventory-2026-10-16/parent-acceptance.json)で得た135Aの5月11日4,190円・9702の8月21日2,480円は歴史参照で、現在価格へ転用しない。

SBI条件取得、3draftのprivacy/窓口調査、ASBJ導線、PEAD原著、以前の503停止経路、全23社の年次入力経路、16社の基礎調査経路は各有限taskを終了した。新たな判断用途なしに再取得・別経路探索・全社再巡回へ戻らない。詳しい当時範囲と受入リンクは[移動前全文](research-history-2026-10-16-through-1628.md)にある。
