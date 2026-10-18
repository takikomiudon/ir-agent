# 質問前baselineの最小接続案（未実装）

**任意のbaseline IDを質問作成時に固定する追加には価値がある。** 比較表を外部で作るだけなら既存の保存研究判断で足りるが、「この質問の前に、このbaselineを選んだ」と機械的に確認するには参照の固定が必要。価格・方針・仮説を新しく設計せず、既存の凍結へ参照を1つ足す。

既存`DecisionLifecycle.freeze/plan`（`src/ir_agent/decision_lifecycle.py:84/119`）は回答枝の事前比較を固定するが、回答前の無変更判断そのもののIDは固定しない。`observations`は状態・信号・期限・結果の設計保存で、価格/保有/研究判断のbaselineを代用しない（`src/ir_agent/observations.py:20/67`、`observation_store.py:126`）。前後評価の別保存という目的は`docs/decision-policy.md:79`にある。今回の案はその接続で、投資方針の追加ではない。

## 最小API

`decision_contract.research_baseline_id`を任意入力にする。callerはIDだけを指定し、サーバが`research_decision_reviews`の不変recordと実`first_saved_at`を解決して、record SHA（`models.json_text`）、初回保存時刻、basis区分を契約へ凍結する。新しい評価・thesis・質問・replyは自動作成しない。baselineの現在表示`current_view`は歴史baselineとして保存しない（`research_decisions.py:224/338`）。

|照合するもの|最小要件|
|---|---|
|主体・仮説|同company、同thesis version、同thesis snapshot SHA。ID/版だけで内容不一致を通さない。|
|方針|同policy ID/version、登録snapshotとSHA。baseline時・質問作成時に利用可能であること。既存policy凍結を再利用。|
|時点|baselineの実`first_saved_at`と`recorded_at`が質問`created_at`以前。source/thesis/positionも当該時点の保存来歴で利用可能。申告日だけの後付けは不可。|
|価格|同じquote snapshot（source、値、通貨、観測/取得時刻、precision、field pathを含む）と根拠source SHA。別価格を「同一価格での回答前後比較」と呼ばない。新価格で比較し直すなら新baselineと新質問を明示する。|
|元資料|baselineと質問のthesis/quoteからたどる原典DAGのID/SHA・公開性・当時のavailabilityを照合。callerがsource集合やpublic-only判定を上書きしない。|
|保有・架空区分|syntheticを一致させ、当時の有効positionの`held`を一致。未知をfalseへ補完しない。synthetic_positionの出所も保持し、実申告と区別する。|
|判定可能性|baselineの不足や`result.status: unresolved`を勝手に完了へ昇格しない。参照付きdraftは保持できても、比較前提が未完了ならpreflightをneeds_reviewとし送信時に既存gateで止める。|

`basis.kind: saved_research`だけでは公開資料のみとは言えない。`basis.public_only: true`かつIR祖先なし・原典/公開性/availability確認済みなら「保存公開資料baseline」。prior IRを含む場合は「既存IRを含む保存研究baseline」とし`reply_bindings`を保持する。祖先未知をpublic-onlyへ補完しない（`research_decisions.py:321/343`）。今回質問自身への返信が原典に含まれる参照は拒否する。いずれも無IRの場合との因果効果を証明しない。

## 一致させなくてよいもの

- baselineの`assessment.evidence_ids`と質問の`evidence_ids`は同じ集合でなくてよい。両方が同じ凍結thesisの根拠subsetであり、全原典の整合が確認できればよい。担当者/rationaleも同文を要求しない。
- positionの観測ID・観測日時・記録JSON全体は同一でなくてよい。後の独立申告でも、質問時点で利用可能な有効`held`が同じなら計算上の保有条件は同じ。ただし両方の出所は残す。
- baselineのthesis_statusは「回答前」の担当者評価、各branchのthesis_statusは「その回答を得た場合」の事前条件であり、一致を要求しない。baseline actionと各branch actionの一致も要求しない。
- 現在時刻のbaseline表示が価格期限切れになったことだけで、過去に固定したbaselineの存在を否定しない。時点比較と現在の利用可否を分ける。

## 凍結・再送・送信時の境界

`freeze`で上の同一性/時点を検証し、`verify_saved_contract`で保存baseline record/SHA・初回保存時刻も再照合する。`validate_send`は既存の現在の価格鮮度・保有・依存情報の訂正・枝比較を引き続き実施し、baselineのhistorical_resultで現在gateを迂回しない。後日訂正や新情報で保留が必要でも旧baseline/契約を書き換えない。新設のbindingは歴史baselineへの参照であり、研究判断・金融入力の採用承認ではない。

`CONTRACT_INPUTS`へ任意keyを足す際は`Harness.add_question`の再送比較にも注意する（`harness.py:394`）。旧契約にないkeyを一律`None`として比較側だけへ足すと、旧質問の同内容再送を壊す。**IDなしの旧質問は従来どおり、IDありは変更不可**を維持し、保存済み質問への後付けはしない。新schemaや観測台帳の拡張は不要。

検証すべき故障は、未知ID・別company/版/SHA/policy/quote/synthetic、質問後に初保存されたbaseline、当時未保存のposition/source、未知祖先をpublic-onlyとするケース、ID/SHAの付替え、旧質問の完全再送失敗、後付け参照、現在holdのbaseline迂回。逆に根拠subset差・同heldの新しい観測ID・回答枝ごとのstatus差は許可する。現在のnewcoreは独立レビュー待ちなので実装やテスト実行はしていない。ネット・実DBアクセス・コード/共有docs編集0。
