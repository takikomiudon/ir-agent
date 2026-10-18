# 数値仮説前の研究点検を接続する

新しいread-only reportを追加し、全1,312テスト・35.209秒で成功した（[tests.log](tests.log)）。Anthropicの新データと仮説の対応・四半期点検を支える。新保存資料、既存未確認、管理日の到来、根拠不足を分け、金融判断やjobを生成しない。[契約](contract.md) / [独立レビュー](independent-code-review.md)。

実DBの135A/1518、計18保存sourceで[実行を確認](actual-run-validation.json)。DBのmain file SHAは前後一致した。既存の数値thesis要件やdailyを変更せず、現在のwatchの研究段階を別枠で点検する。外部schedulerやWeb更新取得を設置したものではない。

| 保存版 | 実ケースの結果 |
|---|---|
| [入力v1](actual-case-requests.json) / [出力v1](actual-report-v1.json) | 管理日の引用に日付がなく、dueはunknown。原記録を残す。 |
| [入力v2](actual-case-requests-v2.json) / [出力v2](actual-report-v2.json) | 日付とtimezoneを含む連続引用へ修正。新保存0、135Aの既存未確認10件を保持、1518は追加triggerなし。 |
| [入力v3](actual-case-requests-v3.json) / [出力v3](actual-report-v3.json) | 135Aの[10本文の関連確認](135A-pending-source-review/review.md)と[親のcheckpoint](135A-combined-review-checkpoint.json)を反映。両社とも新保存0・未確認0・管理日未到来で、追加triggerなし。 |
| [入力v4](actual-case-requests-v4.json) / [出力v4](actual-report-v4.json) | 1721の[著者6論点](../ir-case-studies-2026-10-15/1721/author-conditions/case-record.md)を追加。3社21保存sourceで追加triggerなし、[実行前後のDBは不変](actual-v4-validation.json)。 |
| [入力v5](actual-case-requests-v5.json) / [出力v5](actual-report-v5.json) | 7525・8151の著者論点を追加。5社25保存sourceで追加triggerなし、[実行前後のDBは不変](actual-v5-validation.json)。 |
| [v5＋新会社資料](actual-report-v5-after-issuer-ingest.json) | 7525の会社本文2件を実保存すると、新保存2・論点未確認2でneeds_manual_reviewへ戻る。[分類完了だけで研究済みにしないことを確認](actual-new-source-trigger-validation.json)。 |
| [入力v6](actual-case-requests-v6.json) / [出力v6](actual-report-v6.json) | 7525の[会社一次資料との比較](../ir-case-studies-2026-10-15/7525/issuer-plan-comparison/case-record.md)を反映し、9765の著者論点も追加。6社30保存sourceで追加triggerなし、[DB不変](actual-v6-validation.json)。 |
| [入力v7](actual-case-requests-v7.json) / [出力v7](actual-report-v7.json) | 8151の[著者間比較](../ir-case-studies-2026-10-15/8151/cross-author-comparison/README.md)と7525の空の説明資料索引を反映。6社33保存sourceで追加triggerなし、[DB不変](actual-v7-validation.json)。 |
| [入力v8](actual-case-requests-v8.json) / [出力v8](actual-report-v8.json) | 1518のニュース一覧と7525の公開FAQを既存論点へ対応。6社35保存sourceで追加triggerなし、[DB不変](actual-v8-validation.json)。買収完了・数値仮説・質問送信の判断は追加していない。 |
| [入力v9](actual-case-requests-v9.json) / [出力v9](actual-report-v9.json) | 会社カレンダー・7525政策/ローダー・JPX行別予定を旧論点へ対応。6社44保存sourceで追加triggerなし、[DB不変](actual-v9-validation.json)。 |

135Aの10件は取得経路、索引、アクセス規則、作者方針等だった。既存5件の数値比較・AND条件・未解決定義は維持し、仮説支持や反証成立へ変えない。`reviewed`はその論点との関連を人が確認した記録で、金融入力の正しさやリンク先を全て読んだことを意味しない。

管理日は既存の2027-01-15を維持し、[今回の運用記録](operational-calendar-basis.json)でAsia/Tokyoの暦日と明示した。著者や会社がこの日時を指定したとの主張ではない。現在作成したmanifestの過去存在・前向き検証は認定しない。

今回の正常な無変化時結果から、同じpreviewや仮の予測を作らず、新しい保存資料又は既存管理日の到来を待つ。未解決の事業定義・評価前提は未解決のまま保つ。

