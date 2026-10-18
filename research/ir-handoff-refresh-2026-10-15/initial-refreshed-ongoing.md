# 継続作業の状態

利用者の指示により、停止の指示があるまで、目前のタスクからIRに基づく投資判断ロジックを構築する。既存著者の方針を優先し、予測・倍率・確率・売買条件を独自に補わない。実送信・注文・有料契約は指示されていない。

## 現在の状態

2026-10-15 20:08 UTC。実DBは122資料（公開121・市場1）、公開資料あり21社・財務内容あり20社、分類121、完了job54（intake51・定性3）。attempt51/events102/receipt51は分類と定性のleaseであり、全研究工程の処理能力ではない。source来歴はlegacy28/trusted94。1,819社のwatch/held:falseは実保有の確認ではなく、明示保有申告・金融thesis・正式質問・返信・実policy・送信・注文は0。

native監視は13case・17版・68既読資料。[管理日を全件設定](../research/ir-case-studies-2026-10-15/5831/management-review-setup/README.md)し、今回のqueueは新規0。5831は2027-01-16 Tokyo、他12件は2027-01-15 Tokyo。研究管理日を会社決算予定・反証期限・売却期限へ変換しない。全Webの最新開示を点検した結果ではない。外部scheduler・定時Web取得・LLM自動実行は未設置。

コードの受入は[全1,425件・36.665秒成功](../research/ir-qualitative-independent-code-review-2026-10-15/parent-acceptance.json)。独立レビューで、一時保留後に復旧しても定性jobを再起票できないP2を修正。旧job/packet/attemptを保持して現在時点のjobへ連鎖し、保留継続中は起票しない。全件検証中の実DB122資料SHAは不変。コード変更がない限り同じ全件検証を繰り返さない。

公表値の[索引v21](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v21.json)は18社・97fact・24派生entry・21会社/原典組。[5831のNI/EPS2値](../research/ir-case-studies-2026-10-15/5831/issuer-guidance-facts/parent-acceptance.json)を追加し、旧95factを完全保持。派生sourceは実DB・金融入力へ未採用。[10社31taskの進捗v5](../research/ir-issue-owner-backlog-2026-10-15/README-v5.md)は旧task/owner/DAGを固定し、有限完了と新材料待ち・会社定義・著者仕様・金融未採用を区別する。

## 進めている作業

7325アイリックの会社原本で、業種タグと実際の事業構造を区別する。金融4業種56社のモデル点検taskのうち保険代理店/システム事業を確認する例であり、投資順位ではない。母集団は[1,819社のモデル点検](../research/ir-universe-model-routing-intake-2026-10-15/README.md)。金融4業種56社というラベルを自動除外や専用モデルの確定へ使わない。

[保存5JSONの経路棚卸し](../research/ir-case-studies-2026-10-15/7325/saved-issuer-route-inventory/README.md)から、fresh robotsと新規事業HTMLだけを各1GET、両方200完全本文。旧失敗TOPの再試行・redirect・API/JS・会社概要へのfallbackは0。取得は`7325/business-structure-followup/`へ保存。最大3blockの意味確認とsource/case準備を担当agentが実施中で、実DB保存はまだしていない。

会社原文は保険選択支援/直営店・FC運営・システム等を支持する。グループ全体の引受不在、手数料契約、規制資本適用、資金負債の役割や通常モデル適合は未確定。次はrootが原文/引用/SHA/来歴を受け入れ、必要な1sourceの分類と、会社根拠の研究case引継ぎを行う。銀行型の規制資本モデル・買い/売り・IR質問へ自動変換しない。

## 作業を引き継ぐ際の規則

[技能](../.agents/skills/jp-equity-ir/SKILL.md)・[担当依頼](../.agents/skills/jp-equity-ir/references/roles.md)・[定性job契約](qualitative-research-jobs.md)を使う。まずpacket.kind/stageを確認し、intake分類・定性観測・金融researchの結果契約を混ぜない。元条件と直前の観測を区別し、会社の保存担当は一人にする。反証担当は同じ固定入力を読み、原文にない条件を補わない。

金融条件の採用は[判断方針](decision-policy.md)・[モデル点検](model-routing-inputs.md)・[13段階の運用](ir-operation-design.md)に従う。Anthropicの仮説/反証/四半期点検、Damodaranの説明→数値/モデル適合、EVSIの原式は研究手順へ採用済みだが、個社の未来予測・公正倍率・価格/利確条件・返信尤度は別の採用を必要とする。会社予想の転載と著者独自予測を区別する。

公開GET前に[7 exact hostの収集保留](../research/ir-source-access-holds-2026-10-15/README-v3.md)と同経路の後続記録を確認する。同じnegative、動的一覧、robots/TLS失敗を繰り返し試さず、未解決を未試行へ戻さない。会社が公表済みの答えを再質問しない。不明だけをIR優先理由や売買条件にせず、曖昧/無回答から評価額を変更しない。

[3例の既存草案等](../research/ir-issue-owner-backlog-2026-10-15/README-v5.md)は研究成果で、正式登録や送信準備完了ではない。新しい材料がなく期日未到来なら同義のpreviewを追加しない。正常再投資/FCFE等の不足を0や業界値で埋めず、原典に基づく次の有限資料確認を選ぶ。

## 過去の記録

[従来の詳細な継続記録を完全byteで保存](research-history-2026-10-15-through-2005.md)した。旧件数・未確認・テスト数は当時の状態であり、現在の作業指示として再実行しない。個社別の根拠は[事例索引](../research/ir-case-studies-2026-10-15/README.md)、現在の定性進捗は実台帳のqualitative show、旧manifest v19のreportは当該固定file時点を表す。
