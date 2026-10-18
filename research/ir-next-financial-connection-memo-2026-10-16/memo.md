# 次の1件：2983のIR回答からEPSを変更できる範囲を固定する

作成・固定時刻: 2026-10-16T04:28:05.518682+00:00。対象は `jp:2983` / `2983-author-watch-volume-margin-leverage` / `2983-B01-volume`。提案メモ1件であり、予測採用・金融モデル・質問の登録や送信は実施していない。

## 選ぶ不足は1つ

**会社の受注集計定義を確認する回答と、外部著者のEPS予測を変更する権限・根拠との間に、経済的な対応がない。** 公開レビューのSHA/範囲を質問へ固定する技術的な不足G1は別途受入済みで、再実装対象ではない。現在の不足は資料数や回答保存形式ではなく、「どの回答を、誰のどの予測値の改訂として扱えるか」である。

2983では、2026-10-01付Astrisの直接公表EPS候補が実在する。既存の適用性点検は1/27E **308.31円/株**を著者自身の予測として同定済みで、会社予想304.27円の転載とは別である。精密な将来株数の未確認を理由に、この完了済み点検を再開しない。対象期の厳密日付・全EPSの分割/希薄化basis等の限界は既存記録どおり保持する。[EPS]

一方、既存草案のAは取消等控除後の系列、Bは総額/後期調整/商品差、Cは未解決を区別するだけで、3分岐すべて `valuation_inputs_changed: []`、`financial_input_paths_assigned: null` である。[Q] 著者p8は販売棟数増・上期並み粗利率・販管費効率を予測前提としているが、**取消定義のA/Bから販売量やEPSを何円改訂するかを示していない**。[A] したがって定義が明確になることは比較の前進であり、EPS上方/下方修正や買い/売りの証明にはならない。

## 根拠として借りる手順と、本提案の区別

- Anthropic earnings-previewの “always note the source and date of estimates”（固定原文70行）は、予測の作者・版・時点を残す根拠。thesis-trackerの反証可能性・反対根拠の追跡（63–64行）も維持する。これらは取消率やEPS改訂係数を指定していない。
- Damodaran `damodaran.valuation-project.spring2025` p4の “Tie your narrative to key numbers that you will be using in your valuation.” とp8の新情報後の再評価が、説明から入力への対応を先に定める根拠。[D] 取消→EPSの式や本件の採用倍率を著者に帰属させない。
- 以下の1件の票は、この採用済み手順を当社案件へ適用する**projectの作業設計**。新しい全社共通gateや金融ルールではない。

## rootが実行できる最小の次作業

**既存資料だけで、2983の「基準EPSと回答別変更範囲」の1件のfile-only契約票を作る。** 新GET・原PDF再監査・コード変更は不要。

| 票へ固定する部分 | 既存根拠から埋める内容と境界 |
| --- | --- |
| 基準にする1入力 | Astris・2026-10-01版・印字期1/27E・EPS308.31円/株・実在する既存fact/source/quote参照。既存候補を**当該論点の dated research baseline**として使う採用者/適用用途を記録する。選ぶ用途はその著者前提を点検することに限定し、評価年度の選択や完成済みvaluationとは呼ばない。適合する既存著者予測のこの限定採用に、追加の利用者承認を仮想要件として置かない。 |
| 既存回答の効果 | A/Bは該当系列の定義・比較可否の注記だけ更新。Cは未解決理由だけ。EPS値・著者の旧予測snapshotはいずれも変更しない。返信後に古い予測を「最新」と呼ばず、予測前提の再点検と予測数値の改訂を分ける。 |
| 数値変更を可能にする根拠 | **同じ対象用途に適用できる、作者が明示した改訂EPSとその版・時点**、または作者自身が明示する取消/販売計上から予測入力への計算仕様がある場合のみ、その根拠を別欄に固定する。今読んだ既存記録ではこの回答に対する計算仕様は未確認なのでnull。会社の集計説明を、Astris自身の予測改訂としない。将来の新しい著者EPSがあっても、その改訂が当該IR回答によって起きたとは別途証拠なしに主張しない。 |
| 今回の到達点 | 「定義の回答は比較注記まで／研究基準EPSは作者の版付き直接予測／EPS数値改訂根拠は未充足」を1票で確定する。基準EPSの同定待ちと、回答に対する数値改訂仕様の欠損を混ぜない。 |

基準EPSを1つ固定しても、公正倍率・現在価格・費用後売買条件・退出条件が揃うわけではない。この票ではそれらを埋めず、既存 `2983-investor-input-adoption` の別範囲を維持する。価格から公正PERを逆算する探索、閉鎖済みEPS適用性点検のやり直し、会社へ外部著者の意図を保証させる質問は次作業にしない。[EPS, O]

