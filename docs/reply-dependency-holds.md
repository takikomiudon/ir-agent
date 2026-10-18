# 依存する返信の公開性が保留された場合

新しい返信が公開情報の補足でも、現在の仮説が依存する別の返信に`unclear`または`potential_nonpublic`への訂正があれば、金融入力への適用を保留する。派生資料に複数の原典がある場合も全て遡る。これは[既存の判断方針](decision-policy.md)を処理へ接続するもので、新しい売買規則ではない。

取り込み時から元資料の公開性が未確認の場合も、返信適用の前に止める。IR返信を出典とする資料には`public_clarification`の明示が必要で、分類欠損も保留する。通常の公開開示資料では分類の省略だけで保留しない。いずれも既存評価処理の原典チェックと同じ条件である。

適用結果は`applied:false`、`status:held_for_review`、`decision_status:dependency_information_held_for_review`を返す。当該返信の`information_status`は依存側の分類で上書きしない。`dependency_information_holds`に原因となる別返信のID・訂正版・分類を残す。新しい返信資料や仮説版は追加せず、元の返信、金融入力、過去の判断を保持する。曖昧な分岐は`unresolved`のままで、同じ依存理由も残る。

元資料そのものが原因なら理由は`dependency_source_information_held_for_review`で、`dependency_source_information_holds`に資料ID、snapshotのSHA、元分類、分類の出所を残す。ここに返信訂正版を付けない。両方が原因なら両fieldと理由を保持する。当該新返信の公開性はどちらの場合も別に保持する。

方針契約付き質問の事前確認は`needs_review`となり、`question mark-sent`による新しい送信済み記録も拒否する。これは外部へ送信する機能ではない。契約なしの旧質問についても返信の金融適用は同じ条件で保留するが、全ての旧質問登録・送信記録へ契約を必須化した変更ではない。

新規処理ではDBの書込権取得後の実行時刻で訂正を確認する。申告した質問日・送信日・評価日を過去にして、現在既知の訂正を見落とさない。事前確認には指定時点と現在の確認結果を分けて残す。読み取り専用の`ir-plan FILE`は与えられたsnapshotの条件分析であり、DBの最新訂正を取得する処理ではない。

公開性を再確認した場合は[公開性訂正の操作](workflow.md#返信の公開性を訂正する)で根拠付きの新しい版を追加する。保留された同じ評価要求の再送は、元の保留結果を返す。原文・現在仮説・訂正・価格等を読み直した上で、最新`expected_evaluation_version`と新しい評価日時を指定して`reply evaluate FILE`で明示的に再評価する。仮説版が変わった場合は古い分岐を適用できない。

この再確認による解放は、元資料がpublicで、その後の返信訂正だけが保留原因だった場合の話である。元snapshotが既に不明な資料は、返信訂正をpublicにするだけでは書き換わらず、資料由来の保留が残る。根拠と仮説の依存関係を改めて研究する必要がある。

再確認やguard通過は、回答の意味、会計定義、予測、評価倍率、投資判断の妥当性を認定しない。過去に適用済みの仮説の自動巻戻しも行わない。[再現と修正記録](../research/ir-reply-runtime-gap-review-2026-10-15/README-v2.md)と[全件検証](../research/ir-reply-runtime-gap-review-2026-10-15/parent-full-suite-v2.json)に、この変更の範囲を残した。
