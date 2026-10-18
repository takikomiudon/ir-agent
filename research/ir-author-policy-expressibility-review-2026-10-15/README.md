# 著者方針とdecision v1の表現範囲：保存原典3件の有限点検

**v1の6項目は著者原則そのものではないが、今回の保存根拠から「それらを不要と著者が明示した、即実装できる別の売買ルール」は1件も確証できなかった。** 著者が項目を記していないことと、不要だと指定したことを分ける。現v1の欠損時unresolvedを緩めず、新policy kindは今は追加しない。一方、条件付き評価と研究記録を行える既存経路、v1と異なる相対ratingの表現は区別できる。

記録時刻：2026-10-15T21:14:25.243381+00:00。新しい金融値・確率・費用0・投資閾値の設定、コード変更、計算/テスト実行、実DB操作、ネットワーク取得、外部行為は0。このREADMEだけを作成した。既存原文・調査・manifestを変更していない。

## v1側の確認範囲

[decision.py](../../src/ir_agent/decision.py) の `_PARAMETERS` は minimum_upside_pct / maximum_downside_pct / entry_cost_pct / exit_cost_pct / max_quote_age_seconds / target_scenario の6項目。欠損検査はpolicy_not_configuredを返し、position、仮説状態、原典、価格、反証によるexit判定より前にある。これは現projectの実行契約である。

確率は全ての判断で必須ではない。現在のvaluationは1件以上のscenarioを受け取り、`aggregation: unweighted` なら確率を設定せず個別評価を返せる。v1の保有時exit/holdは、必要な方針・根拠・価格等が揃えばunweightedでも分岐に到達する。**未保有の新規entryだけ**はexpected valueがなければscenario_probabilities_not_configuredとなる。従って「著者は1つの条件付き価値を示すのに、現コードは評価自体にも必ず3ケース確率を求める」というギャップは確認されない。

この確認は同じ金融モデルが妥当だという認定ではない。株価・原典来歴・明示position・公開性・thesis最新版等の既存防御を外す提案もしていない。

## 1. Anthropic：条件付き評価・退出trigger・新情報後のaction記録

保存原典：[thesis-tracker/SKILL.md](../../third_party/anthropic/skills/thesis-tracker/SKILL.md)、固定commit `574ed3624aebd0418c7e96cd101262f30210ab26`。対象は保有・watchlistのthesis管理。原文の該当文は次のとおり。

```text
- **Target price / valuation**: What's it worth if the thesis plays out
- **Stop-loss trigger**: What would make you exit
```

新情報のlogは次の列を持つ。

```text
- **Thesis impact**: Does this strengthen, weaken, or neutralize a specific pillar?
- **Action**: No change / Increase position / Trim / Exit
```

これは著者が明示した**記録・再点検手順**で、条件付き価値と退出理由を残す要求である。原文は「仮説がinvalidatedなら、他の条件にかかわらず即売る」という共通if/then、価格到達時の必須売却、最低上昇余地やmaximum_downsideの数値を示していない。確率を使うな、費用を無視してよい、とも指定していない。pillar例の成長率などを全社共通の閾値へ転用しない。

**判定：記録・条件付きvaluationはそのまま表現可。自動売買候補への昇格には追加assumptionが必要。** 定性case/研究logは支持・反証候補を保存でき、valuationはunweightedの条件付き価値を計算できる。v1は6項目が未設定だとexit分岐にも進めないため、原著の研究手順より狭い。ただし原著がその6項目を「退出には不要」と定義したとまでは言えない。Trimを機械的にexit_reviewへ対応させることや、未知の費用・許容損失を埋めて分岐を通すことはしない。

## 2. Damodaran：DCFの条件付き価値と、推奨前の説明・評価の再点検

保存原典：[ValIntroSpr25の保存text](../ir-policy-adoption-2026-10-15/evidence/e52613a01405bfcd.txt) physical/printed p7、および[eqprojspr25の保存text](../ir-policy-adoption-2026-10-15/evidence/5215df891e0802c0.txt) p8。著者Aswath Damodaran、Spring2025の講義/課題資料であり、現在日本株の推奨や数カ月〜1年の収益実証ではない。

p7は価値計算を次のように定義する（保存改行のまま）。

```text
§ What is it: In discounted cash flow valuation, the value of an asset
  is the present value of the expected cash flows on the asset.
```

課題p8は推奨を出す前の再点検を明示する。

```text
§ Before you make your recommendation, check whether
 anything that has happened during the period of your analysis
 has changed your narrative and your valuation.
```

同頁はDCF・相対・option評価の違いを調整してbuy/sell/holdの最終推奨を作ることを求める。Intro p6の非効率がいつ/どう修正されるかという仮定、p10の長い期間又は触媒という適合条件も、今回の保有期間に自動適合するものではない。

**判定：条件付き価値計算と再評価研究はそのまま表現可。単純なprice<value→buy、又は価格が価値へ達したら必ずsellという実行ルールは、確認した箇所では判定不可。** この原典のexpected cash flowsは期待CFという概念を含み、3scenario確率が印字されないから「不確実性も確率的な前提も不要」とは読まない。1ケースの会社予想を著者の期待CFへ勝手に昇格させない。

