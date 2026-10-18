# 質問へのbaseline参照：独立設計メモ

[設計](../ir-question-baseline-binding-design-2026-10-15/README.md)と既存freeze/plan/verify/send、add_questionの再送処理を読んだ。writer編集中につき最終code reviewは未開始。以下は構成上の故障条件であり、未完成実装のbug認定ではない。実DB・network・コード編集・test実行は0。

1. **歴史参照・送信済み記録・現在情報訂正を分ける（root明確化を反映）。** baselineの実first_saved_at/recorded_atはcreated_at以前を要する。mark_sentは外部で送信済みの事実の記録であり、価格/保有は従来どおり申告sent_at時点を使う。現在の価格期限切れ/held変化だけで当時有効だった歴史sent記録を追加拒否しない。一方、情報訂正holdと未消費新版はtrusted nowでも確認する。baseline current_viewの価格/position表示はadvisoryであり、新しい送信許可gateではない。未解決baselineの昇格禁止は別に維持する。

2. **quote側だけの祖先も含める。** 既存dependency_information_holdsはthesis根拠から始まるため、quoteにだけir_reply親がある場合はそれ単独では訂正を検出できない。選んだbaseline全閉包のcurrent情報hold/未消費分類版を引き続き点検し、immutable baseline.resultを現在可否の代用にしない。

3. **IDだけをcaller入力とする。** serverがnative models.json_text(record) SHA、tableの実first_saved_at、recorded_at、basisを解決する。current_view/envelope又はcompact JSONのhashと混同しない。callerのSHA/日時/public-only/snapshot上書き、未知ID、別会社/版/同版別snapshot/policy/quote/synthetic、後付けIDをrejectし、保存0を確認する。

4. **時計と原典の不足を申告日で埋めない。** baseline.recorded_atが古くても実first_saved_atがcreated_at後なら事前baselineではない。質問時点のsource/thesis/position利用可能性も別に見る。原典欠損/未知をpublic-onlyへ補完せず、今回質問自身への返信がbaseline原典にある参照も拒否する。現在の登録が過去PITを証明したという表示へ広げない。

5. **再送のoptional keyを対称に扱う。** IDなし旧request/旧契約では、比較側だけにresearch_baseline_id=Noneを追加しない。IDありの同要求は元の凍結bindingを返し、別ID/削除/追加による後付けを拒否する。既存質問に後から新baselineを結合しない。callerがserver-generated binding fieldsを追加して凍結照合を迂回できないことも確認する。

6. **未解決baselineを枝計算で昇格しない。** baseline不足があっても参照付きdraftを保存できる範囲は維持できるが、preflightはneeds_reviewである。branch計算だけがdecision_distinguishingになっても、この不足を上書きせずsendを止める。元baseline/result/firstsaveは変更しない。

7. **不要な完全一致を増やさない。** baseline assessmentと質問evidenceは同じthesisの別subsetでよい。同heldの新しい有効な独立position申告も、観測ID/日時/JSON同一性で拒否しない。baselineの回答前thesis_status/actionと、各回答枝の条件付きthesis_status/actionは一致不要である。これらの許可ケースは不正bindingの拒否テストと対にする。

8. **verifyと送信でも凍結参照を再照合する。** record SHA・実firstsave・policy/quote/source bindingの保存根拠を確認し、ID/SHA付替えやbaseline tableの別record参照を通さない。現在のholdは別の診断として付ける。既存の固定policy版・金融条件・reply schema・RecordAvailability entity・新schema追加・新観測作成へ広げる必要はない。

最小実装は、既存baseline recordのserver解決と凍結binding、および既存preflight/sendへ必要なholdを加える薄い接続で足りる。新しい金融計算、枝の再設計、IR効果の因果認定、評価前提や価格の補完、送信処理を追加しない。編集停止の連絡後に、上記の少数故障条件と旧request再送互換をfocusedに点検する。