## 有限の検証と完了条件

1. 既存EPS点検→既存fact/source/quoteを参照して、作者・版・印字期・308.31という原値・単位を1入力として照合する。新計算や未確認basisの補完をしない。
2. 既存A/B/Cをそのまま票に写し、A/BでEPS不変、CでEPSゼロ化/悪化判定なし、いずれも売買action未設定を確認する。架空のIR受信記録や返信尤度は作らない。
3. 著者前提3項目から取消定義→販売/利益/EPSへの係数・算式を読めない場合、改訂根拠nullを**この票の完了結果**にする。無期限の追加探索や、独自感応度の作成へ進まない。
4. 既存元ファイルのSHA不変を確認して1票を固定する。公開で解ける問いは先に閉じる既存手順を維持し、金融判断を変える質問としては本草案を送信readyへ昇格しない。これは質問の価値ゼロの証明ではない。

この作業で接続できるのは「実回答の意味→比較注記→版付き著者予測の再点検」である。「実回答→数値更新→買い/売り/退出」全体が完成したとはしない。意味・数値の対応が未確認なら進めない理由を、単にfinancial thesis/policyが0という状態報告より具体的にする。

## 読取範囲・固定入力

新GET/DB/Store/コード・共有doc・既存file変更は0。以下の固定研究と現行docの必要部分を再利用した。原PDF全体、実DBの現状態、全市場・全著者を再監査した記録ではない。旧監査G1の後続受入は参照し、旧G2を今回禁止へ変更しない。本メモ以外の新成果物は作っていない。固定後は同名編集しない。

参照略号: [EPS]=2983 eps-applicability-review、[Q]=order-netting-question-preflight、[A]=author-conditions、[D]=ir-policy-adoption、[O]=ir-decision-input-ownership。

| ファイル（repository relative） | SHA-256（全bytes） |
| --- | --- |
| `docs/decision-policy.md` | `4f4b6474033c4f2d979991cd282b1600748c8c53b81488d073deb0c0d4acadca` |
| `docs/ir-question-preparation.md` | `c5e881e0a0874edfc28dcc67d8d48c69600a4916254131477f71b961218d7a7f` |
| `docs/ongoing-work.md` | `1523200c65790b8bd3486f184eb57a9d55194f44c52d3e9aff7e0866a80da9c2` |
| `research/ir-question-policy-audit-2026-10-16/README.md` | `e588f0529d06d3fde77cb32610926c0c553c4f6037fc35bc9806d23f162a854f` |
| `research/ir-question-policy-audit-2026-10-16/parent-acceptance.json` | `ee1612bbf106c75700ff4fb5955ba8ac6f440addc7f71a6c6755f8edc78be513` |
| `research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json` | `ffe7089e380eff8b0133def786725040aa0c52938aabd3a05cba3eefeb50eeb1` |
| `research/ir-case-studies-2026-10-15/2983/eps-applicability-review/review.json` | `1ecf797e2f86ba410cf73eb621fd7f3c14bda2623b5d75d5a57a803e85cc7bd8` |
| `research/ir-case-studies-2026-10-15/2983/eps-applicability-review/README.md` | `6b6beac102091394b99827521b7def3677412437de36590e5539e5f4790c5d5e` |
| `research/ir-case-studies-2026-10-15/2983/order-netting-question-preflight/preflight.json` | `1210130616f09483f9355c43863c7beb49980e4f0ee590db390f8c4d340cb398` |
| `research/ir-case-studies-2026-10-15/2983/author-conditions/case-record.json` | `4f0d47ffcc9350a55e5ad7b878cdff92748b400f3e6dd6aaa98c2d006e6945a4` |
| `research/ir-three-draft-horizon-comparison-2026-10-15/README.md` | `520519092256ec151805e7128281b000f55c1146398d608b37b85b0ab33b7f4f` |
| `research/ir-decision-input-ownership-2026-10-15/README.md` | `ba8b6ba7ca79562f00598014436ceb6a2601839530480462681e75888690c922` |
| `research/ir-policy-adoption-2026-10-15/sources.json` | `4b4f591641916b002ab37cb547bc11b5a0726f5a03647d0230ef4c85c32125f1` |
| `research/ir-policy-adoption-2026-10-15/README.md` | `9320cf6b56952d9a2458a81256e46ddda681a884d32bd6f74763087fe2b92356` |
| `third_party/anthropic/skills/earnings-preview/SKILL.md` | `a30d383a6f1c06b732b4d34e422dd2ff18f6340db67229a3347d057d52697f33` |
| `third_party/anthropic/skills/thesis-tracker/SKILL.md` | `6b4ce2967c5e01c6b42f5c140fa1e94dee2713b5d2de3eb71957ff5a5c11469b` |