v1の新規entryが明示確率期待値を必要とすることは、この原著の評価説明に書かれた普遍要件ではない。しかし原著p7だけを根拠に確率を不要とする新entry ruleを作ることもできない。maximum_downside、費用調整、最低乖離、価格差修正時期や推奨優先順位の欠損を0や独自閾値で埋めない。既存value/研究経路で足りる部分と、実行方針が未確認の部分を分ける。

## 3. 岩井コスモ：半年TOPIX相対のA/B+ rating定義

保存根拠：[sources.json](../published-rating-policies-2026-10-15/sources.json) の `quotes[0]` / `quotes[1]`、原sampleは `retrievals[6]` の `raw_pdf_base64`、source ID `a8c457e4283d4d84-bounded8m`、PDF p3「投資判断の定義について」。2026-04-17付の過去sampleで、原PDF entity SHA `0da22eb3eb8dab2280bb66626d8fbfb50dcb560053055caadcde5f3a87bf6c69`。既存の目視転記を再利用し、今回新たな画像再描画/OCR/独立原PDF読解はしていない。

```text
A：今後半年以内に株価パフォーマンスがTOPIXを15%程度以上上回ると予想
B+：今後半年以内に株価パフォーマンスがTOPIXを5〜15%程度上回ると予想
```

半年、TOPIX、15%、5〜15%、および「程度」は原文からの転記であり、今回設定した投資閾値ではない。これは著者が示す**相対予想ratingの分類定義**で、特定銘柄のEPSや目標価格を単に転記することとは違う。同時に、個人の買い・利確指示、絶対上昇率、費用控除後return、損失制約ではない。

**判定：現v1のbuy/watch等へそのまま変換するには追加assumptionが必要。厳密な自動rating再分類は、必要な著者算式・端点規則が未確認のため判定不可。** v1は絶対価格による費用調整期待上昇余地/下落幅の点検で、TOPIX相対ratingという別の出力体系を持たない。この対象・出力の差は実際にあるが、Aをbuy_review、B+をwatchなどへ対応させる根拠はない。「程度」の厳密端点、配当を含むか、相対return算式、TOPIX予測、rating更新や対象期の運用、取引費用は未確認。原sample取得済みと、これら追加定義の取得/確認済みを混同しない。現在の全社共通rating方針や実行policyとして採用済みともしていない。

## 実装の結論と、必要になる追加根拠

今回の3件では、**既存v1の6条件/確率を著者ルールの代わりに補うべきでないことは確認したが、特定条件を不要と明示した完成済みの別売買規則は確証0件**。原文の沈黙を「不要」と解釈してv1を緩めない。欠損のunresolvedは維持する。今回の探索はここで終了し、新たな原典/サイト探索へ広げない。

新policy kindを直ちに実装する提案はしない。将来、v1と異なる**明示的な著者判断規則**を採用する場合にだけ、旧v1を変更せず別kindを検討する。その前に必要なのは、対象主体と期間、状態/価値からactionへの明示対応、条件付き価値か期待値か、費用を扱う範囲、閾値/比較演算と優先順位、退出条件の原典である。相対ratingならさらにbenchmarkとreturnの定義・「程度」の境界・実行actionとの関係が必要。原典が未指定ならnull/未解決のままにし、比較研究や外部ratingのsource記録で足りる間は新しい実行kindを足さない。

## 点検した保存bytes

次のSHAは今回読んだ保存版を識別するためREADME内へ記しただけで、広い監査やmanifest再作成ではない。

| 保存file | SHA-256 |
|---|---|
| `third_party/anthropic/skills/thesis-tracker/SKILL.md` | `6b4ce2967c5e01c6b42f5c140fa1e94dee2713b5d2de3eb71957ff5a5c11469b` |
| `research/ir-policy-adoption-2026-10-15/evidence/e52613a01405bfcd.txt` | `112d65a5682bd4205f5f82294b001b913fa9ee9295cecae018936f71a59c0864` |
| `research/ir-policy-adoption-2026-10-15/evidence/5215df891e0802c0.txt` | `2fb7cdc6c1b601afa445270e87059859e8d60809a19afb7ec4ad56e4f59f1106` |
| `research/published-rating-policies-2026-10-15/sources.json` | `a47b717e3f73da5f5eff7d7e4c099ca43444c2af2590a6a1cd8bccb193eced73` |
| `research/published-rating-policies-2026-10-15/policy-profiles.json` | `2c8f2e67fce829f8725fbc50e2ae4ecde58571abf148d0954c755f4085ad51d7` |
| `src/ir_agent/decision.py` | `a37bbc586c0aa7c00a924ecc54db7e7132417fa89e350915b9fe2215646b064b` |
| `src/ir_agent/valuation.py` | `fa2df871f55935d7d8fdf130595c8606fbbcba15bc42d8e92e76b2b2d46c92ec` |

負の結論は、Anthropic thesis-tracker本文、上記Damodaranの指定頁、既存rating転記/限定profileの範囲に限る。著者の全著作に別ルールが存在しないという主張ではない。