1721は[親の原文照合](../ir-case-studies-2026-10-15/1721/author-conditions/root-recheck.json)で18引用と6つの独立した定性論点を確認した。著者の強み・弱みを新しいAND売買条件にはせず、各論点は未解決のまま保持する。既存会社索引、会社計画HTML、外部レポートの3件について関連を確認した範囲であり、正式短信や外部同業比較を取得済みとはしない。[1721の管理日](1721-operational-calendar-basis.json)は四半期点検を研究段階へ適用した2027-01-15・Asia/Tokyoで、会社公表予定や売却期限とは別である。

v5の7525は[製品構成比の注視点](../ir-case-studies-2026-10-15/7525/author-original-product-review/case-record.md)、8151は[納入・需要・費用・FCFの4条件](../ir-case-studies-2026-10-15/8151/author-forecast-conditions/case-record.md)を対象とする。各社の提供者案内/索引と外部本文2sourceだけをこの時点で確認した。[管理日](7525-8151-operational-calendar-basis.json)はプロジェクトの運用上の選択で、著者の達成期限ではない。並行して取得した未登録の会社資料はこのDB snapshotの外で、後の取り込みと比較を別に記録する。8151の古い著者予測を現在の投資予測へ採用していない。

v6の9765は[著者条件](../ir-case-studies-2026-10-15/9765/author-conditions/case-record.md)、[独立点検](../ir-case-studies-2026-10-15/9765/author-conditions/independent-recheck.md)、[会社短信索引の確認](../ir-case-studies-2026-10-15/9765/issuer-financial-followup/root-recheck.json)を[合成checkpoint](9765-combined-review-checkpoint.json)へ結合した。会社正式短信は未取得、会社予想転載と著者の定性上振れ見通し・市場PERを分け、年度ラベル差は未解決。[管理日](9765-operational-calendar-basis.json)は運用上の選択である。7525も会社40/55目標の裏付けを増やしただけで、比率定義や著者の反証幅・評価額は確定していない。

v7は、8151のQUICK会社NI由来EPSをAstris独自予測の改訂へ混ぜず、[旧4条件との関連を確認](../ir-case-studies-2026-10-15/8151/cross-author-comparison/root-monitoring-checkpoint.json)した。会社原典・株式基準・同一案件の対応は未解決。7525の[説明資料索引](../ir-case-studies-2026-10-15/7525/issuer-presentation-followup/README.md)には静的PDFリンクがなく、最新比率を得た記録ではない。[合成checkpoint](7525-combined-review-checkpoint.json)は旧論点とこの限定確認を結ぶ。どちらも、関連を確認したsourceを`reviewed`にしたもので、金融入力の採用や著者見解の成立を意味しない。

v8は1518の[ニュース一覧](../ir-case-studies-2026-10-15/1518/acquisition-completion-followup/README.md)を確認したが、山洋は旧7/22告知へのリンクだけで、完了・連結開始・利益寄与は未確認。7525の[公開FAQ10問](../ir-case-studies-2026-10-15/7525/public-definition-faq-review/README.md)も比率定義への回答を含まず、研究草案v2を維持する。いずれも取得範囲を超えて未完了・非公表とは判断しない。2つの新checkpointが旧研究・独立点検・新sourceを結ぶ。

v9は[JPXの10/8時点一覧](../ir-jpx-earnings-schedule-review-2026-10-15/README.md)から、1721の11/6、7525と8151の11/11、1518の11/13という2026年の予定を接続した。8151は2026年9月期本決算、他3社は2027年3月期第2四半期。原xlsx1件を4行へ分けた表現で、4つの独立した確認ではない。既存caseの4つの新checkpointが次の公開確認と未解決を記録する。

[予定入力](jpx-event-requests-v1.json)を既存CLIへ渡した[予定レポート](jpx-event-report-v1.json)は4件ともsource-bound candidate。[出力点検](jpx-event-output-recheck.json)でも時刻・timezone・絶対時点はnull、実施はnot_establishedを維持した。1年の表示範囲は売却期限ではない。135A/9765は選択した一覧で未発見であり、予定なしとはしない。研究管理日1/15も変更していない。

7525の[沈黙方針](../ir-case-studies-2026-10-15/7525/issuer-ir-policy-review/README.md)は決算・業績見通しコメントの制限であり全窓口閉鎖とはしない。[ローダー](../ir-case-studies-2026-10-15/7525/issuer-loader-followup/README.md)は配信先robotsの全path禁止でdata0/PDF0停止。1721の一般沈黙方針、1518の年次画像も具体的な発表時刻や現在の送信可否を与えない。金融仮説・評価・草案readyを進めた記録ではない。
